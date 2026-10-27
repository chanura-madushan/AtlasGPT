
from pathlib import Path
from pypdf import PdfReader

def load_txt(file_path: str) -> str:
   # Extract text from a TXT file.
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if path.suffix.lower() != ".txt":
        raise ValueError("File must be a TXT file.")

    return path.read_text(encoding="utf-8")


def load_pdf(file_path: str) -> str:
    #Extract text from a PDF file.
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("File must be a PDF file.")

    reader = PdfReader(str(path))
    pages = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)

    return "\n".join(pages)



def load_document(file_path: str) -> str:
    #Load text from a supported document.
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".txt":
        return load_txt(file_path)

    if extension == ".pdf":
        return load_pdf(file_path)

    raise ValueError("Unsupported file type. Use PDF or TXT.")
