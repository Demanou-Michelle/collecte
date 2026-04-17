"""
Remet à zéro les données de collecte : enregistrements, fichiers audio, compteurs.

Usage:
  python manage.py reset_collecte_data
  python manage.py reset_collecte_data --no-input
"""

import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from recordings.models import AudioFileCounter, Recording, SpeakerIdCounter


class Command(BaseCommand):
    help = (
        "Supprime tous les enregistrements vocaux, les fichiers sous media/audio/, "
        "et remet les compteurs spk_ / audio_ à zéro."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Ne pas demander de confirmation.",
        )

    def handle(self, *args, **options):
        if not options["no_input"]:
            confirm = input(
                "Tout effacer (base + fichiers audio + compteurs) ? [oui/NON] : "
            )
            if confirm.strip().lower() not in ("oui", "o", "yes", "y"):
                self.stdout.write(self.style.WARNING("Annulé."))
                return

        n = 0
        for rec in Recording.objects.all():
            if rec.file:
                rec.file.delete(save=False)
            rec.delete()
            n += 1

        AudioFileCounter.objects.all().delete()

        SpeakerIdCounter.objects.update_or_create(
            pk=1,
            defaults={"next_index": 1},
        )

        audio_root = Path(settings.MEDIA_ROOT) / "audio"
        if audio_root.is_dir():
            shutil.rmtree(audio_root)
            audio_root.mkdir(parents=True, exist_ok=True)

        self.stdout.write(
            self.style.SUCCESS(
                f"OK — {n} enregistrement(s) supprimé(s), compteurs réinitialisés, "
                f"dossier media/audio/ vidé."
            )
        )
        self.stdout.write(
            "Les navigateurs gardent encore l’ancien spk_xxx en local : "
            "pour un nouveau locuteur, videz le stockage du site ou utilisez "
            "« Nouvelle session » sur l’app."
        )
