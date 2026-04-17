from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("next-speaker-id/", views.NextSpeakerIdView.as_view(), name="next_speaker_id"),
    path("upload/", views.UploadView.as_view(), name="upload"),
    path("export/", views.ExportView.as_view(), name="export"),
    path("export/training/", views.TrainingExportView.as_view(), name="export_training"),
    path("stats/", views.StatsView.as_view(), name="stats"),
]
