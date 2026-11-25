from math import isfinite


HEI_STANDARDS = {
    "total_fruits": {
        "type": "adequacy", "best": 0.8, "worst": 0.0, "max_points": 5
    },
    "whole_fruits": {
        "type": "adequacy", "best": 0.4, "worst": 0.0, "max_points": 5
    },
    "total_vegetables": {
        "type": "adequacy", "best": 1.1, "worst": 0.0, "max_points": 5
    },
    "greens_and_beans": {
        "type": "adequacy", "best": 0.2, "worst": 0.0, "max_points": 5
    },
    "whole_grains": {
        "type": "adequacy", "best": 1.5, "worst": 0.0, "max_points": 10
    },
    "dairy": {
        "type": "adequacy", "best": 1.3, "worst": 0.0, "max_points": 10
    },
    "total_protein_foods": {
        "type": "adequacy", "best": 2.5, "worst": 0.0, "max_points": 5
    },
    "seafood_plant_proteins": {
        "type": "adequacy", "best": 0.8, "worst": 0.0, "max_points": 5
    },
    "fatty_acids": {
        "type": "adequacy", "best": 2.5, "worst": 1.2, "max_points": 10
    },
    "refined_grains": {
        "type": "moderation", "best": 1.8, "worst": 4.3, "max_points": 10
    },
    "sodium": {
        "type": "moderation", "best": 1.1, "worst": 2.0, "max_points": 10
    },
    "added_sugars": {
        "type": "moderation", "best": 6.5, "worst": 26.0, "max_points": 10
    },
    "saturated_fats": {
        "type": "moderation", "best": 8.0, "worst": 16.0, "max_points": 10
    },
}

HEI_COMPONENTS = {
    name: standard["max_points"]
    for name, standard in HEI_STANDARDS.items()
}

MAX_HEI_SCORE = sum(HEI_COMPONENTS.values())


def validate_number(value, name):
    if value is None:
        raise ValueError(f"Missing required value: {name}")

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")

    if not isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative")

    return float(value)


def score_adequacy(value, best, max_points, worst=0.0):
    value = validate_number(value, "value")

    if value <= worst:
        return 0.0

    if value >= best:
        return float(max_points)

    return max_points * (value - worst) / (best - worst)


def score_moderation(value, best, worst, max_points=10):
    value = validate_number(value, "value")

    if value <= best:
        return float(max_points)

    if value >= worst:
        return 0.0

    return max_points * (worst - value) / (worst - best)


def calculate_component_score(component, value):
    if component not in HEI_STANDARDS:
        raise ValueError(f"Unknown HEI component: {component}")

    standard = HEI_STANDARDS[component]

    if standard["type"] == "adequacy":
        score = score_adequacy(
            value,
            standard["best"],
            standard["max_points"],
            standard["worst"],
        )
    else:
        score = score_moderation(
            value,
            standard["best"],
            standard["worst"],
            standard["max_points"],
        )

    return round(score, 2)


def per_1000_kcal(amount, calories):
    amount = validate_number(amount, "amount")
    calories = validate_number(calories, "calories")

    if calories == 0:
        raise ValueError("Calories must be greater than zero")

    return amount * 1000 / calories


def percent_energy(grams, calories, kcal_per_gram):
    grams = validate_number(grams, "grams")
    calories = validate_number(calories, "calories")

    if calories == 0:
        raise ValueError("Calories must be greater than zero")

    return grams * kcal_per_gram / calories * 100


def fatty_acid_ratio(mufa_g, pufa_g, saturated_fat_g):
    mufa = validate_number(mufa_g, "mufa_g")
    pufa = validate_number(pufa_g, "pufa_g")
    saturated = validate_number(saturated_fat_g, "saturated_fat_g")

    if saturated == 0:
        if mufa + pufa > 0:
            return float("inf")
        raise ValueError("Fatty acid ratio is undefined (0/0)")

    return (mufa + pufa) / saturated


# Inputs must be aggregated over the same dietary period.
# Food-group equivalents must already be prepared from FPED.
# Legumes must be allocated according to HEI methodology
# before constructing the component totals.
#
# Expected keys:
# calories
# total_fruits_cup
# whole_fruits_cup
# total_vegetables_cup
# greens_and_beans_cup
# whole_grains_oz
# dairy_cup
# total_protein_foods_oz
# seafood_plant_proteins_oz
# refined_grains_oz
# sodium_mg
# added_sugars_tsp
# saturated_fat_g
# monounsaturated_fat_g
# polyunsaturated_fat_g


def calculate_hei_2020(data):
    required = [
        "calories",
        "total_fruits_cup",
        "whole_fruits_cup",
        "total_vegetables_cup",
        "greens_and_beans_cup",
        "whole_grains_oz",
        "dairy_cup",
        "total_protein_foods_oz",
        "seafood_plant_proteins_oz",
        "refined_grains_oz",
        "sodium_mg",
        "added_sugars_tsp",
        "saturated_fat_g",
        "monounsaturated_fat_g",
        "polyunsaturated_fat_g",
    ]

    if not isinstance(data, dict):
        raise ValueError("Input must be a dictionary")

    missing = [key for key in required if data.get(key) is None]

    if missing:
        raise ValueError(
            "Cannot calculate HEI-2020. Missing: "
            + ", ".join(missing)
        )

    values = {
        key: validate_number(data[key], key)
        for key in required
    }

    calories = values["calories"]

    if calories <= 0:
        raise ValueError("Calories must be greater than zero")

    # Food-group densities per 1,000 kcal
    densities = {
        "total_fruits": per_1000_kcal(
            values["total_fruits_cup"], calories
        ),
        "whole_fruits": per_1000_kcal(
            values["whole_fruits_cup"], calories
        ),
        "total_vegetables": per_1000_kcal(
            values["total_vegetables_cup"], calories
        ),
        "greens_and_beans": per_1000_kcal(
            values["greens_and_beans_cup"], calories
        ),
        "whole_grains": per_1000_kcal(
            values["whole_grains_oz"], calories
        ),
        "dairy": per_1000_kcal(
            values["dairy_cup"], calories
        ),
        "total_protein_foods": per_1000_kcal(
            values["total_protein_foods_oz"], calories
        ),
        "seafood_plant_proteins": per_1000_kcal(
            values["seafood_plant_proteins_oz"], calories
        ),
        "refined_grains": per_1000_kcal(
            values["refined_grains_oz"], calories
        ),
        "sodium": per_1000_kcal(
            values["sodium_mg"] / 1000, calories
        ),
    }

    # Added sugar: 1 tsp equivalent = 4.2 g,
    # approximately 16.8 kcal.
    densities["added_sugars"] = percent_energy(
        values["added_sugars_tsp"] * 4.2,
        calories,
        4,
    )

    # Saturated fat: 9 kcal per gram
    densities["saturated_fats"] = percent_energy(
        values["saturated_fat_g"],
        calories,
        9,
    )

    densities["fatty_acids"] = fatty_acid_ratio(
        values["monounsaturated_fat_g"],
        values["polyunsaturated_fat_g"],
        values["saturated_fat_g"],
    )

    component_scores = {
        component: calculate_component_score(
            component, densities[component]
        )
        for component in HEI_STANDARDS
    }

    total_score = round(sum(component_scores.values()), 2)

    return {
        "heiVersion": "HEI-2020",
        "totalScore": total_score,
        "maxScore": MAX_HEI_SCORE,
        "componentScores": component_scores,
        "componentValues": densities,
        "status": "calculated_from_supplied_data",
    }


if __name__ == "__main__":
    print("Maximum HEI Score:", MAX_HEI_SCORE)

    print(
        "Total Fruits:",
        calculate_component_score("total_fruits", 0.4)
    )

    print(
        "Whole Fruits:",
        calculate_component_score("whole_fruits", 0.2)
    )

    print(
        "Total Vegetables:",
        calculate_component_score("total_vegetables", 0.55)
    )

    print(
        "Sodium:",
        calculate_component_score("sodium", 1.1)
    )

    # Synthetic test data only.
    # These values are NOT actual USDA/FPED results.
    sample_data = {
        "calories": 2000,
        "total_fruits_cup": 1.6,
        "whole_fruits_cup": 0.8,
        "total_vegetables_cup": 2.2,
        "greens_and_beans_cup": 0.4,
        "whole_grains_oz": 3.0,
        "dairy_cup": 2.6,
        "total_protein_foods_oz": 5.0,
        "seafood_plant_proteins_oz": 1.6,
        "refined_grains_oz": 3.6,
        "sodium_mg": 2200,
        "added_sugars_tsp": 5.0,
        "saturated_fat_g": 15.0,
        "monounsaturated_fat_g": 25.0,
        "polyunsaturated_fat_g": 15.0,
    }

    result = calculate_hei_2020(sample_data)

    print("\nHEI-2020 component scores:")

    for component, score in result["componentScores"].items():
        print(f"{component}: {score}")

    print("\nTotal HEI-2020 Score:", result["totalScore"])
    print("Maximum Possible Score:", result["maxScore"])
