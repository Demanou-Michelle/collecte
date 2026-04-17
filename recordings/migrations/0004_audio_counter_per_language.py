# Generated manually: compteur audio par langue (audio_001 par langue)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recordings", "0003_audiofilecounter"),
    ]

    operations = [
        migrations.DeleteModel(
            name="AudioFileCounter",
        ),
        migrations.CreateModel(
            name="AudioFileCounter",
            fields=[
                (
                    "language",
                    models.CharField(max_length=20, primary_key=True, serialize=False),
                ),
                ("next_index", models.PositiveIntegerField(default=1)),
            ],
            options={
                "verbose_name": "Compteur fichiers audio (par langue)",
                "verbose_name_plural": "Compteurs fichiers audio",
            },
        ),
    ]
