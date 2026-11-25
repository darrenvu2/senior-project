
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .food_api_v2 import (
    search_foods,
    food_details,
    nutrient_values_per_100g,
    get_fndds_food_code,
)
from .fped_lookup import calculate_fped_portion
from src.hei_scoring import calculate_hei_2020

app = FastAPI(title="AI Nutrition Coach API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8081",
        "http://127.0.0.1:8081",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "AI Nutrition Coach API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/foods/search")
def search_food(query: str):
    try:
        foods = search_foods(query)
        return {"query": query, "results": foods}
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error))


@app.get("/foods/{fdc_id}")
def get_food(fdc_id: int):
    try:
        food = food_details(fdc_id)
        nutrients = nutrient_values_per_100g(food)

        return {
            "fdcId": food.get("fdcId"),
            "foodName": food.get("description"),
            "dataType": food.get("dataType"),
            "nutrientsPer100g": nutrients,
            "source": "USDA FoodData Central",
        }
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error))

from fastapi import Query


@app.get("/foods/{fdc_id}/portion")
def get_food_portion(
    fdc_id: int,
    grams: float = Query(default=100, gt=0, le=10000),
):
    try:
        food = food_details(fdc_id)
        nutrients = nutrient_values_per_100g(food)

        portion_nutrients = {
            key: round(value * grams / 100, 2)
            for key, value in nutrients.items()
            if isinstance(value, (int, float))
        }

        return {
            "fdcId": food.get("fdcId"),
            "foodName": food.get("description"),
            "selectedPortion": {
                "grams": grams,
                "description": f"{grams:g} g",
            },
            "portionNutrients": portion_nutrients,
            "source": "USDA FoodData Central",
        }

    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error))
from pydantic import BaseModel, Field
from fastapi import status

# Temporary meal storage for the proof of concept
meals = {}
next_meal_id = 1


class MealInput(BaseModel):
    fdcId: int
    foodName: str
    grams: float = Field(gt=0, le=10000)


@app.post("/meals", status_code=status.HTTP_201_CREATED)
def create_meal(meal: MealInput):
    global next_meal_id

    meal_id = next_meal_id
    next_meal_id += 1

    saved_meal = {
        "mealId": meal_id,
        **meal.model_dump()
    }

    meals[meal_id] = saved_meal
    return saved_meal


@app.get("/meals")
def get_meals():
    return {"meals": list(meals.values())}


@app.put("/meals/{meal_id}")
def update_meal(meal_id: int, meal: MealInput):
    if meal_id not in meals:
        raise HTTPException(
            status_code=404,
            detail="Meal not found"
        )

    updated_meal = {
        "mealId": meal_id,
        **meal.model_dump()
    }

    meals[meal_id] = updated_meal
    return updated_meal


@app.delete("/meals/{meal_id}")
def delete_meal(meal_id: int):
    if meal_id not in meals:
        raise HTTPException(
            status_code=404,
            detail="Meal not found"
        )

    del meals[meal_id]

    return {"message": "Meal deleted successfully"}

@app.get("/fped/{food_code}/portion")
def get_fped_portion(food_code: int, grams: float = 100):
    if grams <= 0:
        raise HTTPException(
            status_code=400,
            detail="Grams must be greater than zero"
        )

    result = calculate_fped_portion(food_code, grams)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Food code not found in FPED"
        )

    return result

@app.get("/foods/{fdc_id}/analysis")
def analyze_food(fdc_id: int, grams: float = 100):
    if grams <= 0:
        raise HTTPException(
            status_code=400,
            detail="Grams must be greater than zero"
        )

    try:
        food = food_details(fdc_id)
        nutrients = nutrient_values_per_100g(food)
        factor = grams / 100

        scaled_nutrients = {
            key: value * factor if value is not None else None
            for key, value in nutrients.items()
        }

        food_code = get_fndds_food_code(food)
        fped = (
            calculate_fped_portion(food_code, grams)
            if food_code is not None
            else None
        )

        return {
            "fdcId": fdc_id,
            "foodName": food.get("description"),
            "dataType": food.get("dataType"),
            "grams": grams,
            "nutrients": scaled_nutrients,
            "fnddsFoodCode": food_code,
            "fped": fped,
            "fpedMatched": fped is not None,
            "fpedRelease": "2021-2023",
            "heiInputStatus": (
                "pending_release_verification"
                if fped is not None
                else "missing_fped_match"
            ),
        }

    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=502, detail=str(error))

@app.post("/hei/score")
def score_hei(data: dict):
    try:
        return calculate_hei_2020(data)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )
@app.post("/hei/analyze-meal")
def analyze_meal_for_hei(items: list[MealInput]):
    if not items:
        raise HTTPException(
            status_code=400,
            detail="At least one food is required"
        )

    results = []
    missing_fped = []

    for item in items:
        try:
            food = food_details(item.fdcId)
            nutrients = nutrient_values_per_100g(food)

            factor = item.grams / 100

            scaled_nutrients = {
                key: round(value * factor, 2)
                if isinstance(value, (int, float))
                else None
                for key, value in nutrients.items()
            }

            food_code = get_fndds_food_code(food)

            fped = (
                calculate_fped_portion(
                    food_code,
                    item.grams
                )
                if food_code is not None
                else None
            )

            if fped is None:
                missing_fped.append(item.fdcId)

            results.append({
                "fdcId": item.fdcId,
                "foodName": food.get("description"),
                "grams": item.grams,
                "nutrients": scaled_nutrients,
                "fnddsFoodCode": food_code,
                "fped": fped,
                "fpedMatched": fped is not None,
            })

        except (ValueError, RuntimeError) as error:
            raise HTTPException(
                status_code=502,
                detail=str(error)
            )

    return {
        "foods": results,
        "foodCount": len(results),
        "fpedMatched": len(missing_fped) == 0,
        "missingFpedIds": missing_fped,
        "heiScore": None,
        "status": "requires_verified_hei_inputs",
        "message": (
            "Food analysis completed. Verify FPED release "
            "compatibility, required nutrient values, and "
            "HEI food-group allocation before scoring."
        ),
    }