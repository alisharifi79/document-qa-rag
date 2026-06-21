import re
import shutil
from pathlib import Path

from django.conf import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rapidfuzz import process, fuzz

from chat.models import Document
from .vectorstore import load_vectorstore, create_vectorstore
from .llm import ask_llm
from django.db.models import Q


def split_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    return splitter.split_text(text)


def build_index():
    index_path = Path(settings.BASE_DIR) / "faiss_index"

    if index_path.exists():
        for item in index_path.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
    else:
        index_path.mkdir(parents=True, exist_ok=True)

    documents = Document.objects.all()

    print("Documents found:", documents.count())

    chunks = []

    for document in documents:
        print("Document:", document.title)

        if not document.content:
            continue

        split_chunks = split_text(document.content)

        for i, chunk in enumerate(split_chunks):
            chunks.append({
                "text": chunk,
                "metadata": {
                    "doc_id": document.id,
                    "title": document.title,
                    "chunk_id": i
                }
            })

    print("Total chunks:", len(chunks))

    if chunks:
        create_vectorstore(chunks)
        print("FAISS saved successfully")
    else:
        print("No chunks found")

def get_accessible_documents(user=None):
    if user and user.is_authenticated:
        if user.is_superuser:
            return Document.objects.all()

        return Document.objects.filter(
            Q(is_private=False) | Q(user=user)
        )

    return Document.objects.filter(is_private=False)

def get_document_terms(user=None):
    terms = set()

    documents = get_accessible_documents(user)

    for document in documents:
        text = f"{document.title} {document.content or ''}"
        words = re.findall(r"[A-Za-zآ-ی]+", text)

        for word in words:
            word = word.lower().strip()
            if len(word) >= 4:
                terms.add(word)

    return list(terms)


def correct_question_terms(question, user=None):
    document_terms = get_document_terms(user)

    if not document_terms:
        return question

    corrected_question = question

    for word in question.split():
        clean_word = word.strip("?!.,،؟").lower()

        if len(clean_word) < 4:
            continue

        match = process.extractOne(
            clean_word,
            document_terms,
            scorer=fuzz.partial_ratio
        )

        if match and match[1] >= 65:
            corrected_question = corrected_question.replace(
                word,
                match[0]
            )

    return corrected_question


def keyword_fuzzy_search(question, user=None, limit=3):
    results = []

    documents = get_accessible_documents(user)

    question_lower = question.lower()

    for document in documents:
        if not document.content:
            continue

        content_lower = document.content.lower()
        title_lower = document.title.lower()

        title_score = fuzz.partial_ratio(
            question_lower,
            title_lower
        )

        content_score = fuzz.partial_ratio(
            question_lower,
            content_lower
        )

        score = max(title_score, content_score)

        if score >= 40:
            results.append({
                "text": document.content[:1200],
                "metadata": {
                    "doc_id": document.id,
                    "title": document.title,
                    "chunk_id": "keyword"
                },
                "score": score
            })

    results = sorted(
        results,
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:limit]


def answer_question(question, user=None, debug=False):
    corrected_question = correct_question_terms(question, user)

    db = load_vectorstore()

    faiss_docs = db.similarity_search(
        corrected_question,
        k=5
    )

    keyword_results = keyword_fuzzy_search(
        corrected_question,
        user=user,
        limit=3
    )

    allowed_docs = get_accessible_documents(user)
    allowed_doc_ids = set(
        allowed_docs.values_list("id", flat=True)
    )

    combined_docs = []
    seen = set()

    for doc in faiss_docs:
        doc_id = doc.metadata.get("doc_id")

        if doc_id not in allowed_doc_ids:
            continue

        key = (
            doc.metadata.get("doc_id"),
            doc.metadata.get("chunk_id")
        )

        if key not in seen:
            combined_docs.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "source_type": "vector"
            })

            seen.add(key)

    for item in keyword_results:
        key = (
            item["metadata"].get("doc_id"),
            item["metadata"].get("chunk_id")
        )

        if key not in seen:
            combined_docs.append({
                "content": item["text"],
                "metadata": item["metadata"],
                "source_type": "keyword"
            })

            seen.add(key)

    combined_docs = combined_docs[:5]

    context = "\n\n".join(
        item["content"]
        for item in combined_docs
    )
    print("QUESTION:", question)
    print("CORRECTED:", corrected_question)
    print("SOURCES:", [
        item["metadata"].get("title")
        for item in combined_docs
    ])
    print("CONTEXT:", context[:1000])
    answer = ask_llm(
        corrected_question,
        context
    )

    if debug:
        return {
            "original_question": question,
            "corrected_question": corrected_question,
            "answer": answer,
            "retrieved_chunks": [
                {
                    "content": item["content"],
                    "metadata": item["metadata"],
                    "source_type": item["source_type"]
                }
                for item in combined_docs
            ],
            "sources": [
                {
                    "title": item["metadata"].get("title"),
                    "chunk_id": item["metadata"].get("chunk_id"),
                    "source_type": item["source_type"]
                }
                for item in combined_docs
            ]
        }

    return answer