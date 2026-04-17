import csv
import json
import random
import shutil
import subprocess
import wave
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from django.conf import settings

from .models import Recording, sanitize_speaker_folder


def _compute_split_map(speaker_ids, train_ratio=0.8, valid_ratio=0.1, test_ratio=0.1, seed=None):
    """
    Split par speaker (pas de fuite train/test).
    Répartition visée: 80/10/10 avec minimum 1 speaker en valid/test
    quand possible.
    """
    speakers = sorted(set(speaker_ids))
    if seed is not None:
        rng = random.Random(seed)
        rng.shuffle(speakers)
    n = len(speakers)
    if n == 0:
        return {}
    if n == 1:
        return {speakers[0]: "train"}

    # Répartition configurable
    n_train = round(n * train_ratio)
    n_valid = round(n * valid_ratio)
    n_test = n - n_train - n_valid

    # Ajustements pour garder un split utile quand possible.
    if n >= 3:
        if n_valid == 0:
            n_valid = 1
            n_train = max(1, n_train - 1)
        if n_test == 0:
            n_test = 1
            n_train = max(1, n_train - 1)

    # Ajuste la somme exactement à n.
    while n_train + n_valid + n_test < n:
        n_train += 1
    while n_train + n_valid + n_test > n and n_train > 1:
        n_train -= 1
    while n_train + n_valid + n_test > n and n_valid > 0:
        n_valid -= 1
    while n_train + n_valid + n_test > n and n_test > 0:
        n_test -= 1

    train_end = n_train
    valid_end = n_train + n_valid
    train_speakers = set(speakers[:train_end])
    valid_speakers = set(speakers[train_end:valid_end])
    test_speakers = set(speakers[valid_end:])
    split_map = {}
    for sid in speakers:
        if sid in test_speakers:
            split_map[sid] = "test"
        elif sid in valid_speakers:
            split_map[sid] = "valid"
        elif sid in train_speakers:
            split_map[sid] = "train"
        else:
            split_map[sid] = "train"
    return split_map


def _duration_seconds(wav_path: Path):
    with wave.open(str(wav_path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate() or 16000
        return round(frames / float(rate), 3), rate


def _convert_to_wav_16k_mono(src_path: Path, dst_path: Path):
    """
    Conversion via ffmpeg vers WAV PCM 16-bit, mono, 16kHz.
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        "-sample_fmt",
        "s16",
        str(dst_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"Conversion ffmpeg échouée pour {src_path.name}: {proc.stderr[-300:]}"
        )


def build_training_dataset_zip(train_ratio=0.8, valid_ratio=0.1, test_ratio=0.1, seed=None):
    """
    Construit un dataset entraînement et retourne (zip_bytes, dataset_info_dict).

    Structure dans le ZIP:
      dataset/
        audio/<lang>/<speaker>/audio_XXX.wav
        manifests/train.csv
        manifests/valid.csv
        manifests/test.csv
        metadata/speakers.csv
        metadata/dataset_info.json
    """
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg introuvable. Installez ffmpeg pour convertir les enregistrements en WAV."
        )

    recordings = list(
        Recording.objects.all().order_by("language", "speaker_id", "created_at", "id")
    )
    split_map = _compute_split_map(
        [r.speaker_id for r in recordings],
        train_ratio=train_ratio,
        valid_ratio=valid_ratio,
        test_ratio=test_ratio,
        seed=seed,
    )

    with TemporaryDirectory() as tmp:
        root = Path(tmp) / "dataset"
        audio_root = root / "audio"
        manifests_root = root / "manifests"
        metadata_root = root / "metadata"
        audio_root.mkdir(parents=True, exist_ok=True)
        manifests_root.mkdir(parents=True, exist_ok=True)
        metadata_root.mkdir(parents=True, exist_ok=True)

        rows_by_split = {"train": [], "valid": [], "test": []}
        speakers_meta = {}
        per_bucket_counter = {}

        for rec in recordings:
            src = Path(settings.MEDIA_ROOT) / rec.file.name
            if not src.exists():
                continue

            speaker_folder = sanitize_speaker_folder(rec.speaker_id)
            bucket = (rec.language, speaker_folder)
            per_bucket_counter[bucket] = per_bucket_counter.get(bucket, 0) + 1
            index = per_bucket_counter[bucket]
            wav_name = f"audio_{index:03d}.wav" if index < 1000 else f"audio_{index}.wav"

            dst_rel = Path("audio") / rec.language / speaker_folder / wav_name
            dst_abs = root / dst_rel
            dst_abs.parent.mkdir(parents=True, exist_ok=True)

            _convert_to_wav_16k_mono(src, dst_abs)
            duration_sec, sample_rate = _duration_seconds(dst_abs)

            split = split_map.get(rec.speaker_id, "train")
            row_id = f"{rec.language}_{speaker_folder}_{index:04d}"
            row = {
                "id": row_id,
                "audio_path": str(dst_rel).replace("\\", "/"),
                "text": rec.text_local,
                "translation_fr": rec.translation,
                "language": rec.language,
                "speaker_id": rec.speaker_id,
                "duration_sec": f"{duration_sec:.3f}",
                "sample_rate": str(sample_rate),
                "age": str(rec.age),
                "gender": rec.gender,
            }
            rows_by_split[split].append(row)

            if rec.speaker_id not in speakers_meta:
                speakers_meta[rec.speaker_id] = {
                    "speaker_id": rec.speaker_id,
                    "age": str(rec.age),
                    "gender": rec.gender,
                }

        fieldnames = [
            "id",
            "audio_path",
            "text",
            "translation_fr",
            "language",
            "speaker_id",
            "duration_sec",
            "sample_rate",
            "age",
            "gender",
        ]
        for split, rows in rows_by_split.items():
            csv_path = manifests_root / f"{split}.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

        speakers_csv = metadata_root / "speakers.csv"
        with speakers_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["speaker_id", "age", "gender"])
            writer.writeheader()
            writer.writerows(sorted(speakers_meta.values(), key=lambda x: x["speaker_id"]))

        info = {
            "audio_format": "wav",
            "encoding": "pcm_s16le",
            "sample_rate_hz": 16000,
            "channels": 1,
            "split_ratio": {
                "train": train_ratio,
                "valid": valid_ratio,
                "test": test_ratio,
            },
            "split_seed": seed,
            "splits": {k: len(v) for k, v in rows_by_split.items()},
            "num_recordings_exported": sum(len(v) for v in rows_by_split.values()),
            "num_speakers": len(speakers_meta),
            "languages": sorted({r.language for r in recordings}),
        }
        with (metadata_root / "dataset_info.json").open("w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

        zip_path = Path(tmp) / "dataset_training_export.zip"
        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zf:
            for p in root.rglob("*"):
                if p.is_file():
                    zf.write(p, p.relative_to(Path(tmp)))

        return zip_path.read_bytes(), info
