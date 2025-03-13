from unittest.mock import patch, Mock

import pytest

from lambda_app.lambda_utils import request_content


@pytest.fixture
def mock_200_response():
    mock_200_response = Mock()
    mock_200_response.status_code = 200
    mock_200_response.json.return_value = {"response": "test response"}
    return mock_200_response


@pytest.fixture
def mock_400_response():
    mock_400_response = Mock()
    mock_400_response.status_code = 400
    mock_400_response.json.return_value = {
        "response": {
            "status": "error",
            "message": "Invalid search query syntax. You can use AND and OR operators, parentheses to specify precedence, and double quotes for phrases.",
        }
    }
    return mock_400_response


@pytest.fixture
def mock_500_response():
    mock_500_response = Mock()
    mock_500_response.status_code = 500
    mock_500_response.json.return_value = {
        "response": {"status": "error", "message": "Something broke :("}
    }
    return mock_500_response


@patch("lambda_app.lambda_utils.get_request")
def test_uses_parameters_in_request(mock_get_request, mock_200_response):
    mock_get_request.return_value = mock_200_response
    request_content("test-API-key", "test-search-term", "2023-03-28", "2024-08-23")
    exp_call = "https://content.guardianapis.com/search?q=test-search-term&from-date=2023-03-28&to-date=2024-08-23&show-fields=wordcount&show-blocks=body&api-key=test-API-key"
    mock_get_request.assert_called_with(exp_call)


@patch("lambda_app.lambda_utils.get_request")
def test_returns_dict_with_status_code_and_body_keys(
    mock_get_request, mock_200_response
):
    mock_get_request.return_value = mock_200_response
    output = request_content(
        "test-API-key", "test-search-term", "2023-03-28", "2024-08-23"
    )
    assert isinstance(output, dict)
    assert output["StatusCode"]
    assert output["Body"]


@patch("lambda_app.lambda_utils.get_request")
def test_takes_status_code_from_response(mock_get_request, mock_500_response):
    mock_get_request.return_value = mock_500_response
    output = request_content(
        "test-API-key", "test-search-term", "2023-03-28", "2024-08-23"
    )
    assert output["StatusCode"] == mock_500_response.status_code

@patch("lambda_app.lambda_utils.get_request")
def test_takes_body_from_response(mock_get_request, mock_400_response):
    mock_get_request.return_value = mock_400_response
    output = request_content(
        "test-API-key", "test-search-term", "2023-03-28", "2024-08-23"
    )
    assert output["Body"] == mock_400_response.json()