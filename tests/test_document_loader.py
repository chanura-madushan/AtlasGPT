from unittest.mock import patch, Mock
import pytest
from docx import Document

from src.rag.document_loader import load_docx, load_document, load_pdf
from src.rag.ingest import ingest_document
def test_load_docx(tmp_path):
    file_path = tmp_path / "sample.docx"

    document = Document()
    document.add_paragraph("AtlasGPT is an AI assistant.")
    document.add_paragraph("It supports document question answering.")
    document.save(file_path)

    result = load_docx(str(file_path))

    assert "AtlasGPT is an AI assistant." in result
    assert "It supports document question answering." in result

def test_load_document_docx(tmp_path):
    file_path = tmp_path / "sample.docx"

    document = Document()
    document.add_paragraph("Testing AtlasGPT document routing.")
    document.save(file_path)

    result = load_document(str(file_path))

    assert "Testing AtlasGPT document routing." in result


def test_ingest_docx(tmp_path):
    file_path = tmp_path / "sample.docx"

    document = Document()
    document.add_paragraph("AtlasGPT supports DOCX ingestion.")
    document.save(file_path)

    with patch("src.rag.ingest.embed_texts") as mock_embed, \
        patch("src.rag.ingest.add_documents") as mock_add:

        mock_embed.return_value = [[0.1] * 768]

        result = ingest_document(str(file_path), user_id=999)

    assert result == 1
    mock_embed.assert_called_once()
    mock_add.assert_called_once()

def test_load_pdf_rejects_invalid_file(tmp_path):
    file_path = tmp_path / "fake.pdf"
    file_path.write_bytes(b"This is not a PDF file.")

    with pytest.raises(ValueError, match="Invalid PDF file"):
        load_pdf(str(file_path))

def test_load_docx_rejects_invalid_file(tmp_path):
    file_path = tmp_path / "fake.docx"
    file_path.write_bytes(b"This is not a DOCX file.")

    with pytest.raises(ValueError, match="Invalid DOCX file"):
        load_docx(str(file_path))



def test_load_pdf_pages_preserves_page_numbers(tmp_path):
    from src.rag.document_loader import load_pdf_pages

    file_path = tmp_path / "sample.pdf"
    file_path.write_bytes(b"%PDF-1.4")

    mock_reader = Mock()
    mock_reader.pages = [Mock(), Mock(), Mock()]

    mock_reader.pages[0].extract_text.return_value = "First page content."
    mock_reader.pages[1].extract_text.return_value = ""
    mock_reader.pages[2].extract_text.return_value = "Third page content."

    with patch(
        "src.rag.document_loader.PdfReader",
        return_value=mock_reader,
    ):
        result = load_pdf_pages(str(file_path))

    assert result == [
        {"page": 1, "text": "First page content."},
        {"page": 3, "text": "Third page content."},
    ]




def test_ingest_pdf_preserves_page_numbers(tmp_path):
    file_path = tmp_path / "sample.pdf"
    file_path.write_bytes(b"%PDF-1.4")

    mock_pages = [
        {"page": 1, "text": "First page content."},
        {"page": 3, "text": "Third page content."},
    ]

    with patch(
        "src.rag.ingest.load_pdf_pages",
        return_value=mock_pages,
    ), patch(
        "src.rag.ingest.split_text",
        side_effect=lambda text: [text],
    ), patch(
        "src.rag.ingest.embed_texts",
        return_value=[[0.1] * 768, [0.2] * 768],
    ), patch(
        "src.rag.ingest.add_documents",
    ) as mock_add:

        result = ingest_document(str(file_path), user_id=999)

    assert result == 2

    mock_add.assert_called_once_with(
        [
            "First page content.",
            "Third page content.",
        ],
        [[0.1] * 768, [0.2] * 768],
        "sample.pdf",
        999,
        page_numbers=[1, 3],
    )
