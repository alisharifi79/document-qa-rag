# AI Internship - Document Question Answering System

## Project Overview

This project is a Retrieval-Augmented Generation (RAG) document question-answering system built with Django.

Users can upload documents, ask questions about them, manage chat sessions, and view the source documents used to generate answers.

The system supports both English and Persian/Farsi.

---

## Main Features

* Document Upload
* Automatic DOCX Text Extraction
* Private/Public Documents
* User-Based Access Control
* Chat Sessions
* Question History
* Source Attribution
* Persian & English Support
* RTL/LTR Text Handling
* Semantic Search (FAISS)
* Fuzzy Keyword Search (RapidFuzz)
* Typo-Tolerant Retrieval
* OpenRouter Integration
* Docker Support

---

## Technologies Used

* Python
* Django
* Django REST Framework
* FAISS
* LangChain
* Sentence Transformers
* RapidFuzz
* OpenRouter
* Docker
* SQLite

---

## Environment Variables

Create a `.env` file:

```env
OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY
```

---

## Run With Docker

```bash
docker compose up --build
```

Run migrations:

```bash
docker compose exec web python manage.py migrate
```

Create admin user:

```bash
docker compose exec web python manage.py createsuperuser
```

Build search index:

```bash
docker compose exec web python manage.py build_index
```

---

## URLs

Admin:

http://localhost:8000/admin/

Ask Documents:

http://localhost:8000/api/admin-ask/

API:

http://localhost:8000/api/ask/

---

## Testing

1. Login to Admin.
2. Upload DOCX files.
3. Build index. its automatedly done when change or add a doc
4. Open Ask Documents page.
5. Ask questions.
6. Verify sources and answers.

---

## Notes

* Rebuild the FAISS index whenever documents change. its automatedly done when change or add a doc
* Superusers can access all documents.
* Staff users can access public documents and their own private documents.
* Sample documents are included in the `sample_documents` folder.
* API documentation is available in `API_DOCUMENTATION.md`.
