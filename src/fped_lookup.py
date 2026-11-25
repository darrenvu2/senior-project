
from pathlib import Path
import xlrd

FPED_PATH = Path(__file__).resolve().parent.parent / "data" / "fped" / "FPED_2123.xls"


def get_fped_food(food_code):
    workbook = xlrd.open_workbook(str(FPED_PATH))
    sheet = workbook.sheet_by_name("FPED_2123")

    headers = sheet.row_values(0)

    for row_index in range(1, sheet.nrows):
        row = sheet.row_values(row_index)

        if str(row[0]).split(".")[0] == str(food_code):
            return dict(zip(headers, row))

    return None

def calculate_fped_portion(food_code, grams):
    if grams <= 0:
        raise ValueError("Portion must be greater than zero")

    food = get_fped_food(food_code)

    if food is None:
        return None

    factor = grams / 100

    result = {
        "foodCode": food_code,
        "description": food["DESCRIPTION"],
        "grams": grams,
        "fpedValues": {}
    }

    for key, value in food.items():
        if key not in ("FOODCODE", "DESCRIPTION", "NO_COMPONENTS"):
            if isinstance(value, (int, float)):
                result["fpedValues"][key] = value * factor

    return result
if __name__ == "__main__":
    food = get_fped_food(11111000)

    if food is None:
        print("Food not found")
    else:
        print("FPED column names:")
        for key in food:
            print(key)