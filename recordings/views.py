import csv
import json
from io import StringIO

from django.http import HttpResponse
from django.shortcuts import render
from django.db import IntegrityError
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .dataset_export import build_training_dataset_zip
from .models import Recording, SpeakerIdCounter
from .sentences_data import LANGUAGE_LABELS, SENTENCES
from .serializers import RecordingUploadSerializer


def index(request):
    """Page principale : collecte vocale."""
    return render(
        request,
        "recordings/index.html",
        {
            "languages": list(LANGUAGE_LABELS.items()),
            "sentences_json": json.dumps(SENTENCES, ensure_ascii=False),
        },
    )


class UploadView(APIView):
    """POST /upload/ — enregistrement audio + métadonnées."""

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        serializer = RecordingUploadSerializer(data=request.data)
        if not serializer.is_valid():
            # DRF peut déjà valider les contraintes d'unicité via UniqueConstraint
            # et remonter une erreur sous `non_field_errors`.
            non_field = serializer.errors.get("non_field_errors")
            if isinstance(non_field, list) and non_field:
                msg_any = " ".join([str(x) for x in non_field])
                if "ensemble unique" in msg_any or "unique" in msg_any:
                    return Response(
                        {
                            "message": "Cette phrase a déjà été enregistrée pour ce locuteur.",
                        },
                        status=status.HTTP_409_CONFLICT,
                    )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            recording = serializer.save()
        except IntegrityError:
            return Response(
                {
                    "message": "Cette phrase a déjà été enregistrée pour ce locuteur.",
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(
            {
                "id": recording.id,
                "file_path": recording.relative_file_path,
                "message": "Enregistrement sauvegardé.",
            },
            status=status.HTTP_201_CREATED,
        )


class ExportView(APIView):
    """GET /export/ — CSV pour entraînement."""

    def get(self, request, *args, **kwargs):
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            ["file_path", "text_local", "translation", "language", "speaker_id"]
        )
        for rec in Recording.objects.all().iterator():
            writer.writerow(
                [
                    rec.relative_file_path,
                    rec.text_local,
                    rec.translation,
                    rec.language,
                    rec.speaker_id,
                ]
            )
        response = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="dataset_export.csv"'
        return response


class TrainingExportView(APIView):
    """GET /export/training/ — dataset WAV + manifests CSV (zip)."""

    @staticmethod
    def _parse_split_params(request):
        defaults = {"train": 0.8, "valid": 0.1, "test": 0.1}
        values = {}
        for key, default in defaults.items():
            raw = request.query_params.get(key)
            if raw is None or raw == "":
                values[key] = default
                continue
            try:
                values[key] = float(raw)
            except ValueError as exc:
                raise ValueError(f"Paramètre '{key}' invalide: {raw}") from exc
            if values[key] <= 0 or values[key] >= 1:
                raise ValueError(
                    f"Paramètre '{key}' doit être > 0 et < 1."
                )

        total = values["train"] + values["valid"] + values["test"]
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"La somme train+valid+test doit être 1.0 (actuel={total:.6f})."
            )

        seed_raw = request.query_params.get("seed")
        seed = None
        if seed_raw not in (None, ""):
            try:
                seed = int(seed_raw)
            except ValueError as exc:
                raise ValueError(f"Paramètre 'seed' invalide: {seed_raw}") from exc

        return values["train"], values["valid"], values["test"], seed

    def get(self, request, *args, **kwargs):
        try:
            train_ratio, valid_ratio, test_ratio, seed = self._parse_split_params(
                request
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            zip_bytes, info = build_training_dataset_zip(
                train_ratio=train_ratio,
                valid_ratio=valid_ratio,
                test_ratio=test_ratio,
                seed=seed,
            )
        except RuntimeError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response = HttpResponse(zip_bytes, content_type="application/zip")
        response["Content-Disposition"] = (
            'attachment; filename="dataset_training_export.zip"'
        )
        response["X-Export-Recordings"] = str(info.get("num_recordings_exported", 0))
        return response


class NextSpeakerIdView(APIView):
    """GET /next-speaker-id/ — attribue spk_001, spk_002, … (nouveau locuteur)."""

    def get(self, request, *args, **kwargs):
        speaker_id = SpeakerIdCounter.allocate_next()
        return Response({"speaker_id": speaker_id})


class StatsView(APIView):
    """GET /stats/?language=yemba — progression pour une langue."""

    def get(self, request, *args, **kwargs):
        lang = request.query_params.get("language", "")
        if lang not in SENTENCES:
            return Response(
                {"error": "Langue invalide."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        total_sentences = len(SENTENCES[lang])
        recorded = Recording.objects.filter(language=lang).count()
        return Response(
            {
                "language": lang,
                "recorded_count": recorded,
                "total_sentences": total_sentences,
            }
        )
