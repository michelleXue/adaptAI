import redis
import logging, json
import time,httpx,traceback, threading
from fastapi import HTTPException

# ✅ Connect to Redis
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# Stream and Consumer Group details
STREAM_NAME = 'preprocess_request'
GROUP_NAME = 'post-processing-grp'
CONSUMER_NAME = 'preprocess_request'

# Define backend microservices URLs
POSTPROCESSING_API_URL = "http://localhost:8004/postprocessing/"

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:\t %(asctime)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Ensure the group exists
try:
    redis_client.xgroup_create(STREAM_NAME, GROUP_NAME, id='0', mkstream=True)
    logger.info("Group {} created.".format(GROUP_NAME))
except redis.exceptions.ResponseError as e:
    if "BUSYGROUP" not in str(e):
        raise  # Ignore error if group already exists


def redis_polling():
    """Continuously polls Redis stream for new messages."""
    while True:
        try:
            messages = redis_client.xreadgroup(
                groupname=GROUP_NAME,
                consumername=CONSUMER_NAME,
                streams={STREAM_NAME: '>'},  # Read new messages
                count=10,
                block=5000  # Blocks for 5 sec if no messages are available
            )

            if messages:
                for stream, entries in messages:
                    for entry_id, data in entries:
                        logger.info(f"Processing message {entry_id}: {data}")
                        # Forwarding the request to post procecessing server
                        """Main function that processes data and forwards it in a separate thread."""
                        thread = threading.Thread(target=forward_request, args=(data,))
                        thread.start()
                        # Acknowledge the message after processing
                        redis_client.xack(STREAM_NAME, GROUP_NAME, entry_id)
            else:
                print("No new messages. Polling again...")

        except Exception as e:
            print(f"Error in Redis polling: {e}")
            time.sleep(5)  # Wait before retrying

def forward_request(ai_query_response):
    logger.info("Forwarding request")
    with httpx.Client() as client:  # ✅ Use synchronous `httpx.Client()` instead of `asyncClient`
        try:
            # ✅ Ensure `result` is correctly parsed as a dictionary
            if isinstance(ai_query_response["result"], str):
                try:
                    ai_query_response["result"] = json.loads(ai_query_response["result"].replace("'", '"'))
                except json.JSONDecodeError as e:
                    logger.error(f"JSON Decode Error: {str(e)} - Raw Data: {ai_query_response['result']}")
                    ai_query_response["result"] = {"error": "Invalid result format"}

            # ✅ Convert `id` to an integer if it's a valid number
            if "id" in ai_query_response and isinstance(ai_query_response["id"], str) and ai_query_response[
                "id"].isdigit():
                ai_query_response["id"] = int(ai_query_response["id"])
            logger.info(f"Formatted Data Before Sending: {ai_query_response}")

            response = client.post(POSTPROCESSING_API_URL, json=ai_query_response)
            if response.status_code != 200:
                raise HTTPException(status_code=500,
                                    detail=f"Failed to send AIQueryResponse to external API: {response.text}")

        except httpx.HTTPStatusError as http_err:
            logger.error(f"HTTP Error: {http_err.response.status_code} - {http_err.response.text}")
            raise HTTPException(status_code=http_err.response.status_code,
                                detail=f"External API Error: {http_err.response.text}")

        except httpx.RequestError as req_err:
            logger.error(f"Request Error: {str(req_err)}")
            raise HTTPException(status_code=500,
                                detail=f"Failed to send request to postprocessing API: {str(req_err)}")

        except ValueError:
            raise HTTPException(status_code=500,
                                detail=f"Invalid JSON received from postprocessing API: {response.text}")

        except Exception as e:
            error_type = type(e).__name__  # Get the exception type
            error_details = traceback.format_exc()  # Get full traceback
            logger.error(f"Exception Type: {error_type}\nDetails: {error_details}")
            raise HTTPException(status_code=500, detail=f"Unexpected error ({error_type}): {str(e)}")

# Keep the main thread alive
try:
    while True:
        redis_polling()
        time.sleep(1)
except KeyboardInterrupt:
    print("Shutting down...")
