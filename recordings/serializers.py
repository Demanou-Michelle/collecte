import re

from rest_framework import serializers

from .models import Recording


class RecordingUploadSerializer(serializers.ModelSerializer):
    audio = serializers.FileField(write_only=True, source="file")

    class Meta:
        model = Recording
        fields = (
            "audio",
            "text_local",
            "translation",
            "language",
            "speaker_id",
            "age",
            "gender",
        )

    def validate_age(self, value):
        if value < 1 or value > 120:
            raise serializers.ValidationError("L'âge doit être entre 1 et 120.")
        return value

    def validate_text_local(self, value):
        # Normalisation simple pour éviter les doublons liés aux espaces.
        normalized = re.sub(r"\s+", " ", (value or "").strip())
        if not normalized:
            raise serializers.ValidationError("Le texte local est obligatoire.")
        return normalized
