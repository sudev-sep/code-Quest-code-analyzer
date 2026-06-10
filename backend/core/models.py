from django.db import models
from django.contrib.auth.models import User


class Repository(models.Model):
    STATUS_CHOICES = [
        ('ready', 'Ready'),
        ('indexing', 'Indexing'),
        ('cloning', 'Cloning'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    github_url = models.URLField()
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    local_path = models.CharField(max_length=255, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True),
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class FileChunk(models.Model):
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='chunks')
    file_path = models.CharField(max_length=255)
    chunk_index = models.IntegerField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_path} - chunk {self.chunk_index}"