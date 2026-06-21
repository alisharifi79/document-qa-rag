from django.core.management.base import BaseCommand
from chat.rag.pipeline import build_index


class Command(BaseCommand):
    help = "Build FAISS index from uploaded documents"

    def handle(self, *args, **kwargs):
        build_index()
        self.stdout.write(
            self.style.SUCCESS("FAISS index created successfully")
        )