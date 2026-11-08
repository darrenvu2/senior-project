import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "https://api.nal.usda.gov/fdc/v1"
API_KEY = os.environ.get("FDC_API_KEY", "DEMO_KEY")
OUTPUT_DIR = Path(__file__).resolve().parent / "meals"
DATA_TYPES = ["Foundation", "SR Legacy", "Survey (FNDDS)"]
NUTRIENT_IDS = {
    1003: ("protein_g", "g"),
    1004: ("fat_g", "g"),
    1005: ("carbohydrate_g", "g"),
    1079: ("fiber_g", "g"),
    1093: ("sodium_mg", "mg"),
    2000: ("total_sugars_g", "g"),
    1235: ("added_sugars_g", "g"),
    1258: ("saturated_fat_g", "g"),
    1008: ("calories", "kcal"),
    2047: ("calories", "kcal"),
    2048: ("calories", "kcal"),
}
ENERGY_PRIORITY = {2047: 3, 1008: 2, 2048: 1}


def api_request(path, payload=None):
    url = f"{BASE_URL}{path}?{urllib.parse.urlencode({'api_key': API_KEY})}"
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json", "User-Agent": "AI-Nutrition-Coach-Student-Prototype/1.0"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read(500).decode("utf-8", errors="replace")
        raise RuntimeError(f"USDA HTTP {error.code}: {detail}") from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise RuntimeError(f"USDA connection failed: {error}") from error


def search_foods(query):
    result = api_request("/foods/search", {"query": query, "pageSize": 12, "dataType": DATA_TYPES})
    return result.get("foods", [])


def food_details(fdc_id):
    return api_request(f"/food/{int(fdc_id)}")


def nutrient_values_per_100g(food):
    """For Foundation, SR Legacy, Survey (FNDDS) detailed records only.

    The nutrient 'amount' in these food types is conventionally per 100 g.
    Missing nutrient values remain missing (not zero).
    """
    if food.get("dataType") not in DATA_TYPES:
        raise ValueError("Unsupported USDA data type; per-100g basis not verified")
    result = {}
    best_energy = 0
    for item in food.get("foodNutrients", []):
        nutrient = item.get("nutrient") or {}
        nutrient_id = nutrient.get("id", item.get("nutrientId"))
        if nutrient_id not in NUTRIENT_IDS:
            continue
        value = item.get("amount", item.get("value"))
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        key, unit = NUTRIENT_IDS[nutrient_id]
        actual_unit = str(nutrient.get("unitName", "")).lower()
        if actual_unit and actual_unit != unit.lower():
            continue
        if key == "calories":
            rank = ENERGY_PRIORITY[nutrient_id]
            if rank <= best_energy:
                continue
            best_energy = rank
        result[key] = float(value)
    return result


def portion_options(food):
    """Keep USDA portions only when labels are readable; never decode numeric codes by guessing."""
    options = [{"label": "100 g", "grams": 100.0, "source": "fixed_grams"},
               {"label": "200 g", "grams": 200.0, "source": "fixed_grams"}]
    seen = set()
    for portion in food.get("foodPortions") or []:
        grams = portion.get("gramWeight")
        if not isinstance(grams, (int, float)) or grams <= 0:
            continue
        measure = portion.get("measureUnit") or {}
        unit = str(measure.get("name", "")).strip() if isinstance(measure, dict) else ""
        modifier = str(portion.get("modifier") or "").strip()
        amount = portion.get("amount")
        # FNDDS sometimes returns numeric unit codes, not descriptions.
        if unit.isdigit():
            unit = ""
        if modifier.isdigit():
            modifier = ""
        parts = []
        if amount is not None and (unit or modifier):
            parts.append(f"{amount:g}" if isinstance(amount, (int, float)) else str(amount))
        if unit:
            parts.append(unit)
        if modifier and modifier.lower() not in unit.lower():
            parts.append(modifier)
        label = " ".join(parts).strip()
        if not label:
            # No trustworthy household description; weight remains selectable.
            label = f"USDA portion ({grams:g} g; household unit unspecified)"
        key = (label.lower(), round(float(grams), 3))
        if key not in seen:
            options.append({"label": label, "grams": float(grams), "source": "USDA foodPortions"})
            seen.add(key)
    options.append({"label": "Enter custom grams", "grams": None, "source": "user_input"})
    return options


def calculate_nutrients(per_100g, grams):
    if not isinstance(grams, (int, float)) or not 0 < grams <= 10000:
        raise ValueError("Portion must be between 0 and 10000 grams")
    return {name: round(value * grams / 100.0, 2) for name, value in per_100g.items()}


def make_food_entry(food, grams, portion_label, method="manual_selection"):
    return {
        "fdcId": food.get("fdcId"),
        "foodName": food.get("description"),
        "dataType": food.get("dataType"),
        "source": "USDA FoodData Central",
        "portion": {"label": portion_label, "estimatedGrams": round(grams, 2), "method": method},
        "nutrientBasis": {"amount": round(grams, 2), "unit": "g", "description": "selected portion"},
        "nutrients": calculate_nutrients(nutrient_values_per_100g(food), grams),
    }


def build_meal(entries, demo=False):
    if not entries:
        raise ValueError("A meal must have at least one food")
    keys = set(NUTRIENT_IDS[id][0] for id in NUTRIENT_IDS)
    keys.update(*(item["nutrients"].keys() for item in entries))
    totals = {}
    incomplete = []
    for key in sorted(keys):
        if all(key in item["nutrients"] for item in entries):
            totals[key] = round(sum(item["nutrients"][key] for item in entries), 2)
        else:
            totals[key] = None
            incomplete.append(key)
    return {
        "mealId": "meal_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f"),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "mode": "illustrative_demo" if demo else "usda_live",
        "foods": entries,
        "mealTotals": totals,
        "incompleteTotals": incomplete
        
    }


def save_meal(meal):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = OUTPUT_DIR / (meal["mealId"] + ("_demo" if meal["mode"] == "illustrative_demo" else "") + ".json")
    filename.write_text(json.dumps(meal, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return filename


def choose_number(maximum, prompt):
    while True:
        answer = input(prompt).strip()
        if answer.lower() in ("q", "quit"):
            return None
        if answer.isdigit() and 1 <= int(answer) <= maximum:
            return int(answer) - 1
        print(f"Enter 1–{maximum}, or q to quit.")


def choose_portion(food):
    options = portion_options(food)
    print("\nAvailable portions:")
    for i, option in enumerate(options, 1):
        suffix = "" if option["grams"] is None else f" — {option['grams']:g} g"
        print(f"  {i}. {option['label']}{suffix if not option['label'].endswith('g') else ''}")
    choice = choose_number(len(options), "Select portion number: ")
    if choice is None:
        return None
    option = options[choice]
    if option["grams"] is None:
        while True:
            try:
                grams = float(input("Estimated grams (e.g., 85): ").strip())
                if 0 < grams <= 10000:
                    return grams, f"Custom: {grams:g} g", "user_estimate"
            except ValueError:
                pass
            print("Please enter a positive weight up to 10000 g.")
    return option["grams"], option["label"], "usda_portion" if option["source"] == "USDA foodPortions" else "manual_grams"


def print_meal(meal):
    print("\n=== MEAL NUTRITION ===")
    for item in meal["foods"]:
        print(f"\n{item['foodName']} | {item['portion']['estimatedGrams']:g} g | FDC {item['fdcId']}")
        for key, value in item["nutrients"].items():
            print(f"  {key}: {value}")
    print("\n=== MEAL TOTALS ===")
    for key, value in meal["mealTotals"].items():
        print(f"  {key}: {value if value is not None else 'unknown (missing for some foods)'}")


def run_interactive():
    print("AI Nutrition Coach | USDA Food Database")
    print("Search foods, select portions, and calculate meal nutrition.")
    entries = []
    while True:
        query = input("\nEnter food name (or 'done' to finish): ").strip()
        if query.lower() in ("done", "q", "quit"):
            break
        if not query:
            continue
        try:
            results = search_foods(query)
            if not results:
                print("No matching foods. Try a more specific name.")
                continue
            for i, food in enumerate(results, 1):
                print(f"  {i}. {food.get('description')} [{food.get('dataType')}] (FDC {food.get('fdcId')})")
            choice = choose_number(len(results), "Choose food number: ")
            if choice is None:
                continue
            food = food_details(results[choice]["fdcId"])
            portion = choose_portion(food)
            if portion is None:
                continue
            grams, label, method = portion
            entry = make_food_entry(food, grams, label, method)
            if not entry["nutrients"]:
                print("No supported nutrient data found for this food. Try another entry.")
                continue
            entries.append(entry)
            print(f"Added {entry['foodName']} ({grams:g} g). Foods in meal: {len(entries)}")
        except (RuntimeError, ValueError, KeyError) as error:
            print(f"Could not add food: {error}")
    if entries:
        meal = build_meal(entries)
        print_meal(meal)
        print(f"\nSaved JSON: {save_meal(meal)}")
    else:
        print("No foods added; no file saved.")

DEMO_FOODS = [
    ("Salmon, cooked (ILLUSTRATIVE)", 85, {"calories": 206, "protein_g": 22, "fat_g": 12, "carbohydrate_g": 0}),
    ("Broccoli, cooked (ILLUSTRATIVE)", 100, {"calories": 35, "protein_g": 2.4, "fat_g": 0.4, "carbohydrate_g": 7}),
    ("Rice, white, cooked (ILLUSTRATIVE)", 150, {"calories": 130, "protein_g": 2.7, "fat_g": 0.3, "carbohydrate_g": 28}),
]


def run_demo():
    entries = []
    for name, grams, values in DEMO_FOODS:
        entries.append({
            "fdcId": None, "foodName": name, "dataType": "synthetic_example",
            "source": "ILLUSTRATIVE VALUES — NOT VERIFIED USDA",
            "portion": {"label": f"Example {grams} g", "estimatedGrams": grams, "method": "example"},
            "nutrientBasis": {"amount": grams, "unit": "g", "description": "selected portion"},
            "nutrients": calculate_nutrients(values, grams),
        })
    meal = build_meal(entries, demo=True)
    print("DEMO MODE — EXAMPLE VALUES, NOT VERIFIED USDA DATA")
    print_meal(meal)
    print(f"\nSaved JSON: {save_meal(meal)}")


def run_tests():
    assert calculate_nutrients({"calories": 200, "protein_g": 20}, 85) == {"calories": 170.0, "protein_g": 17.0}
    f = {"dataType": "Foundation", "foodNutrients": [
        {"nutrient": {"id": 1003, "unitName": "g"}, "amount": 20},
        {"nutrient": {"id": 2047, "unitName": "kcal"}, "amount": 110},
        {"nutrient": {"id": 1008, "unitName": "kcal"}, "amount": 120},
    ]}
    assert nutrient_values_per_100g(f) == {"protein_g": 20.0, "calories": 110.0}
    a = {"nutrients": {"calories": 50, "protein_g": 3}}
    b = {"nutrients": {"calories": 70}}
    assert build_meal([a, b])["mealTotals"]["calories"] == 120
    assert build_meal([a, b])["mealTotals"]["protein_g"] is None
    assert build_meal([a, b])["mealTotals"]["fiber_g"] is None
    assert "household unit unspecified" in portion_options({"foodPortions": [{"gramWeight": 85, "measureUnit": {"name": "90000"}}]})[2]["label"]
    assert make_food_entry({"fdcId": 1, "description": "Test", "dataType": "Foundation", "foodNutrients": []}, 110, "110 g")["nutrientBasis"]["amount"] == 110
    print("All tests passed.")


def main():
    parser = argparse.ArgumentParser(description="USDA food database and meal nutrition prototype")
    parser.add_argument("--demo", action="store_true", help="offline demo with clearly labeled illustrative values")
    parser.add_argument("--test", action="store_true", help="run offline unit tests")
    args = parser.parse_args()
    if args.test:
        run_tests()
    elif args.demo:
        run_demo()
    else:
        try:
            run_interactive()
        except (KeyboardInterrupt, EOFError):
            print("\nStopped.")


if __name__ == "__main__":
    main()
