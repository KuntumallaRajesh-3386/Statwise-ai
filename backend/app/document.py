import fitz


def extract_pdf_text(file_path: str):
    doc = fitz.open(file_path)

    pages = []

    for page_number, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()

        if text:
            pages.append({
                "page": page_number,
                "text": text
            })

    doc.close()

    return pages


def chunk_pages(pages, chunk_size=1200, overlap=200):
    chunks = []

    for page in pages:
        text = page["text"]
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))

            chunks.append({
                "page": page["page"],
                "text": text[start:end]
            })

            if end == len(text):
                break

            start = end - overlap

    return chunks