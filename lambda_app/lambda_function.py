from pydantic import ValidationError

from lambda_utils import (
    setup_logger,
    get_api_key,
    request_content,
    prepare_messages,
    post_to_sqs,
)
from lambda_classes import LambdaEvent


logger = setup_logger("Guardian Data Streaming Lambda")


def lambda_handler(event: dict, context: dict) -> dict:
    """Lambda handler: makes api request, wrangles reponse and uploads to SQS.

    - Validates that passed event is suitable for processing
    - Invokes get_api_key to retrieve api key
    - Invokes request_content using data from event to get data from API
    - Calls prepare_messages to wrangle the response into an SQS-compatible message
    - Invokes post_to_sqs to post the prepared messages to an SQS queue.

    Args
    ----
        event: a dict of keys and values defined upstream.
            Should contain the following keys:
                {
                "SearchTerm": "scary futuristic blobs",
                "FromDate": "2015-12-17",
                "queue": "guardian_content"
                }
        context: an object with attributes reflecting AWS runtime information

    Returns
    -------
        A dict containing a status code reflecting the success or failure of
        the execution and a body containing further information, e.g.,
            {
            "staus_code": 500,
            "body": "Critical error experienced while processing request."
            }

    """

    logger.info("Guardian data streaming lambda invoked")

    # Validate event
    try:
        logger.info("Validating event")
        event = LambdaEvent(**event)
        logger.info("Event validated")
    except ValidationError as e:
        logger.error(f"Invalid event. Event = {event}")
        return {"statusCode": 400, "body": f"{str(e)}"}

    # Capture values from event
    queue, search_term  = event.queue, event.SearchTerm
    from_date, to_date  = event.FromDate, event.ToDate 

    # Get API key from Secrets Manager
    try:
        logger.info("get_api_key invoked")
        api_key = get_api_key()
        logger.info("get_api_key executed successfully")
    except Exception as e:
        logger.critical(f"Critical error during get_api_key execution: {repr(e)}")
        return {
            "statusCode": 500,
            "body": "Critical error experienced while processing request.",
        }

    # Make get request using search terms and API key
    try:
        logger.info(f"request_content invoked, search_term = {search_term}")
        raw_response = request_content(api_key, search_term, from_date, to_date)
        logger.info(
            f"request_content executed successfully, search_term = {search_term}"
        )
    except Exception as e:
        logger.critical(f"Critical error during request_content execution: {repr(e)}")
        return {
            "statusCode": 500,
            "body": "Critical error experienced while processing request",
        }

    # Handle failed responses based on http code
    if raw_response['StatusCode'] == 400:
        return {"statusCode": 400, "body": raw_response['Body']['Message']}
    elif raw_response['StatusCode'] == 500:
        message = raw_response['Body']['Message']
        return {"statusCode": 424, "body": f"Guardian API failure: {message}"}
    elif raw_response['StatusCode'] != 200:
        message = raw_response['Body']['Message']
        logger.error(
            f"unexpected API response. {raw_response['StatusCode']=}, {message=}"
        )
        return {"statusCode": 424, "body": f"Guardian API failure: {message}"}
    
    # Handle search term that yields 0 articles
    if not raw_response['Body']['response']['results']:
        return {
            "statusCode": 200,
            "body": "Search yielded 0 articles",
        }

    # Prepare content into messages
    try:
        logger.info("prepare_messages invoked")
        prepared_messages = prepare_messages(raw_response["Body"])
        logger.info("prepare_messages executed successfully")
    except Exception as e:
        logger.critical(f"Critical error during prepare_messages execution: {repr(e)}")
        return {
            "statusCode": 500,
            "body": "Critical error experienced while processing request",
        }

    # Post messages to SQS
    try:
        logger.info("post_to_sqs invoked")
        post_to_sqs(queue, prepared_messages)
        logger.info("post_to_sqs executed successfully")
    except Exception as e:
        logger.critical(f"Critical error during post_to_sqs execution: queue = {queue}, error = {repr(e)}")
        return {
            "statusCode": 500,
            "body": "Critical error experienced while processing request",
        }

    return {
        "statusCode": 200,
        "body": f"{len(prepared_messages)} messages uploaded to SQS",
    }
