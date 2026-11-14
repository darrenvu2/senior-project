
from fastapi import FastAPI, HTTPException
from .food_api_v2 import (
    search_foods,
    food_details,
    nutrient_values_per_100g,
)

app = FastAPI(title="AI Nutrition Coach API")


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

