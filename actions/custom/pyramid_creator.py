# In with this file the pyramid of a user is visualized. On a grey pyramid for each tracked field, the icon is
# being inserted. So a fully tracked pyramid is colorful. For each portion tracked more than intended a red cross
# will be drawn next to the group of corresponding fields.
# The image of the nutrition pyramid was retrieved from:
# https://www.bzfe.de/ernaehrung/die-ernaehrungspyramide/die-ernaehrungspyramide-eine-fuer-alle/

import sqlite3
from PIL import Image  # https://pillow.readthedocs.io/en/stable/
from typing import List, Tuple
import logging
from . import enums

# create logger
logger = logging.getLogger('custom.pyramid_creator')

# here the coordinates for top left corner of the icons of the different groups are defined.
# in the second line the positions for portions eaten more than the initial pyramid handles are being stored
water_positions = [(80, 206), (120, 206), (160, 206), (201, 206), (242, 206), (282, 206),
                   (182, 248), (142, 248), (223, 248), (102, 248), (263, 248), (62, 248), (303, 248)]

fruits_positions = [(100, 173), (141, 173),
                    (45, 173), (5, 173)]

vegetables_positions = [(182, 173), (223, 173), (263, 173),
                        (318, 173), (358, 173)]

carbohydrates_positions = [(120, 139), (161, 139), (243, 139),
                           (65, 139), (298, 139), (25, 139), (338, 139)]

carbohydrates_special_positions = [(202, 139)]  # there is one icon with an additional potato

milk_products_positions = [(138, 106), (170, 106), (202, 106),
                           (91, 106), (58, 106)]

meat_positions = [(234, 106),
                  (281, 106), (314, 106)]

oil_positions = [(162, 73),
                 (107, 73), (67, 73)]

fat_positions = [(202, 73),
                 (257, 73), (297, 73)]

extras_positions = [(182, 40),
                    (127, 40), (237, 40), (87, 40), (277, 40)]

# reading in the base image (black and white pyramid)
base_image = Image.open("./actions/custom/images/pyramid_no_colors.png")

# reading in all the icons
water_icon = Image.open("./actions/custom/images/water.png")
fruits_icon = Image.open("./actions/custom/images/fruits.png")
vegetables_icon = Image.open("./actions/custom/images/vegetables.png")
carbohydrates_icon = Image.open("./actions/custom/images/carbohydrates.png")
carbohydrates_special_icon = Image.open("./actions/custom/images/carbohydrates_special.png")
milk_products_icon = Image.open("./actions/custom/images/milk_products.png")
meat_icon = Image.open("./actions/custom/images/meat.png")
oil_icon = Image.open("./actions/custom/images/oil.png")
fat_icon = Image.open("./actions/custom/images/fat.png")
extras_icon = Image.open("./actions/custom/images/extras.png")


def __paste_icons_in_base_image(number: int, image, icon, position_list: List[Tuple[int, int]]):
    # number has to be greater than 0, otherwise no portions have been tracked
    if number <= 0:
        return

    index = 0

    # paste the given number of icons on incrementing positions as long as the index is in bound of the list and
    # smaller than the number passed
    while index < len(position_list) and index < number:
        if 0 < (number - index) < 1:
            # if the number has decimals, the percentage of the width (38px) is being used to display portions partly
            width = 38 * (number - index)
            image.paste(icon.crop((0, 0, width, 31)), position_list[index])

            # this can only be the case in the last iteration e.g. index = 3, number = 3.5
            return
        else:
            # paste icon in base image to colorize the field
            image.paste(icon, position_list[index])
            index = index + 1


def generate_pyramid_image(pyramid: sqlite3.Row) -> str:
    logger.info("Creating pyramid image")

    # create copy of base image to paste icons into otherwise the base image itself would be modified
    copy = base_image.copy()

    # iterating over all keys in the row (i.e the columns of raina.db)
    user_id = ""
    for field in pyramid.keys():
        value = pyramid[field]
        if field == "user_id":
            # saving the userId for the image name
            user_id = value
        elif field == enums.FoodTypes.WATER.value:
            __paste_icons_in_base_image(value, copy, water_icon, water_positions)
        elif field == enums.FoodTypes.FRUITS.value:
            __paste_icons_in_base_image(value, copy, fruits_icon, fruits_positions)
        elif field == enums.FoodTypes.VEGETABLES.value:
            __paste_icons_in_base_image(value, copy, vegetables_icon, vegetables_positions)
        elif field == enums.FoodTypes.CARBOHYDRATES.value:
            # depending on how high the value is, the third carbohydrate icon (special) will be used
            if value <= 2:
                # use only the normal icons twice
                __paste_icons_in_base_image(value, copy, carbohydrates_icon, carbohydrates_positions)
            if 2 < value < 3:
                # use the two normal icons
                __paste_icons_in_base_image(2, copy, carbohydrates_icon, carbohydrates_positions)
                # ad a percentage of the special icon
                __paste_icons_in_base_image(value-2, copy, carbohydrates_special_icon, carbohydrates_special_positions)
            if value >= 3:
                # paste values-1 normal carbohydrate icons
                __paste_icons_in_base_image(value - 1, copy, carbohydrates_icon, carbohydrates_positions)
                # add the special one extra
                __paste_icons_in_base_image(1, copy, carbohydrates_special_icon, carbohydrates_special_positions)
        elif field == enums.FoodTypes.MILK_PRODUCTS.value:
            __paste_icons_in_base_image(value, copy, milk_products_icon, milk_products_positions)
        elif field == enums.FoodTypes.MEAT.value:
            __paste_icons_in_base_image(value, copy, meat_icon, meat_positions)
        elif field == enums.FoodTypes.OIL.value:
            __paste_icons_in_base_image(value, copy, oil_icon, oil_positions)
        elif field == enums.FoodTypes.FAT.value:
            __paste_icons_in_base_image(value, copy, fat_icon, fat_positions)
        elif field == enums.FoodTypes.EXTRAS.value:
            __paste_icons_in_base_image(value, copy, extras_icon, extras_positions)

    # check if the user_id has been assigned
    if user_id != "":
        # save the image as <userId>.png, so that the number of images is limited to the number of users
        image_path = f"./actions/custom/images/backlog/%s.png" % user_id
    else:
        # empty pyramid to be displayed if no userId has been passed
        image_path = "./actions/custom/images/pyramid_no_colors.png"

    # save the generated image and return the path to be used
    logger.info("Saving image")
    copy.save(image_path)
    return image_path
