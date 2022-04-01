# In this file all function performing custom checks are specified, so that the action.py file remains readable with as
# little business logic as possible.
import datetime
from actions.custom import enums, sqlite_client

# in this dict the max values of fields which can be displayed are stored for the different types
max_portions = {
    enums.FoodTypes.WATER.value: 13,
    enums.FoodTypes.FRUITS.value: 4,
    enums.FoodTypes.VEGETABLES.value: 5,
    enums.FoodTypes.CARBOHYDRATES.value: 8,
    enums.FoodTypes.MILK_PRODUCTS.value: 5,
    enums.FoodTypes.MEAT.value: 3,
    enums.FoodTypes.OIL.value: 3,
    enums.FoodTypes.FAT.value: 3,
    enums.FoodTypes.EXTRAS.value: 5
}

# in this dict the recommended amount of portions in the pyramid are stored
recommended_portions = {
    enums.FoodTypes.WATER.value: 6,
    enums.FoodTypes.FRUITS.value: 2,
    enums.FoodTypes.VEGETABLES.value: 3,
    enums.FoodTypes.CARBOHYDRATES.value: 4,
    enums.FoodTypes.MILK_PRODUCTS.value: 3,
    enums.FoodTypes.MEAT.value: 1,
    enums.FoodTypes.OIL.value: 1,
    enums.FoodTypes.FAT.value: 1,
    enums.FoodTypes.EXTRAS.value: 1
}


# Security measure to prevent users from inserting huge amounts of portions, which are not realistic.
def is_valid_for_increment(user_id: str, date: datetime, field: enums.FoodTypes, number_of_portions: float) -> bool:
    """
    This method checks if the given field is valid for being incremented by comparing it to the max value specified.

    :param user_id: the user_id of the user the field should be checked
    :param date: the date of the users pyramid
    :param field: the field to be checked in the pyramid
    :param number_of_portions: the amount of portions to be added intended by the user
    :return: true if the field can be incremented, false otherwise
    """

    # get pyramid for user and date
    pyramid = sqlite_client.get_pyramid(user_id, date)

    # check field and return result
    return (pyramid[field.value] + number_of_portions) <= max_portions[field.value]


# Security measure to prevent users from tracking a negative amount of portions
def is_valid_for_decrement(user_id: str, date: datetime, field: enums.FoodTypes, number_of_portions: float) -> bool:
    """
    This method checks if the given field is valid for being decremented by verifying it is greater than 0.

    :param user_id: the user_id of the user the field should be checked
    :param date: the date of the users pyramid
    :param field: the field to be checked in the pyramid
    :param number_of_portions: the amount of portions to be subtracted intended by the user
    :return: true if the field can be incremented, false otherwise
    """

    # get pyramid for user and date
    pyramid = sqlite_client.get_pyramid(user_id, date)

    # check field and return result
    return (pyramid[field.value] - number_of_portions) >= 0
