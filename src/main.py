
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .food_api_v2 import (
    search_foods,
    food_details,
    nutrient_values_per_100g,
)

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

