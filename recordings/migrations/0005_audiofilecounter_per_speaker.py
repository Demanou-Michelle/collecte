# Compteur audio par (speaker_id, langue) + chemins par dossier locuteur

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recordings", "0004_audio_counter_per_language"),
    ]

    operations = [
        migrations.DeleteModel(
            name="AudioFileCounter",
        ),
        migrations.CreateModel(
            name="AudioFileCounter",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("speaker_id", models.CharField(max_length=100)),
                ("language", models.CharField(max_length=20)),
                ("next_index", models.PositiveIntegerField(default=1)),
            ],
            options={
                "verbose_name": "Compteur fichiers audio (locuteur × langue)",
                "verbose_name_plural": "Compteurs fichiers audio",
            },
        ),
        migrations.AddConstraint(
            model_name="audiofilecounter",
            constraint=models.UniqueConstraint(
                fields=("speaker_id", "language"),
                name="uniq_audio_counter_speaker_lang",
            ),
        ),
    ]
