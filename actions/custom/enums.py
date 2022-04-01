from enum import Enum


class FoodTypes(Enum):
    """
    This class provides enums for the different types of food used in the nutrition pyramid, mapped to the columns of
    the pyramid tables in the db. This is being used to secure the string substitution in the SQLite queries.
    """
    WATER = "water"
    FRUITS = "fruits"
    VEGETABLES = "vegetables"
    CARBOHYDRATES = "carbohydrates"
    MILK_PRODUCTS = "milk_products"
    MEAT = "meat"
    OIL = "oil"
    FAT = "fat"
    EXTRAS = "extras"
    UNKNOWN = "unknown"


def get_field_from_entity(entity: str) -> FoodTypes:
    """
    This method maps the given entity in the conversation to a field of the nutrition pyramid used in the database.

    :param entity: entity extracted from the last message
    :return: enum of the column name in the pyramid table
    """
    if entity == "Getränke":
        return FoodTypes.WATER
    elif entity == "Gemüse":
        return FoodTypes.VEGETABLES
    elif entity == "Obst":
        return FoodTypes.FRUITS
    elif entity == "Kohlenhydrate":
        return FoodTypes.CARBOHYDRATES
    elif entity == "Milchprodukte":
        return FoodTypes.MILK_PRODUCTS
    elif entity == "Fleisch":
        return FoodTypes.MEAT
    elif entity == "Fett":
        return FoodTypes.FAT
    elif entity == "Öl":
        return FoodTypes.OIL
    elif entity == "Extras":
        return FoodTypes.EXTRAS
    else:
        return FoodTypes.UNKNOWN
