from django.db import models
from django.contrib.auth.models import User
from documents.utils import extract_docx_text
import re


class Document(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    is_private = models.BooleanField(
        default=True,
        help_text="Private = only owner can use it. Public = everyone can use it."
    )

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="documents/")
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.file and not self.content:
            self.content = extract_docx_text(self.file.path)
            super().save(update_fields=["content"])

    def __str__(self):
        return self.title


class ChatSession(models.Model):
    title = models.CharField(
        max_length=255,
        blank=True
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Chat"
        verbose_name_plural = "Chats"

    def __str__(self):
        return self.title or f"Chat {self.id}"


class QuestionHistory(models.Model):
    chat = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
        null=True,
        blank=True
    )

    question = models.TextField()
    answer = models.TextField(blank=True)

    sources = models.JSONField(
        default=list,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Question History"
        ordering = ["-created_at"]

    def question_direction(self):
        if re.search(r"[\u0600-\u06FF]", self.question or ""):
            return "rtl"
        return "ltr"

    def answer_direction(self):
        if re.search(r"[\u0600-\u06FF]", self.answer or ""):
            return "rtl"
        return "ltr"

    def __str__(self):
        return self.question[:50]