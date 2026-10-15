from unittest.mock import Mock, patch

from src.llm.ollama_client import ask_ollama


@patch("src.llm.ollama_client.requests.post")
def test_ask_ollama_success(mock_post):
    mock_response = Mock()
    mock_response.json.return_value = {"response": "AI enables machines to perform tasks that normally require human intelligence."}
    mock_post.return_value = mock_response

    answer = ask_ollama("Explain artificial intelligence.")

    assert answer == "AI enables machines to perform tasks that normally require human intelligence."
    mock_post.assert_called_once()


 
@patch("src.llm.ollama_client.requests.post")
def test_ask_ollama_timeout(mock_post):
    import requests

    mock_post.side_effect = requests.exceptions.Timeout

    answer = ask_ollama("Test prompt")

    assert answer == "Error: Ollama took too long to respond."




 
@patch("src.llm.ollama_client.requests.post")
def test_ask_ollama_connection_error(mock_post):
    import requests

    mock_post.side_effect = requests.exceptions.ConnectionError

    answer = ask_ollama("Test prompt")

    assert answer == "Error: Could not connect to Ollama. Is Ollama running?"



 
@patch("src.llm.ollama_client.requests.post")
def test_ask_ollama_http_error(mock_post):
    import requests

    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "500 Server Error"
    )
    mock_post.return_value = mock_response

    answer = ask_ollama("Test prompt")

    assert answer.startswith("Error communicating with Ollama:")