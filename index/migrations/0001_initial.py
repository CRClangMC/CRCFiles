# Generated by Django 5.0.4 on 2025-05-01 08:04

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FileRecord',
            fields=[
                ('id', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('file_name', models.CharField(max_length=255)),
                ('file_path', models.CharField(max_length=255)),
            ],
        ),
    ]
