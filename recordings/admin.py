from django.contrib import admin

from .models import AudioFileCounter, Recording, SpeakerIdCounter


@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "language",
        "text_local",
        "speaker_id",
        "age",
        "gender",
        "created_at",
    )
    list_filter = ("language", "gender", "created_at")
    search_fields = ("text_local", "translation", "speaker_id")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


@admin.register(SpeakerIdCounter)
class SpeakerIdCounterAdmin(admin.ModelAdmin):
    list_display = ("id", "next_index")
    readonly_fields = ("id", "next_index")


@admin.register(AudioFileCounter)
class AudioFileCounterAdmin(admin.ModelAdmin):
    list_display = ("speaker_id", "language", "next_index")
    list_filter = ("language",)
    search_fields = ("speaker_id",)
    readonly_fields = ("speaker_id", "language")
