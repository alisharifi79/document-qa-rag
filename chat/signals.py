from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User, Group

from .models import Document
from .rag.pipeline import build_index


@receiver(post_save, sender=Document)
def rebuild_index_after_document_save(sender, instance, created, **kwargs):
    build_index()


@receiver(post_delete, sender=Document)
def rebuild_index_after_document_delete(sender, instance, **kwargs):
    build_index()


@receiver(post_save, sender=User)
def assign_default_groups_to_staff_user(sender, instance, created, **kwargs):
    if instance.is_staff and not instance.is_superuser:
        document_group, _ = Group.objects.get_or_create(
            name="Document Users"
        )

        chat_group, _ = Group.objects.get_or_create(
            name="Chat Users"
        )

        instance.groups.add(document_group, chat_group)