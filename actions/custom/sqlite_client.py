import datetime
import sqlite3
import logging
from typing import Optional, List
from actions.custom import enums

# create logger
logger = logging.getLogger('custom.sqlite_client')

# In this file all functions to interact with raina.db are specified. The business logic like custom checks before
# incrementing/decrementing a field in a column are done in the class modeling a custom action, which is calling those
# functions (those are defined in actions.py)


def __connect():
    """
    This function connects to the raina.db file and creates it if it does not exist
    """
    connection = sqlite3.connect('./actions/db/raina.db')

    # set the row factory of the connection to Row, to be able to use keys to access a specific column
    # https://docs.python.org/3/library/sqlite3.html#sqlite3.Row
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()
    return connection, cursor


def __disconnect(connection: sqlite3.Connection, cursor: sqlite3.Cursor):
    """
    This function commits the changes made in the given connection, closes the cursor and disconnects from raina.db.

    :param cursor: cursor to be closed
    :param connection: connection to be closed
    """
    connection.commit()
    cursor.close()
    connection.close()


def create_pyramid_table():
    """
    This function creates a new table to save fields of nutrition pyramid
    """
    connection, cursor = __connect()

    # create table
    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS pyramid (
                        user_id TEXT NOT NULL,
                        date DATETIME DEFAULT current_date,
                        water INTEGER DEFAULT 0,
                        fruits INTEGER DEFAULT 0,
                        vegetables INTEGER DEFAULT 0,
                        carbohydrates INTEGER DEFAULT 0,
                        milk_products INTEGER DEFAULT 0,
                        meat INTEGER DEFAULT 0,
                        oil INTEGER DEFAULT 0,
                        fat INTEGER DEFAULT 0,
                        extras INTEGER DEFAULT 0,
                         PRIMARY KEY (user_id, date)
                    )''')

    __disconnect(connection, cursor)


def create_user_table():
    """
    This function creates a new table to save all user_ids and the date they joined at. This is being used by the
    scheduler to send checkIn messages to EVERY user.
    """
    connection, cursor = __connect()

    # create table
    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user (
                        user_id TEXT NOT NULL,
                        created_at DATETIME DEFAULT current_date,
                        PRIMARY KEY (user_id)
                    )''')

    __disconnect(connection, cursor)


def create_reflection_table():
    """
    This function creates a new table to save information on the ckeckIn questions. Those questions are designed
    to be answered on a scale from 1: bad to 5: really good. The answer is stored as integer to enable better analysis.
    """
    connection, cursor = __connect()

    # create table
    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS reflection (
                        user_id TEXT NOT NULL,
                        date DATETIME DEFAULT current_date,
                        title TEXT NOT NULL,
                        score INTEGER NOT NULL,
                        PRIMARY KEY (user_id, date, title)
                    )''')

    __disconnect(connection, cursor)


def insert_or_ignore_pyramid(user_id: str, date: datetime):
    """
    This function inserts a new empty pyramid for the given user, if it does not exist already

    :param user_id: equals senderId of the rasa conversation
    :param date: the date for which the pyramid should be created
    """
    connection, cursor = __connect()

    # insert new row
    cursor.execute('''
                    INSERT OR IGNORE INTO pyramid (user_id, date)
                        VALUES (:user_id, :date)''',
                   {'user_id': user_id, 'date': date})

    __disconnect(connection, cursor)


def get_pyramid(user_id: str, date: datetime) -> Optional[sqlite3.Row]:
    """
    This function looks up the pyramid for a user on the given day

    :param user_id: equals tracker.senderId of the rasa conversation
    :param date: date on which the pyramid was created
    :return: pyramid as sqlite3.Row if it exists, none otherwise (use "tuple(pyramid)" to get is as tuple)
    """
    connection, cursor = __connect()

    # fetch pyramid
    cursor.execute('''SELECT * 
                        FROM pyramid p
                        WHERE p.user_id = :user_id
                            AND p.date = :date''',
                   {'user_id': user_id, 'date': date})
    pyramid = cursor.fetchone()
    return pyramid


def add_portion(user_id: str, date: datetime, food_type: enums.FoodTypes, number_of_portions: float):
    """
    This function adds one portion of the given food type (e.g. treats) to the user's pyramid. Since the food_type is
    used as string parameter in the query it has to be exactly the name of a column thus an enum is being used.

    :param user_id: equals senderId of the rasa conversation
    :param date: date on which the pyramid was created
    :param food_type: a field of the nutrition pyramid, specified as enums in enums.py
    :param number_of_portions: float number of portions to be added to the column
    """
    connection, cursor = __connect()

    # add portion to given field, using the food type as string parameter in the query
    # user_id and date are used as normal query parameters
    cursor.execute('''UPDATE pyramid
                        SET %s = %s + :number_of_portions
                        WHERE user_id = :user_id
                            AND date = :date''' % (food_type.value, food_type.value),
                   {'user_id': user_id, 'date': date, 'number_of_portions': number_of_portions})

    __disconnect(connection, cursor)


def remove_portion(user_id: str, date: datetime, food_type: enums.FoodTypes, number_of_portions: float):
    """
    This function adds one portion of the given food type (e.g. treats) to the user's pyramid. Since the food_type is used
    as string parameter in the query it has to be exactly the name of a column thus an enum is being used.

    :param user_id: equals senderId of the rasa conversation
    :param date: date on which the pyramid was created
    :param food_type: a field of the nutrition pyramid, specified as enums in enums.py
    :param number_of_portions: float number of portions to be added to the column
    """
    connection, cursor = __connect()

    # add portion to given field, using the food type as string parameter in the query
    # user_id and date are used as normal query parameters
    cursor.execute('''UPDATE pyramid 
                        SET %s = %s - :number_of_portions
                        WHERE user_id = :user_id
                            AND date = :date''' % (food_type.value, food_type.value),
                   {'user_id': user_id, 'date': date, 'number_of_portions': number_of_portions})

    __disconnect(connection, cursor)


def set_portion(user_id: str, date: datetime, food_type: enums.FoodTypes, number_of_portions: float):
    """
    This function sets the number of portions in the database to a specific value passed as parameter. This is being
    used for setting the portions to the maximum/zero if the user specifies and amount not in bounds when trying to
    add/remove portions.

    :param user_id: equals senderId of the rasa conversation
    :param date: date on which the pyramid was created
    :param food_type: a field of the nutrition pyramid, specified as enums in enums.py
    :param number_of_portions: float number of portions to be added to the column
    """
    connection, cursor = __connect()

    # set the amount of portions of the given field, using the food type as string parameter in the query
    # user_id and date are used as normal query parameters
    cursor.execute('''UPDATE pyramid 
                        SET %s = :number_of_portions
                        WHERE user_id = :user_id
                            AND date = :date''' % food_type.value,
                   {'user_id': user_id, 'date': date, 'number_of_portions': number_of_portions})

    __disconnect(connection, cursor)


def get_avg_pyramid(user_id: str, start_date: datetime, end_date: datetime) -> Optional[sqlite3.Row]:
    """
    This function calculates the average pyramid for a user in the given timeframe. Notice that only pyramids which have
    been fetched or have at least one entry are taken in consideration, since a pyramid is only being inserted when
    needed.

    :param user_id: equals senderId of the rasa conversation
    :param start_date: the start date of the time frame (included)
    :param end_date:  the end date of the time frame (included)
    :return: pyramid as sqlite3.Row if it exists, none otherwise (use "tuple(pyramid)" to get is as tuple). The pyramid
    contains the passed user_id and the end_date as date
    """
    connection, cursor = __connect()

    # get average pyramid for the given timeframe
    cursor.execute('''SELECT user_id,
                        max(date) as date,
                        avg(water) as water,
                        avg(fruits) as fruits,
                        avg(vegetables) as vegetables,
                        avg(carbohydrates) as carbohydrates,
                        avg(milk_products) as milk_products,
                        avg(meat) as meat,
                        avg(oil) as oil,
                        avg(fat) as fat,
                        avg(extras) as extras
                        FROM pyramid
                        WHERE user_id = :user_id
                          AND date >= :start_date
                          AND date <= :end_date
                        group by user_id''',
                   {'user_id': user_id, 'start_date': start_date, 'end_date': end_date})

    # return pyramid
    pyramid = cursor.fetchone()
    __disconnect(connection, cursor)
    return pyramid


def insert_or_ignore_user(user_id: str, date: datetime):
    """
    This function creates a new entry for a user in the database with the data of joining. This table is being used to
    fetch all user_ids in order to send scheduled messages to everyone.

    :param user_id: equals senderId of the rasa conversation
    :param date: the date the user joined at
    """

    connection, cursor = __connect()

    # insert new row
    cursor.execute('''
                        INSERT OR IGNORE INTO user (user_id, created_at)
                            VALUES (:user_id, :date)''',
                   {'user_id': user_id, 'date': date})

    __disconnect(connection, cursor)


def get_all_users() -> List[sqlite3.Row]:
    """
    This function fetches all user_ids from the users table.
    :return: a List filled with all user_ids, empty if no user was found
    """
    connection, cursor = __connect()

    # getting all user_id
    cursor.execute('''SELECT DISTINCT user_id
                        FROM user''')

    users_ids = cursor.fetchall()
    __disconnect(connection, cursor)
    return users_ids


def insert_or_update_reflection(user_id: str, date: datetime, title: str, score: int):
    """
    This function inserts a row into the reflection table, if a user answers the same question twice, the row will be
    updated.

    :param user_id: equals senderId of the rasa conversation
    :param date: the date the user answered the question
    :param title: the title of the question
    :param score: the score of the user's answers (1-5)
    """

    connection, cursor = __connect()

    cursor.execute('''
                        INSERT OR REPLACE INTO reflection (user_id, date, title, score)
                            VALUES (:user_id, :date, :title, :score)''',
                   {'user_id': user_id, 'date': date, 'title': title, 'score': score})

    __disconnect(connection, cursor)


# used to create the tables on startup, if they do not exist yet
logger.info("Creating table for storing user information")
create_user_table()

logger.info("Creating table for storing reflection data")
create_reflection_table()

logger.info("Creating table for storing users' pyramids")
create_pyramid_table()
