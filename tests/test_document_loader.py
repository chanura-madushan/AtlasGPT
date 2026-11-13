from unittest.mock import patch

from docx import Document

from src.rag.document_loader import load_docx, load_document
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
         patch("src.rag.ingest.add_documents") as mock_add, \
         patch("src.rag.ingest.delete_document"):

        mock_embed.return_value = [[0.1] * 768]

        result = ingest_document(str(file_path), user_id=999)

    assert result == 1
    mock_embed.assert_called_once()
    mock_add.assert_called_once()