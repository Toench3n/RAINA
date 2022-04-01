# in this file the intents which can be sent when clicking on a button for answering the check-in questions will be
# processed into values which can be inserted into the database
# e.g. BUTTON_morning_check_in_1 -> title: "morning_check_in", score: 1

import logging

# create logger
logger = logging.getLogger('custom.answer_splitter')


def process(intent: str):
    logger.info("Splitting intent: %s" % intent)
    # cut of the button prefix, remaining: "morning_check_in_1"
    intent = intent.replace("BUTTON_", "")

    # split the string at the last delimiter
    values = intent.rsplit("_", 1)

    # assign values
    title = values[0]
    score = int(values[1])

    logger.info("Returning: title = %s, score = %s" % (title, score))
    return title, score
