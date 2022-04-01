# This files contains code for all custom actions RAINA uses. Those include actions interacting with the database and
# actions for managing reminders.
# There are several cases of similar code fragments, due to the fact that every custom action is its own python class.
# Custom functions for mapping the pyramids or creating and uploading the images are located in the custom folder.

# rasa imports
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

# python imports
from typing import Any, Text, Dict, List
import datetime

# own classes
from .custom import enums
from .custom import validity_checker as checker
from .custom import sqlite_client
from .custom import pyramid_creator
from .custom import s3_client
from .custom import intent_splitter


# This action adds a portion to the database
class ActionAddPortion(Action):

    def name(self) -> Text:
        return "action_add_portion"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # getting primary keys used in the database
        user_id = tracker.sender_id
        date = datetime.date.today()

        # getting the first pyramid_field passed in the last message received
        pyramid_field = next(tracker.get_latest_entity_values("pyramid_field"))

        # map pyramid_field to field to increment in the table
        field = enums.get_field_from_entity(pyramid_field)

        # if RAINA does not know the field, she will ask to rephrase and exit the action
        if field == enums.FoodTypes.UNKNOWN:
            dispatcher.utter_message(
                text="Ich habe als Feld \"%s\" erkannt und kenne das leider nicht. 😕\n"
                     "Ganze Gerichte kann ich leider nicht in ihre Bestandteile aufteilen. Überlege dir in diesem Fall "
                     "bitte, aus welchen Zutaten das Gericht besteht und welche Felder diese abdecken. \n"
                     "Wenn du ein einzelnes Feld hinzufügen wolltest, versuche bitte eine andere Bezeichnung zu "
                     "verwenden.\n"
                     "ℹ️ Du kannst mich jederzeit Fragen wie die Felder der Pyramide heißen." % pyramid_field)
            return []

        # 1 portion is being used as default
        number_of_portions = 1.0

        # trying to get a number passed by the user, which was extracted by duckling
        try:
            number_of_portions = next(tracker.get_latest_entity_values("number"))
        # if the duckling entity extractor fails to extract a number the iteration raises an exception and 1 portion is
        # being used as default number
        # e.g: "eine" is not interpreted as "1" and float numbers with points are interpreted as dates
        except StopIteration:
            pass

        # creating a new pyramid for the user, if it does not exist
        sqlite_client.insert_or_ignore_pyramid(user_id, date)

        # increment field in the database for the user by the desired amount of portions
        if checker.is_valid_for_increment(user_id, date, field, number_of_portions):
            sqlite_client.add_portion(user_id, date, field, number_of_portions)
        else:
            # set the amount to the maximum
            sqlite_client.set_portion(user_id, date, field, checker.max_portions[field.value])

            # notify the user that no more portions can be tracked for this food type
            dispatcher.utter_message(
                text="Ich kann leider nicht mehr als %d Portionen %s in deine Pyramide eintragen! "
                     "Versuche darauf zu achten nicht zu viel von einer Kategorie zu essen, "
                     "sondern deine Ernährung ausgewogen zu gestalten!" % (
                         checker.max_portions[field.value], pyramid_field))
            return []

        # create string for informing user about adding the portions
        if float(number_of_portions).is_integer():
            inform_adding = f"Ich habe %d Feld(er) %s zu deiner Pyramide hinzugefügt." % (
                number_of_portions, pyramid_field.capitalize())
        else:
            inform_adding = "Ich habe %.2f Felder %s zu deiner Pyramide hinzugefügt." % (
                number_of_portions, pyramid_field.capitalize())

        # getting the new amount for the incremented field
        result = sqlite_client.get_pyramid(user_id, date)
        number_tracked = result[field.value]
        portions_recommended = checker.recommended_portions[field.value]

        # create string to inform user about the remaining portions
        if float(number_tracked).is_integer():
            inform_remaining = "Damit hast du jetzt %d von %d Portionen %s für heute eingetragen." % (
                number_tracked, portions_recommended, pyramid_field.capitalize())
        else:
            inform_remaining = "Damit hast du jetzt %.2f von %d Portionen %s für heute eingetragen." % (
                number_tracked, portions_recommended, pyramid_field.capitalize())

        # informing the user in one message by concatenating the Strings
        dispatcher.utter_message(text=inform_adding + "\n" + inform_remaining)
        return []


# This action removes a portion from the database (analogue to adding one)
class ActionRemovePortion(Action):

    def name(self) -> Text:
        return "action_remove_portion"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_id = tracker.sender_id
        date = datetime.date.today()
        pyramid_field = next(tracker.get_latest_entity_values("pyramid_field"))
        field = enums.get_field_from_entity(pyramid_field)

        if field == enums.FoodTypes.UNKNOWN:
            dispatcher.utter_message(
                text="Ich habe als Feld \"%s\" erkannt und kenne das leider nicht. 😕\n"
                     "Versuche bitte eine andere Bezeichnung für das Feld zu verwenden.\n"
                     "ℹ️ Du kannst mich jederzeit Fragen wie die Felder der Pyramide heißen." % pyramid_field)
            return []

        number_of_portions = 1.0
        try:
            number_of_portions = next(tracker.get_latest_entity_values("number"))
        except StopIteration:
            pass

        sqlite_client.insert_or_ignore_pyramid(user_id, date)

        if checker.is_valid_for_decrement(user_id, date, field, number_of_portions):
            sqlite_client.remove_portion(user_id, date, field, number_of_portions)
        else:
            sqlite_client.set_portion(user_id, date, field, 0)
            dispatcher.utter_message(
                text="Ich kann leider nicht alle Portionen abziehen, weil du sonst weniger als 0 Felder %s "
                     "eingetragen hättest, das wäre nicht sinnvoll. Ich habe stattdessen die Anzahl an %s wieder "
                     "auf 0 gesetzt." % (pyramid_field, pyramid_field))
            return []

        # create string for informing user about adding the portions
        if float(number_of_portions).is_integer():
            inform_adding = f"Ich habe %d Feld(er) %s von deiner Pyramide abgezogen." % (
                number_of_portions, pyramid_field.capitalize())
        else:
            inform_adding = "Ich habe %.2f Felder %s von deiner Pyramide abgezogen." % (
                number_of_portions, pyramid_field.capitalize())

        # getting the new amount for the incremented field
        result = sqlite_client.get_pyramid(user_id, date)
        number_tracked = result[field.value]
        portions_recommended = checker.recommended_portions[field.value]

        # create string to inform user about the remaining portions
        if float(number_tracked).is_integer():
            inform_remaining = "Damit hast du jetzt nur noch %d von %d Portionen %s für heute eingetrage." % (
                number_tracked, portions_recommended, pyramid_field.capitalize())
        else:
            inform_remaining = "Damit hast du jetzt nur noch %.2f von %d Portionen %s für heute eingetragen." % (
                number_tracked, portions_recommended, pyramid_field.capitalize())

        # informing the user in one message by concatenating the Strings
        dispatcher.utter_message(text=inform_adding + "\n" + inform_remaining)
        return []


# This actions allows the user to ask for the remaining number of portions for the given food group
class ActionGetNumberOfPortions(Action):

    def name(self) -> Text:
        return "action_get_number_of_portions"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # getting primary keys used in the database, default date is today
        user_id = tracker.sender_id
        date = datetime.date.today()

        # getting the first pyramid_field passed in the last message received
        pyramid_field = next(tracker.get_latest_entity_values("pyramid_field"))

        # map pyramid_field to field to increment in the table
        field = enums.get_field_from_entity(pyramid_field)

        # if RAINA does not know the field, she will ask to rephrase and exit the action
        if field == enums.FoodTypes.UNKNOWN:
            dispatcher.utter_message(
                text="Ich habe als Feld %s erkannt und kenne das leider nicht. "
                     "Versuche bitte deine Nachricht anders zu formulieren." % pyramid_field)
            return []

        # checking if duckling identified a specific point of time
        try:
            # if duckling finds a time keyword (e.g. "heute"/"gestern"), it is returned as timestamp of the form:
            # 2021-11-13T00:00:00.000+01:00
            timestamp = next(tracker.get_latest_entity_values("time"))

            # just the date is needed so the time part is simply cut of
            date_parsed = timestamp.split('T')[0]

            # the string is being converted to a date object for further use
            date = datetime.datetime.strptime(date_parsed, '%Y-%m-%d').date()
        except (AttributeError, StopIteration, TypeError):
            pass

        # insert a pyramid if missing, so user get a empty pyramid if they have not tracked any portions yet
        sqlite_client.insert_or_ignore_pyramid(user_id, date)

        # fetch the users pyramid for the given date
        result = sqlite_client.get_pyramid(user_id, date)

        # get number of portions for specified field as well as the max value
        number_tracked = result[field.value]
        portions_recommended = checker.recommended_portions[field.value]

        # informing the user about the consumed portions
        if date == datetime.date.today():
            date_str = "heute"
        else:
            date_str = date.strftime('am %d.%m.%Y')

        # informing the user about the remaining portions
        if float(number_tracked).is_integer():
            dispatcher.utter_message("Du hast %s %d von %d Portionen %s eingetragen." % (
                date_str, number_tracked, portions_recommended, pyramid_field.capitalize()))
        else:
            dispatcher.utter_message("Du hast %s %.2f von %d Portionen %s eingetragen." % (
                date_str, number_tracked, portions_recommended, pyramid_field.capitalize()))
        return []


# This action returns the pyramid for the current day
class ActionShowSinglePyramid(Action):
    def name(self) -> Text:
        return "action_show_single_pyramid"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # getting primary keys used in the database, default date is today
        user_id = tracker.sender_id
        date = datetime.date.today()

        # checking if duckling identified a specific point of time
        try:
            # if duckling finds a time keyword (e.g. "heute"/"gestern"), it is returned as timestamp of the form:
            # 2021-11-13T00:00:00.000+01:00
            timestamp = next(tracker.get_latest_entity_values("time"))

            # just the date is needed so the time part is simply cut of
            date_parsed = timestamp.split('T')[0]

            # the string is being converted to a date object for further use
            date = datetime.datetime.strptime(date_parsed, '%Y-%m-%d').date()

        except (AttributeError, StopIteration, TypeError):
            pass

        # insert a pyramid if missing, so user get a empty pyramid if they have not tracked any portions yet
        sqlite_client.insert_or_ignore_pyramid(user_id, date)

        # fetch the users pyramid for the given date
        result = sqlite_client.get_pyramid(user_id, date)

        # generate image for the given pyramid
        image_path = pyramid_creator.generate_pyramid_image(result)

        # upload image to AWS S3 and retrieve URL
        image_url = s3_client.upload_image_to_s3(image_path, user_id)

        # format the dates to the german notation
        if date == datetime.date.today():
            date_str = "heute"
        else:
            date_str = date.strftime('den %d.%m.%Y')

        # respond to the user and send the generated imageURL to show the image of the user's pyramid
        dispatcher.utter_message("Hier ist deine Pyramide für %s" % str(date_str), image=image_url)

        return []


# This action returns the average pyramid for the given time frame
class ActionShowAveragePyramid(Action):
    def name(self) -> Text:
        return "action_show_average_pyramid"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # getting the user_id as primary key, the date is extracted by duckling. If this does not work, the user will
        # get a message with further instructions
        user_id = tracker.sender_id

        # checking if duckling identified a specific time frame
        try:
            # if duckling finds a time frame, it is returned as a string/dictionary of the form:
            # {'to': '2021-11-13T00:00:00.000+01:00', 'from': '2021-11-10T00:00:00.000+01:00'}
            dates = next(tracker.get_latest_entity_values("time"))

            # just the date is needed so the time part is simply cut of
            from_parsed = dates['from'].split('T')[0]
            to_parsed = dates['to'].split('T')[0]

            # the string is being converted to a date object for further use
            start_date = datetime.datetime.strptime(from_parsed, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(to_parsed, '%Y-%m-%d').date()

        except (AttributeError, StopIteration, TypeError):
            dispatcher.utter_message(
                "Ich habe deine Zeitangabe leider nicht verstanden. Schreibe etwas wie: \"Wie sieht meine "
                "durchschnittliche Pyramide der letzten 7 Tage aus?\" oder \"Wie sieht meine "
                "Pyramide vom 01.12.2021 bis zum 15.12.2021 aus?\"")
            return []

        # insert a pyramid for the end_date if missing, so user get a empty pyramid in case they have not tracked any
        # portions in the given timeframe yet
        sqlite_client.insert_or_ignore_pyramid(user_id, end_date)

        # fetch the users average pyramid for the given time interval
        result = sqlite_client.get_avg_pyramid(user_id, start_date, end_date)

        # generate image for the given pyramid
        image_path = pyramid_creator.generate_pyramid_image(result)

        # upload image to AWS S3 and retrieve URL
        image_url = s3_client.upload_image_to_s3(image_path, user_id)

        # format the dates to the german notation
        start_date = start_date.strftime('%d.%m.%Y')
        end_date = end_date.strftime('%d.%m.%Y')

        # respond to the user and send the generated imageURL to show the image of the user's pyramid
        dispatcher.utter_message(
            "Hier ist deine durchschnittliche Pyramide für den Zeitraum vom %s bis zum %s" % (
                str(start_date), str(end_date)),
            image=image_url)

        return []


# This action is being called when starting the initial conversation, it adds the user_id to the database which will be
# used for scheduled checkIns
class ActionAddUser(Action):
    def name(self) -> Text:
        return "action_add_user"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_id = tracker.sender_id
        date = datetime.date.today()

        sqlite_client.insert_or_ignore_user(user_id, date)

        return []


# this action is being called when the scheduler triggered the rule and sends the user the pyramid for the last 7 days
class ActionWeeklyCheckIn(Action):
    def name(self) -> Text:
        return "action_weekly_check_in"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # getting the userId and calculating the timestamps
        user_id = tracker.sender_id
        start_date = datetime.date.today() - datetime.timedelta(days=7)
        end_date = datetime.date.today()

        # analogue to "ActionShowAveragePyramid"
        sqlite_client.insert_or_ignore_pyramid(user_id, end_date)
        result = sqlite_client.get_avg_pyramid(user_id, start_date, end_date)

        image_path = pyramid_creator.generate_pyramid_image(result)
        image_url = s3_client.upload_image_to_s3(image_path, user_id)

        start_date = start_date.strftime('%d.%m.%Y')
        end_date = end_date.strftime('%d.%m.%Y')

        dispatcher.utter_message(
            "Hey, ich habe hier deinen Wochen-Überblick vom %s bis zum %s. Deine nächste "
            "Zusammenfassung wirst du in einer Woche erhalten." % (str(start_date), str(end_date)), image=image_url)

        return []


# this action is being called when the scheduler triggered the rule and sends the user the pyramid for the last 7 days
class ActionEveningCheckIn(Action):
    def name(self) -> Text:
        return "action_evening_check_in"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # getting primary keys used in the database, default date is today
        user_id = tracker.sender_id
        date = datetime.date.today()

        # insert the pyramid if missing, so user get a empty pyramid if they have not tracked any portions yet
        sqlite_client.insert_or_ignore_pyramid(user_id, date)

        # fetch the users pyramid for today
        result = sqlite_client.get_pyramid(user_id, date)

        # generate image for the pyramid
        image_path = pyramid_creator.generate_pyramid_image(result)

        # upload image to AWS S3 and retrieve URL
        image_url = s3_client.upload_image_to_s3(image_path, user_id)

        # respond to the user and send the generated imageURL to show the image of the user's pyramid
        dispatcher.utter_message("Guten Abend! Ich hoffe du hattest einen schönen Tag. Ich habe hier deine bisherige "
                                 "Pyramide für heute. Falls du vergessen hast etwas einzutragen, ist jetzt der "
                                 "richtige Zeitpunkt das nachzuholen. Ansonsten schau einfach welche Felder noch frei "
                                 "sind und koche dir ein leckeres Abendessen!", image=image_url)

        return []


# this action inserts the score to a check-in question into the database
class ActionSaveCheckIn(Action):
    def name(self) -> Text:
        return "action_save_check_in"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # getting user data
        user_id = tracker.sender_id
        date = datetime.date.today()

        # getting intent from the tracker (i.e. the payload of the button in the domain file)
        intent = tracker.get_intent_of_latest_message()

        # the intent looks like this (naming convention): BUTTON_morning_check_in_1
        title, score = intent_splitter.process(intent)

        # inserting the result into the database
        sqlite_client.insert_or_update_reflection(user_id, date, title, score)

        # sending the user utterances based on their self assessment, depending on question and score
        # score: 1 = very bad, 2 = bad, 3 = unsure, 4 = good, 5 = very good (5-point Likert scale)
        if title == "morning_check_in":
            if score <= 3:
                dispatcher.utter_message(response="utter_morning_cheer_up")
            else:
                dispatcher.utter_message(response="utter_morning_motivation")
        elif title == "evening_check_in":
            if score <= 3:
                dispatcher.utter_message(response="utter_evening_cheer_up")
            else:
                dispatcher.utter_message(response="utter_evening_motivation")
        elif title == "weekly_check_in":
            if score <= 3:
                dispatcher.utter_message(response="utter_weekly_cheer_up")
            else:
                dispatcher.utter_message(response="utter_weekly_motivation")
        return []
