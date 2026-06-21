from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = "Create default user groups and permissions"

    def handle(self, *args, **kwargs):
        document_group, _ = Group.objects.get_or_create(
            name="Document Users"
        )

        chat_group, _ = Group.objects.get_or_create(
            name="Chat Users"
        )

        document_permissions = Permission.objects.filter(
            content_type__app_label="chat",
            content_type__model="document",
            codename__in=[
                "view_document",
                "add_document",
                "change_document",
                "delete_document",
            ]
        )

        chat_permissions = Permission.objects.filter(
            content_type__app_label="chat",
            content_type__model__in=[
                "chatsession",
                "questionhistory",
            ],
            codename__in=[
                "view_chatsession",
                "add_chatsession",
                "change_chatsession",
                "delete_chatsession",
                "view_questionhistory",
                "add_questionhistory",
                "change_questionhistory",
                "delete_questionhistory",
            ]
        )

        document_group.permissions.set(document_permissions)
        chat_group.permissions.set(chat_permissions)

        self.stdout.write(
            self.style.SUCCESS("Default groups created successfully.")
        )