from unittest.mock import patch, Mock
import sys, os

sys.path.append("./lambda_app")

# Remove the Lambda layer path from sys.path
lambda_layer_path = os.path.join(os.getcwd(), 'layers', 'python')
if lambda_layer_path in sys.path:
    sys.path.remove(lambda_layer_path)


import pytest
from botocore.exceptions import ClientError
from requests import RequestException

from lambda_function import lambda_handler


### Fixtures ###

@pytest.fixture
def mock_get_api_key():
    with patch("lambda_function.get_api_key") as mock_get_api_key:
        yield mock_get_api_key


@pytest.fixture
def mock_request_content():
    with patch("lambda_function.request_content") as mock_request_content:
        yield mock_request_content


@pytest.fixture
def mock_prepare_messages():
    with patch("lambda_function.prepare_messages") as mock_prepare_messages:
        yield mock_prepare_messages


@pytest.fixture
def mock_post_to_sqs():
    with patch("lambda_function.post_to_sqs") as mock_post_to_sqs:
        yield mock_post_to_sqs


@pytest.fixture
def patch_all(
    mock_get_api_key,
    mock_request_content,
    mock_prepare_messages,
    mock_post_to_sqs
):
    yield {
        "mock_get_api_key": mock_get_api_key,
        "mock_request_content": mock_request_content,
        "mock_prepare_messages": mock_prepare_messages,
        "mock_post_to_sqs": mock_post_to_sqs
    }


@pytest.fixture
def test_event():
    return {
        "SearchTerm": "futuristic egg",
        "FromDate": "2025-01-01",
        "queue": "guardian_content",
    }


@pytest.fixture
def client_error_message():
    client_error_message = {
        "Error": {"Code": "NoWayDude", "Message": "You've gone too far this time."},
        "ResponseMetadata": {
            "RequestId": "12345",
            "HTTPStatusCode": 404,
            "HostId": "host-id-example",
        },
    }
    return client_error_message


### Tests begin here ###


class TestOutput:
    def test_returns_dict(self, patch_all, test_event):
        output = lambda_handler(test_event, "AWS")
        assert isinstance(output, dict)

    def test_dict_has_status_code_key(self, patch_all, test_event):
        output = lambda_handler(test_event, "AWS")
        assert "statusCode" in output

    def test_dict_has_body_key(self, patch_all, test_event):
        output = lambda_handler(test_event, "AWS")
        assert "body" in output

    def test_return_0_articles(self, patch_all, test_event):
        patch_all['mock_prepare_messages'].return_value = []
        output = lambda_handler(test_event, "AWS")
        assert output == {"statusCode": 200, "body": "0 articles retrieved"}


class TestLoggingAndErrorHandling:
    def test_catches_and_logs_invalid_events(self, caplog):
        expected_log = "Invalid event. Event = "
        output = lambda_handler({}, "AWS")
        assert expected_log in caplog.text

    def test_catches_and_logs_get_api_key_error(
        self, mock_get_api_key, test_event, caplog, client_error_message
    ):
        expected_log = "Critical error during get_api_key execution: ClientError"
        mock_get_api_key.side_effect = ClientError(
            client_error_message,
            operation_name="get_secret_value",
        )
        lambda_handler(test_event, "AWS")
        assert expected_log in caplog.text

    def test_catches_and_logs_request_content_error(
        self,
        mock_get_api_key,
        test_event,
        mock_request_content,
        caplog,
        client_error_message,
    ):
        expected_log = (
            "Critical error during request_content execution: RequestException"
        )
        mock_request_content.side_effect = RequestException("Yelp!")
        lambda_handler(test_event, "AWS")
        assert expected_log in caplog.text

    def test_catches_and_logs_prepare_messages_error(
        self,
        test_event,
        patch_all,
        caplog
    ):
        expected_log = (
            "Critical error during perpare_messages execution: KeyError('Burp!')"
        )
        patch_all['mock_prepare_messages'].side_effect = KeyError("Burp!")
        output = lambda_handler(test_event, "AWS")
        assert expected_log in caplog.text

    def test_catches_and_logs_post_to_sqs_error(
        self,
        test_event,
        patch_all,
        client_error_message,
        caplog
    ):
        expected_log = (
            "Critical error during post_to_sqs execution: ClientError"
        )
        patch_all['mock_post_to_sqs'].side_effect = ClientError(client_error_message,
            operation_name="send_message_batch",)
        output = lambda_handler(test_event, "AWS")
        assert expected_log in caplog.text