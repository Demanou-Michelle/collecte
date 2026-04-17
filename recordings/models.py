import re
from pathlib import Path

from django.db import models, transaction


def sanitize_speaker_folder(speaker_id: str) -> str:
    """Nom de dossier sûr pour le stockage des fichiers."""
    s = (speaker_id or "").strip() or "unknown"
    s = re.sub(r"[^\w\-]", "_", s)
    return s[:120] if s else "unknown"


def format_audio_filename(n: int) -> str:
    """audio_001, audio_002, … puis audio_1000 si besoin."""
    if n < 1000:
        return f"audio_{n:03d}"
    return f"audio_{n}"


def audio_upload_path(instance, filename):
    ext = Path(filename).suffix.lower()
    if ext not in (".wav", ".webm", ".ogg", ".mp4", ".m4a"):
        ext = ".webm"
    sid = getattr(instance, "speaker_id", None) or "unknown"
    base = AudioFileCounter.allocate_next(sid, instance.language)
    folder = sanitize_speaker_folder(sid)
    # Par langue, puis par locuteur : media/audio/yemba/spk_001/audio_001.webm
    return f"audio/{instance.language}/{folder}/{base}{ext}"


def format_speaker_id(n: int) -> str:
    """spk_001, spk_002, … puis spk_1000 si besoin."""
    if n < 1000:
        return f"spk_{n:03d}"
    return f"spk_{n}"


class SpeakerIdCounter(models.Model):
    """Une ligne (pk=1) : prochain numéro de locuteur à attribuer."""

    id = models.PositiveSmallIntegerField(primary_key=True, default=1)
    next_index = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Compteur identifiants locuteurs"

    def __str__(self):
        return f"prochain → {format_speaker_id(self.next_index)}"

    @classmethod
    def allocate_next(cls) -> str:
        with transaction.atomic():
            cls.objects.get_or_create(pk=1, defaults={"next_index": 1})
            row = cls.objects.select_for_update().get(pk=1)
            n = row.next_index
            row.next_index = n + 1
            row.save(update_fields=["next_index"])
        return format_speaker_id(n)


class AudioFileCounter(models.Model):
    """Compteur par couple (locuteur, langue) : audio_001 repart pour chaque dossier locuteur."""

    speaker_id = models.CharField(max_length=100)
    language = models.CharField(max_length=20)
    next_index = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Compteur fichiers audio (locuteur × langue)"
        verbose_name_plural = "Compteurs fichiers audio"
        constraints = [
            models.UniqueConstraint(
                fields=["speaker_id", "language"],
                name="uniq_audio_counter_speaker_lang",
            ),
        ]

    def __str__(self):
        return f"{self.speaker_id} / {self.language} → {format_audio_filename(self.next_index)}"

    @classmethod
    def allocate_next(cls, speaker_id: str, language: str) -> str:
        sid = (speaker_id or "").strip() or "unknown"
        with transaction.atomic():
            cls.objects.get_or_create(
                speaker_id=sid,
                language=language,
                defaults={"next_index": 1},
            )
            row = cls.objects.select_for_update().get(
                speaker_id=sid,
                language=language,
            )
            n = row.next_index
            row.next_index = n + 1
            row.save(update_fields=["next_index"])
        return format_audio_filename(n)


class Recording(models.Model):
    LANGUAGE_YEMBA = "yemba"
    LANGUAGE_DOUALA = "douala"
    LANGUAGE_EWONDO = "ewondo"
    LANGUAGE_CHOICES = [
        (LANGUAGE_YEMBA, "Yemba"),
        (LANGUAGE_DOUALA, "Douala"),
        (LANGUAGE_EWONDO, "Ewondo"),
    ]

    GENDER_M = "M"
    GENDER_F = "F"
    GENDER_O = "O"
    GENDER_CHOICES = [
        (GENDER_M, "Masculin"),
        (GENDER_F, "Féminin"),
        (GENDER_O, "Autre"),
    ]

    file = models.FileField(upload_to=audio_upload_path)
    text_local = models.CharField(max_length=500)
    translation = models.CharField(max_length=500)
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    speaker_id = models.CharField(max_length=100)
    age = models.PositiveSmallIntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["speaker_id", "language", "text_local"],
                name="uniq_recording_speaker_language_text_local",
            ),
        ]

    def __str__(self):
        return f"{self.language} — {self.text_local[:40]}"

    @property
    def relative_file_path(self):
        """Path relative to MEDIA_ROOT for exports."""
        return self.file.name
