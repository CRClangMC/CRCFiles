from django.db import models

class FileRecord(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255)

    def __str__(self):
        return self.file_name
