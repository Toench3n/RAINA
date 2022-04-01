# In this class a scheduled function are defined which send out messages to all telegram users. This is being
# implemented by sending a post request to the telegram webhook for the corresponding bot. This post request will
# update the conversation with a message containing an intent on which Rasa will react:
# https://core.telegram.org/bots/webhooks#testing-your-bot-with-updates
# https://core.telegram.org/bots/api#update
# https://stackoverflow.com/questions/48530174/telegram-bot-api-simulate-user-interaction

# This is a common practice to make bots reach out to users "by themselves" at a specific point of time and was also
# used by Ludwig Horner in his Bachelor's Thesis (2019) as well as by Wenjian Li in his Master's Thesis (2020).

# To avoid a Telegram Bot API rate limit error when rasa starts reacting/sending the messages there will be a 0.5s pause
# after the 25th POST request to stay under the maximum of 30 requests per second:
# https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this

# For scheduling the schedule library has been used:
# https://schedule.readthedocs.io/en/stable/examples.html#run-a-job-every-x-minute

# python imports
import json
import os
import time
import requests
import schedule
import datetime
import threading
import logging

# own classes
from . import sqlite_client

# get telegram tokens from env vars
telegram_webhook = os.getenv("TELEGRAM_WEBHOOK_URL")

# create logger
logger = logging.getLogger('custom.message_scheduler')


def build_payload(user_id: int, intent: str, offset: int) -> json:
    """
    This function builds the payload for the POST request to the telegram webhook.
    :param user_id: a user_if from the database
    :param intent: the intent to be sent by "the user", i.e. "/{intent}"
    :param offset: the number of the user in the list
    :return: a json object to be sent to the webhook
    """
    # convert date to int and append the message offset to it to get a usable id
    generated_id = int(datetime.datetime.now().strftime("%d%m%H") + "%s" % offset)
    current_timestamp = time.time()

    # build the payload
    payload = {
        "update_id": generated_id,
        "message": {
            "message_id": generated_id,
            "chat": {
                "id": user_id,
                "type": "private"
            },
            "date": current_timestamp,
            "text": intent
        }
    }

    return payload


def is_telegram_user(user_id: str) -> bool:
    """
    Telegram expects the user_id to be an integer, so every user_id which is not an integer will be skipped in the
    sending process of the check-ins since they can not receive scheduled messages. This is the case for all users which
    were created using the RasaX testing instance for testing the rasa NLU.

    :param user_id: the user_id retrieved from the database
    :return: true if the user_id is valid for use in telegram, false otherwise
    """

    # Telegram expects the user_id to be an integer, so every user_id which is not an integer will be skipped.
    if user_id.isnumeric():
        return True
    else:
        # RasaX users from the developing process do not have a valid telegram_id and will not get weekly overviews
        logger.info("Skipping user with invalid telegram id: %s" % user_id)
        return False


def send_intent(intent: str):
    """
    This function sends a post request to the webhook for all user-chats with the given intent. This function is used to
    aggregate the sending of the different check-ins into one function by just passing the intent. The scheduled
    functions simply call this function with their intent.

    :param intent: the intent defined in the domain.yml which will trigger a rule (e.g. "/EXTERNAL_trigger_rule")
    """

    logger.info("Starting to send intent: %s to all telegram users" % intent)
    users = sqlite_client.get_all_users()

    user_number = 0
    for user in users:
        # Telegram expects the user_id to be an integer, so every user_id which is not an integer will be skipped.
        if user_number == 24:
            time.sleep(0.5)

        # get user_id
        user_id = user[0]

        if is_telegram_user(user_id):
            logger.info("Sending intent to user: %s" % user_id)

            # building the payload with the intent to trigger the corresponding rule rule and post it to the webhook
            content = build_payload(int(user_id), intent, user_number)
            response = requests.post(telegram_webhook, json=content)
            logger.info("Telegram response was: %s" % response.text)
            user_number = user_number + 1

    logger.info("Finished sending all intents")


# time has to be given in UTC (german time -1h) with leading 0 if necessary
@schedule.repeat(schedule.every().day.at("07:00"))  # i.e. 08:00 german time
def send_morning_check_in():
    """
    This function calls the send_intent function with the intent "/EXTERNAL_send_morning_check_in" to trigger the rule
    starting the morning checkin for all telegram users.
    """

    # implementation analogue to the weekly check-in
    logger.info("Calling function to send evening check-ins")
    send_intent("/EXTERNAL_send_morning_check_in")


# time has to be given in UTC (german time -1h) with leading 0 if necessary
@schedule.repeat(schedule.every().day.at("16:00"))  # i.e. 17:00 german time
def send_evening_check_in():
    """
    This function calls the send_intent function with the intent "/EXTERNAL_send_evening_check_in" to trigger the rule
    starting the evening checkin for all telegram users.
    """

    # implementation analogue to the weekly check-in
    logger.info("Calling function to send evening check-ins")
    send_intent("/EXTERNAL_send_evening_check_in")


# time has to be given in UTC (german time -1h) with leading 0 if necessary
@schedule.repeat(schedule.every().sunday.at("19:00"))  # i.e. 20:00 german time
def send_weekly_check_in():
    """
    This function calls the send_intent function with the intent "/EXTERNAL_send_weekly_check_in" to trigger the rule
    starting the weekly checkin for all telegram users.
    """

    logger.info("Calling function to send weekly check-ins")
    send_intent("/EXTERNAL_send_weekly_check_in")


# this loop will check every 10 seconds if there is a task scheduled and run it.
def check_scheduled_tasks():
    logger.info("Checking for pending tasks")
    schedule.run_pending()
    timer = threading.Timer(10, check_scheduled_tasks)
    timer.start()


# start loop checking for scheduled tasks
check_scheduled_tasks()
