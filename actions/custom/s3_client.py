import datetime
import logging
import os
import boto3  # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html

# create logger
logger = logging.getLogger('custom.s3_client')

# name of the AWS S3 bucket to use
aws_bucket_name = os.getenv("AWS_BUCKET_NAME")
# retrieve by uploading a file to the bucket manually and copy the Object URL. Delete the file name from the URL, the
# result should be something like this: https://<bucketname>.s3.<serverlocation>.amazonaws.com
aws_bucket_url = os.getenv("AWS_BUCKET_URL")


def upload_image_to_s3(image_path: str, user_id: str) -> str:
    # connect to s3
    # WARNING: env vars AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY have to be set!
    s3 = boto3.client("s3")

    # generate file name from user_id
    filename = f"%s.png" % user_id

    # upload image to S3
    logger.info("uploading image to S3 for user: %s" % user_id)
    s3.upload_file(image_path, aws_bucket_name, filename)

    # adding a timestamp to the URL so the channels do not use cached images from past requests
    # https://stackoverflow.com/questions/42719409/telegram-bot-image-from-url-undesired-cache
    timestamp_hash = hash(datetime.datetime.now())

    # return URL to use in RasaX and Telegram to display image
    # URLs look like: https://<bucketname>.s3.<serverlocation>.amazonaws.com/<user_id>.png?<timestamp_hash>
    logger.info("Generating link for user: %s" % user_id)
    return aws_bucket_url + "/" + filename + "?" + str(timestamp_hash)
