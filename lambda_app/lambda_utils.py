import logging
from json import dumps

import boto3
from requests import get as get_request


class JSONFormatter(logging.Formatter):
    """A JSON formatter for logging

    Takes a log record and returns the record in serialised JSON format
    """

    def format(self, record):
        log_obj = {
            "asctime": self.formatTime(record, self.datefmt),
            "levelname": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "filename": record.filename,
            "funcName": record.funcName,
        }
        return dumps(log_obj)
    

def setup_logger(logger_name: str):
    """Returns logger at debug level with JSON formatter

    - Creates logger with passed logger name
    - Sets logger level to debug
    - Removes existing handler
    - Adds JSON handler with JSON formatter to logger

    Args
    ----
        logger_name: a string to be used as the logger name

    Returns
    -------
        A logger object set to debug level with a JSON formatter

    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    json_handler = logging.StreamHandler()
    formatter = JSONFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(filename)s %(funcName)s"
    )
    json_handler.setFormatter(formatter)
    logger.addHandler(json_handler)
    logger.propagate = False

    return logger


def get_api_key() -> str:
    """Uses boto3 to request AWS secret – a Guardian API key"""
    secret_name = "Guardian-API-Key"
    client = boto3.client("secretsmanager")
    get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    return get_secret_value_response["SecretString"]


def request_content(
    api_key: str, search_term: str, from_date: str, to_date: str
) -> dict | None:
    """Makes get request to Guardian API using params

    - Creates request URL using passed search term
    - Adds from_date and to_date queries to URL if passed
    - Makes get request to Guardian API using passed key

    Args
    ----
        api_key: a Guardian API key
        search_term: a word, phrase or Boolean query
        from_date: date string in format YYYY-MM-DD
        to_date: date string in format YYYY-MM-DD

    Returns
    -------
        For a 200 response:
            A deserialised response from
            the Guardian API search endpoint
            https://open-platform.theguardian.com/documentation/search


        For any other response:
            None

    """
    url = f"https://content.guardianapis.com/search?q={search_term}"

    if from_date:
        url += f"&from-date={from_date}"

    if to_date:
        url += f"&to-date={to_date}"

    options = "&show-fields=wordcount&show-blocks=body"

    response = get_request(url + options + f"&api-key={api_key}")

    return {"StatusCode": response.status_code, "Body": response.json()}


def prepare_messages(raw_response):
    """Prepares API responses into desired format for SQS

    - Accesses articles list from raw response
    - Creates num range == num articles for SQS ids
    - Iterates over articles creating list of dicts
      in required shape – one dict per article.

    Args
    ----
        raw_response: a deserialised 200 response from
            the Guardian API search endpoint
            https://open-platform.theguardian.com/documentation/search

    Returns
    -------
        A list of dicts. Each dict contains data for Guardian article.

    """
    articles = raw_response["response"]["results"]

    id_range = range(1, len(articles) + 1)
    id_gen = iter(id_range)

    def shorten(x):  # Shortens a string to last full stop before the 1000th char
        return x[:1001].rsplit(".", 1)[0] + "."

    prepared_messages = [
        {
            "Id": str(next(id_gen)),
            "MessageBody": dumps(
                {
                    "Title": x["webTitle"],
                    "Section": x["sectionName"],
                    "PublicationDate": x["webPublicationDate"],
                    "WordCount": x["fields"]["wordcount"],
                    "Url": x["webUrl"],
                    "Preview": shorten(x["blocks"]["body"][0]["bodyTextSummary"]),
                }
            ),
        }
        for x in articles
    ]

    return prepared_messages


def post_to_sqs(queue: str, messages: list):
    """Posts messages to AWS SQS using boto3"""
    sqs_client = boto3.client("sqs")
    queue_url = sqs_client.get_queue_url(QueueName=queue)["QueueUrl"]
    response = sqs_client.send_message_batch(QueueUrl=queue_url, Entries=messages)
    return response


