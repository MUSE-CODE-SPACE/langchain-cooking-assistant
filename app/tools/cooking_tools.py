"""
Cooking Tools - LangChain tools for the cooking assistant
"""

from __future__ import annotations

import json

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.data.recipes import (
    RECIPES_DB,
    TECHNIQUES_DB,
    Cuisine,
    DietaryTag,
    Difficulty,
    get_all_cuisines,
    get_all_dietary_tags,
    get_ingredient_info,
    get_recipe,
    get_technique_info,
    search_recipes,
)


class RecipeSearchInput(BaseModel):
    """Input for recipe search."""
    query: str = Field(default="", description="Search term for recipe name or ingredients")
    cuisine: str | None = Field(
        default=None, description="Cuisine type (korean, italian, mexican, etc.)"
    )
    difficulty: str | None = Field(
        default=None, description="Difficulty level (easy, medium, hard)"
    )
    dietary_tags: list[str] | None = Field(
        default=None,
        description="Dietary requirements (vegetarian, vegan, gluten_free, etc.)",
    )
    max_time_min: int | None = Field(
        default=None, description="Maximum total cooking time in minutes"
    )


class RecipeSearchTool(BaseTool):
    """Tool for searching recipes."""
    name: str = "recipe_search"
    description: str = (
        "Search for recipes by name, cuisine, difficulty, dietary requirements, or cooking time"
    )
    args_schema: type[BaseModel] = RecipeSearchInput

    def _run(
        self,
        query: str = "",
        cuisine: str | None = None,
        difficulty: str | None = None,
        dietary_tags: list[str] | None = None,
        max_time_min: int | None = None,
    ) -> str:
        cuisine_enum: Cuisine | None = None
        if cuisine:
            try:
                cuisine_enum = Cuisine(cuisine.lower())
            except ValueError:
                return json.dumps(
                    {
                        "error": f"Unknown cuisine: {cuisine}",
                        "available_cuisines": get_all_cuisines(),
                    },
                    indent=2,
                )

        difficulty_enum: Difficulty | None = None
        if difficulty:
            try:
                difficulty_enum = Difficulty(difficulty.lower())
            except ValueError:
                return json.dumps(
                    {
                        "error": f"Unknown difficulty: {difficulty}",
                        "available_difficulties": ["easy", "medium", "hard"],
                    },
                    indent=2,
                )

        dietary_tags_enum: list[DietaryTag] | None = None
        if dietary_tags:
            try:
                dietary_tags_enum = [DietaryTag(tag.lower()) for tag in dietary_tags]
            except ValueError as e:
                return json.dumps(
                    {
                        "error": str(e),
                        "available_dietary_tags": get_all_dietary_tags(),
                    },
                    indent=2,
                )

        results = search_recipes(
            query=query,
            cuisine=cuisine_enum,
            difficulty=difficulty_enum,
            dietary_tags=dietary_tags_enum,
            max_time_min=max_time_min,
        )

        if not results:
            return json.dumps(
                {
                    "message": "No recipes found matching your criteria.",
                    "suggestion": "Try broadening your search or removing some filters.",
                },
                indent=2,
            )

        recipes_list = [
            {
                "id": recipe.id,
                "name": recipe.name,
                "cuisine": recipe.cuisine.value,
                "difficulty": recipe.difficulty.value,
                "total_time": f"{recipe.prep_time_min + recipe.cook_time_min} min",
                "servings": recipe.servings,
                "dietary_tags": [tag.value for tag in recipe.dietary_tags],
            }
            for recipe in results[:10]
        ]

        return json.dumps({"found": len(results), "recipes": recipes_list}, indent=2)


class RecipeDetailInput(BaseModel):
    """Input for getting recipe details."""
    recipe_id: str = Field(description="The recipe ID to get details for")


class RecipeDetailTool(BaseTool):
    """Tool for getting full recipe details."""
    name: str = "recipe_detail"
    description: str = "Get the full recipe with ingredients and step-by-step instructions"
    args_schema: type[BaseModel] = RecipeDetailInput

    def _run(self, recipe_id: str) -> str:
        recipe = get_recipe(recipe_id)

        if not recipe:
            for key, r in RECIPES_DB.items():
                if recipe_id.lower() in key or recipe_id.lower() in r.name.lower():
                    recipe = r
                    break

        if not recipe:
            return json.dumps(
                {
                    "error": f"Recipe '{recipe_id}' not found.",
                    "available_recipes": list(RECIPES_DB.keys()),
                },
                indent=2,
            )

        ingredients_list = []
        for ing in recipe.ingredients:
            ing_str = f"{ing.amount} {ing.unit} {ing.name}".strip()
            if ing.notes:
                ing_str += f" ({ing.notes})"
            ingredients_list.append(ing_str)

        result: dict = {
            "name": recipe.name,
            "description": recipe.description,
            "cuisine": recipe.cuisine.value,
            "difficulty": recipe.difficulty.value,
            "prep_time": f"{recipe.prep_time_min} minutes",
            "cook_time": f"{recipe.cook_time_min} minutes",
            "total_time": f"{recipe.prep_time_min + recipe.cook_time_min} minutes",
            "servings": recipe.servings,
            "dietary_info": [tag.value for tag in recipe.dietary_tags],
            "ingredients": ingredients_list,
            "instructions": recipe.instructions,
            "tips": recipe.tips,
        }

        if recipe.nutrition:
            result["nutrition_per_serving"] = {
                "calories": recipe.nutrition.calories,
                "protein": f"{recipe.nutrition.protein_g}g",
                "carbs": f"{recipe.nutrition.carbs_g}g",
                "fat": f"{recipe.nutrition.fat_g}g",
            }

        return json.dumps(result, indent=2)


class IngredientSubstituteInput(BaseModel):
    """Input for finding ingredient substitutes."""
    ingredient: str = Field(description="The ingredient to find substitutes for")


class IngredientSubstituteTool(BaseTool):
    """Tool for finding ingredient substitutes."""
    name: str = "ingredient_substitute"
    description: str = "Find substitutes for a specific ingredient"
    args_schema: type[BaseModel] = IngredientSubstituteInput

    def _run(self, ingredient: str) -> str:
        info = get_ingredient_info(ingredient)

        if info:
            return json.dumps(
                {
                    "ingredient": info["name"],
                    "substitutes": info["substitutes"],
                    "storage_tips": info["storage"],
                },
                indent=2,
            )

        ingredient_lower = ingredient.lower()
        for recipe in RECIPES_DB.values():
            for ing in recipe.ingredients:
                if ingredient_lower in ing.name.lower() and ing.substitutes:
                    return json.dumps(
                        {
                            "ingredient": ing.name,
                            "substitutes": ing.substitutes,
                            "from_recipe": recipe.name,
                        },
                        indent=2,
                    )

        common_substitutes = {
            "milk": ["Oat milk", "Almond milk", "Soy milk", "Coconut milk"],
            "cream": ["Coconut cream", "Cashew cream", "Evaporated milk"],
            "flour": ["Almond flour", "Oat flour", "Coconut flour (use less)"],
            "sugar": ["Honey", "Maple syrup", "Stevia", "Coconut sugar"],
            "lemon": ["Lime", "White wine vinegar", "Citric acid"],
            "wine": ["Broth + splash of vinegar", "Grape juice", "Apple juice"],
        }

        for key, subs in common_substitutes.items():
            if key in ingredient_lower:
                return json.dumps(
                    {
                        "ingredient": ingredient,
                        "substitutes": subs,
                        "note": "Amounts may need adjustment",
                    },
                    indent=2,
                )

        return json.dumps(
            {
                "message": f"No specific substitutes found for '{ingredient}'",
                "suggestion": (
                    "Try searching for the base ingredient or consult a substitution guide"
                ),
            },
            indent=2,
        )


class CookingTechniqueInput(BaseModel):
    """Input for cooking technique information."""
    technique: str = Field(description="The cooking technique to learn about")


class CookingTechniqueTool(BaseTool):
    """Tool for learning about cooking techniques."""
    name: str = "cooking_technique"
    description: str = (
        "Get information about cooking techniques like sauté, braise, roast, etc."
    )
    args_schema: type[BaseModel] = CookingTechniqueInput

    def _run(self, technique: str) -> str:
        info = get_technique_info(technique)

        if info:
            return json.dumps(
                {
                    "technique": info["name"],
                    "description": info["description"],
                    "best_for": info["best_for"],
                    "tips": info["tips"],
                },
                indent=2,
            )

        available = list(TECHNIQUES_DB.keys())
        return json.dumps(
            {
                "error": f"Technique '{technique}' not found",
                "available_techniques": available,
            },
            indent=2,
        )


class MealPlanInput(BaseModel):
    """Input for meal planning."""
    days: int = Field(default=7, description="Number of days to plan for")
    preferences: list[str] | None = Field(default=None, description="Dietary preferences")
    cuisine_variety: bool = Field(default=True, description="Include variety of cuisines")


class MealPlanTool(BaseTool):
    """Tool for generating meal plans."""
    name: str = "meal_plan"
    description: str = "Generate a meal plan for multiple days with recipe suggestions"
    args_schema: type[BaseModel] = MealPlanInput

    def _run(
        self,
        days: int = 7,
        preferences: list[str] | None = None,
        cuisine_variety: bool = True,
    ) -> str:
        all_recipes = list(RECIPES_DB.values())

        if preferences:
            filtered = []
            for recipe in all_recipes:
                tags = [tag.value for tag in recipe.dietary_tags]
                if any(pref.lower() in tags for pref in preferences):
                    filtered.append(recipe)
            if filtered:
                all_recipes = filtered

        cuisines_used: set[str] = set()
        meal_plan = []

        for day in range(1, min(days + 1, 8)):
            available = all_recipes.copy()

            if cuisine_variety and len(cuisines_used) < len(all_recipes):
                available = [
                    r for r in all_recipes if r.cuisine.value not in cuisines_used
                ]
                if not available:
                    available = all_recipes
                    cuisines_used.clear()

            if available:
                recipe = available[day % len(available)]
                cuisines_used.add(recipe.cuisine.value)

                meal_plan.append(
                    {
                        "day": day,
                        "recipe": {
                            "id": recipe.id,
                            "name": recipe.name,
                            "cuisine": recipe.cuisine.value,
                            "time": f"{recipe.prep_time_min + recipe.cook_time_min} min",
                            "difficulty": recipe.difficulty.value,
                        },
                    }
                )

        return json.dumps(
            {
                "meal_plan": meal_plan,
                "total_days": len(meal_plan),
                "tip": "Use 'recipe_detail' tool to get full recipe for each meal",
            },
            indent=2,
        )


class UnitConversionInput(BaseModel):
    """Input for unit conversion."""
    amount: float = Field(description="The amount to convert")
    from_unit: str = Field(description="The unit to convert from")
    to_unit: str = Field(description="The unit to convert to")


class UnitConversionTool(BaseTool):
    """Tool for converting cooking units."""
    name: str = "unit_conversion"
    description: str = (
        "Convert between cooking measurements (cups, tbsp, ml, g, oz, etc.)"
    )
    args_schema: type[BaseModel] = UnitConversionInput

    def _run(self, amount: float, from_unit: str, to_unit: str) -> str:
        volume_to_ml = {
            "ml": 1,
            "l": 1000,
            "liter": 1000,
            "cup": 236.588,
            "cups": 236.588,
            "tbsp": 14.787,
            "tablespoon": 14.787,
            "tsp": 4.929,
            "teaspoon": 4.929,
            "fl_oz": 29.574,
            "fluid_ounce": 29.574,
            "pint": 473.176,
            "quart": 946.353,
            "gallon": 3785.41,
        }

        weight_to_g = {
            "g": 1,
            "gram": 1,
            "grams": 1,
            "kg": 1000,
            "kilogram": 1000,
            "oz": 28.3495,
            "ounce": 28.3495,
            "lb": 453.592,
            "pound": 453.592,
        }

        from_unit_clean = from_unit.lower().replace(" ", "_")
        to_unit_clean = to_unit.lower().replace(" ", "_")

        if from_unit_clean in volume_to_ml and to_unit_clean in volume_to_ml:
            ml_value = amount * volume_to_ml[from_unit_clean]
            result = ml_value / volume_to_ml[to_unit_clean]
            return json.dumps(
                {
                    "original": f"{amount} {from_unit}",
                    "converted": f"{round(result, 2)} {to_unit}",
                    "type": "volume",
                },
                indent=2,
            )

        if from_unit_clean in weight_to_g and to_unit_clean in weight_to_g:
            g_value = amount * weight_to_g[from_unit_clean]
            result = g_value / weight_to_g[to_unit_clean]
            return json.dumps(
                {
                    "original": f"{amount} {from_unit}",
                    "converted": f"{round(result, 2)} {to_unit}",
                    "type": "weight",
                },
                indent=2,
            )

        is_celsius_from = "celsius" in from_unit_clean or from_unit_clean == "c"
        is_fahrenheit_from = "fahrenheit" in from_unit_clean or from_unit_clean == "f"
        is_celsius_to = "celsius" in to_unit_clean or to_unit_clean == "c"
        is_fahrenheit_to = "fahrenheit" in to_unit_clean or to_unit_clean == "f"

        if is_celsius_from and is_fahrenheit_to:
            result = (amount * 9 / 5) + 32
            return json.dumps(
                {
                    "original": f"{amount}°C",
                    "converted": f"{round(result)}°F",
                    "type": "temperature",
                },
                indent=2,
            )

        if is_fahrenheit_from and is_celsius_to:
            result = (amount - 32) * 5 / 9
            return json.dumps(
                {
                    "original": f"{amount}°F",
                    "converted": f"{round(result)}°C",
                    "type": "temperature",
                },
                indent=2,
            )

        return json.dumps(
            {
                "error": f"Cannot convert from {from_unit} to {to_unit}",
                "supported_volume": list(volume_to_ml.keys()),
                "supported_weight": list(weight_to_g.keys()),
                "supported_temp": ["celsius", "fahrenheit", "C", "F"],
            },
            indent=2,
        )


class NutritionCalculatorInput(BaseModel):
    """Input for nutrition calculation."""
    recipe_id: str = Field(description="Recipe ID to calculate nutrition for")
    servings: int = Field(default=1, description="Number of servings")


class NutritionCalculatorTool(BaseTool):
    """Tool for calculating recipe nutrition."""
    name: str = "nutrition_calculator"
    description: str = "Calculate nutritional information for a recipe"
    args_schema: type[BaseModel] = NutritionCalculatorInput

    def _run(self, recipe_id: str, servings: int = 1) -> str:
        recipe = get_recipe(recipe_id)

        if not recipe:
            return json.dumps({"error": f"Recipe '{recipe_id}' not found"}, indent=2)

        if not recipe.nutrition:
            return json.dumps(
                {
                    "recipe": recipe.name,
                    "message": "Nutrition information not available for this recipe",
                },
                indent=2,
            )

        n = recipe.nutrition
        multiplier = servings

        return json.dumps(
            {
                "recipe": recipe.name,
                "servings_calculated": servings,
                "nutrition": {
                    "calories": n.calories * multiplier,
                    "protein_g": round(n.protein_g * multiplier, 1),
                    "carbs_g": round(n.carbs_g * multiplier, 1),
                    "fat_g": round(n.fat_g * multiplier, 1),
                    "fiber_g": round(n.fiber_g * multiplier, 1),
                    "sodium_mg": n.sodium_mg * multiplier,
                },
                "daily_values_note": "Based on 2000 calorie diet",
            },
            indent=2,
        )


class TimerCalculatorInput(BaseModel):
    """Input for cooking timer suggestions."""
    food_item: str = Field(description="The food item to get cooking time for")
    cooking_method: str = Field(description="Cooking method (bake, boil, grill, etc.)")
    weight_or_size: str | None = Field(
        default=None, description="Weight or size description"
    )


class TimerCalculatorTool(BaseTool):
    """Tool for suggesting cooking times."""
    name: str = "timer_calculator"
    description: str = "Get recommended cooking times for different foods and methods"
    args_schema: type[BaseModel] = TimerCalculatorInput

    def _run(
        self,
        food_item: str,
        cooking_method: str,
        weight_or_size: str | None = None,
    ) -> str:
        cooking_times = {
            "chicken_breast": {
                "bake": {
                    "temp": "375°F (190°C)",
                    "time": "20-25 min",
                    "internal_temp": "165°F (74°C)",
                },
                "grill": {
                    "temp": "Medium-high",
                    "time": "6-8 min per side",
                    "internal_temp": "165°F (74°C)",
                },
                "pan_fry": {
                    "temp": "Medium-high",
                    "time": "6-7 min per side",
                    "internal_temp": "165°F (74°C)",
                },
                "poach": {
                    "temp": "Simmer",
                    "time": "15-20 min",
                    "internal_temp": "165°F (74°C)",
                },
            },
            "steak": {
                "grill": {
                    "rare": "2-3 min per side (125°F/52°C)",
                    "medium_rare": "3-4 min per side (135°F/57°C)",
                    "medium": "4-5 min per side (145°F/63°C)",
                    "well_done": "5-6 min per side (160°F/71°C)",
                },
                "pan_sear": {
                    "rare": "2-3 min per side",
                    "medium_rare": "3-4 min per side",
                    "medium": "4-5 min per side",
                },
            },
            "eggs": {
                "boil": {
                    "soft_boil": "6-7 min",
                    "medium_boil": "9-10 min",
                    "hard_boil": "12-13 min",
                },
                "fry": {"sunny_side": "2-3 min", "over_easy": "1 min flip + 30 sec"},
                "scramble": {"time": "3-5 min", "tip": "Low heat, constantly stir"},
                "poach": {"time": "3-4 min", "tip": "Simmer, don't boil"},
            },
            "pasta": {"boil": {"dried": "8-12 min (check package)", "fresh": "2-4 min"}},
            "rice": {
                "boil": {
                    "white": "18-20 min",
                    "brown": "40-45 min",
                    "tip": "Let rest 5 min after cooking",
                }
            },
            "vegetables": {
                "steam": {
                    "broccoli": "5-7 min",
                    "carrots": "7-10 min",
                    "asparagus": "4-6 min",
                },
                "roast": {
                    "temp": "400°F (200°C)",
                    "time": "20-30 min",
                    "tip": "Cut uniformly",
                },
                "saute": {"time": "5-8 min", "tip": "High heat, keep moving"},
            },
            "fish": {
                "bake": {
                    "temp": "400°F (200°C)",
                    "time": "10-12 min per inch thickness",
                },
                "grill": {"time": "3-4 min per side"},
                "pan_sear": {"time": "3-4 min per side"},
            },
        }

        food_key = food_item.lower().replace(" ", "_")
        method_key = cooking_method.lower().replace(" ", "_").replace("-", "_")

        result = None
        for key in cooking_times:
            if key in food_key or food_key in key:
                if method_key in cooking_times[key]:
                    result = {
                        "food": food_item,
                        "method": cooking_method,
                        "cooking_info": cooking_times[key][method_key],
                    }
                else:
                    result = {
                        "food": food_item,
                        "available_methods": list(cooking_times[key].keys()),
                        "tip": f"Try one of these methods for {food_item}",
                    }
                break

        if result:
            return json.dumps(result, indent=2)

        return json.dumps(
            {
                "message": (
                    f"Specific timing not found for {food_item} ({cooking_method})"
                ),
                "general_tip": "Use a food thermometer for best results",
                "available_foods": list(cooking_times.keys()),
            },
            indent=2,
        )


def get_cooking_tools() -> list[BaseTool]:
    """Get all cooking assistant tools."""
    return [
        RecipeSearchTool(),
        RecipeDetailTool(),
        IngredientSubstituteTool(),
        CookingTechniqueTool(),
        MealPlanTool(),
        UnitConversionTool(),
        NutritionCalculatorTool(),
        TimerCalculatorTool(),
    ]
