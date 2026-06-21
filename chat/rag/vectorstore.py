from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document as LCDocument
from .embeddings import get_embeddings
from django.conf import settings
from pathlib import Path

INDEX_PATH = Path(settings.BASE_DIR) / "faiss_index"

def create_vectorstore(chunks):
    embeddings = get_embeddings()

    docs = [
        LCDocument(
            page_content=c["text"],
            metadata=c["metadata"]
        )
        for c in chunks
    ]

    db = FAISS.from_documents(docs, embeddings)

    db.save_local(INDEX_PATH)
    return db


def load_vectorstore():
    embeddings = get_embeddings()

    return FAISS.load_local(
        INDEX_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )