# Generated by Django 5.2.1 on 2025-05-20 12:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="studenttest",
            name="is_completed",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="studenttest",
            name="completed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
