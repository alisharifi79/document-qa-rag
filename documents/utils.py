from docx import Document as DocxDocument

def extract_docx_text(file_path):
    doc = DocxDocument(file_path)

    full_text = []

    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text)

    return "\n".join(full_text)