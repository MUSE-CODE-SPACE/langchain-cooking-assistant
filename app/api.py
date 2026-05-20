"""
Flask API for Cooking Assistant.

Run for development with:

    python -m app.api

For production, prefer running through gunicorn:

    gunicorn --bind 0.0.0.0:5000 --workers 2 app.api:app
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask.wrappers import Response
from flask_cors import CORS

from app.agents.cooking_agent import CookingAssistantAgent, create_cooking_agent
from app.data.recipes import (
    RECIPES_DB,
    TECHNIQUES_DB,
    Cuisine,
    DietaryTag,
    Difficulty,
    search_recipes,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_STATIC = _REPO_ROOT / "static"
_DEFAULT_TEMPLATES = _REPO_ROOT / "templates"


def create_app() -> Flask:
    """Application factory."""
    app = Flask(
        __name__,
        static_folder=str(_DEFAULT_STATIC),
        template_folder=str(_DEFAULT_TEMPLATES),
    )
    CORS(app)

    agents: dict[str, CookingAssistantAgent] = {}

    def get_agent(session_id: str) -> CookingAssistantAgent:
        if session_id not in agents:
            agents[session_id] = create_cooking_agent()
        return agents[session_id]

    @app.route("/")
    def index() -> Response | str:
        # Templates are optional in this repo (the demo lives under docs/).
        if (_DEFAULT_TEMPLATES / "index.html").exists():
            return render_template("index.html")
        return jsonify(
            {
                "service": "cooking-assistant",
                "message": "Cooking Assistant API. See /api/health and /api/recipes.",
            }
        )

    @app.route("/static/<path:filename>")
    def serve_static(filename: str) -> Response:
        return send_from_directory(app.static_folder, filename)

    @app.route("/api/health", methods=["GET"])
    def health_check() -> Response:
        agent_count = len(agents)
        sample_agent = next(iter(agents.values()), None)
        llm_enabled = sample_agent.llm_enabled if sample_agent is not None else False
        return jsonify(
            {
                "status": "healthy",
                "service": "cooking-assistant",
                "timestamp": datetime.now(UTC).isoformat(),
                "active_sessions": agent_count,
                "llm_enabled": llm_enabled,
            }
        )

    @app.route("/api/chat", methods=["POST"])
    def chat() -> tuple[Response, int] | Response:
        data = request.get_json(silent=True) or {}
        session_id = data.get("session_id", "default")
        message = data.get("message", "")

        if not message:
            return jsonify({"error": "Message is required"}), 400

        try:
            agent = get_agent(session_id)
            response = agent.chat(message)
            return jsonify(
                {
                    "response": response,
                    "session_id": session_id,
                    "llm_enabled": agent.llm_enabled,
                }
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/recipes", methods=["GET"])
    def list_recipes() -> Response:
        """List all recipes."""
        recipes = [
            {
                "id": key,
                "name": recipe.name,
                "cuisine": recipe.cuisine.value,
                "difficulty": recipe.difficulty.value,
                "prep_time": recipe.prep_time_min,
                "cook_time": recipe.cook_time_min,
                "servings": recipe.servings,
                "dietary_tags": [tag.value for tag in recipe.dietary_tags],
            }
            for key, recipe in RECIPES_DB.items()
        ]
        return jsonify({"recipes": recipes})

    @app.route("/api/recipes/<recipe_id>", methods=["GET"])
    def get_recipe(recipe_id: str) -> tuple[Response, int] | Response:
        """Get a specific recipe."""
        recipe = RECIPES_DB.get(recipe_id)
        if not recipe:
            return jsonify({"error": "Recipe not found"}), 404

        ingredients = [
            {
                "name": ing.name,
                "amount": ing.amount,
                "unit": ing.unit,
                "notes": ing.notes,
                "substitutes": ing.substitutes,
            }
            for ing in recipe.ingredients
        ]

        nutrition = None
        if recipe.nutrition:
            nutrition = {
                "calories": recipe.nutrition.calories,
                "protein_g": recipe.nutrition.protein_g,
                "carbs_g": recipe.nutrition.carbs_g,
                "fat_g": recipe.nutrition.fat_g,
                "fiber_g": recipe.nutrition.fiber_g,
                "sodium_mg": recipe.nutrition.sodium_mg,
            }

        return jsonify(
            {
                "id": recipe.id,
                "name": recipe.name,
                "description": recipe.description,
                "cuisine": recipe.cuisine.value,
                "difficulty": recipe.difficulty.value,
                "prep_time": recipe.prep_time_min,
                "cook_time": recipe.cook_time_min,
                "servings": recipe.servings,
                "ingredients": ingredients,
                "instructions": recipe.instructions,
                "tips": recipe.tips,
                "dietary_tags": [tag.value for tag in recipe.dietary_tags],
                "nutrition": nutrition,
            }
        )

    @app.route("/api/recipes/search", methods=["GET"])
    def search_recipes_api() -> Response:
        """Search recipes with filters."""
        query = request.args.get("q", "")
        cuisine = request.args.get("cuisine")
        difficulty = request.args.get("difficulty")
        dietary = request.args.getlist("dietary")
        max_time = request.args.get("max_time", type=int)

        cuisine_enum = Cuisine(cuisine) if cuisine else None
        difficulty_enum = Difficulty(difficulty) if difficulty else None
        dietary_enums = [DietaryTag(d) for d in dietary] if dietary else None

        results = search_recipes(
            query=query,
            cuisine=cuisine_enum,
            difficulty=difficulty_enum,
            dietary_tags=dietary_enums,
            max_time_min=max_time,
        )

        recipes = [
            {
                "id": recipe.id,
                "name": recipe.name,
                "cuisine": recipe.cuisine.value,
                "difficulty": recipe.difficulty.value,
                "total_time": recipe.prep_time_min + recipe.cook_time_min,
                "servings": recipe.servings,
                "dietary_tags": [tag.value for tag in recipe.dietary_tags],
            }
            for recipe in results
        ]

        return jsonify({"results": recipes, "count": len(recipes)})

    @app.route("/api/techniques", methods=["GET"])
    def list_techniques() -> Response:
        """List all cooking techniques."""
        techniques = [
            {
                "id": key,
                "name": tech["name"],
                "description": tech["description"],
                "best_for": tech["best_for"],
                "tips": tech["tips"],
            }
            for key, tech in TECHNIQUES_DB.items()
        ]
        return jsonify({"techniques": techniques})

    @app.route("/api/cuisines", methods=["GET"])
    def list_cuisines() -> Response:
        """List all available cuisines."""
        return jsonify({"cuisines": [c.value for c in Cuisine]})

    @app.route("/api/dietary-tags", methods=["GET"])
    def list_dietary_tags() -> Response:
        """List all dietary tags."""
        return jsonify({"dietary_tags": [t.value for t in DietaryTag]})

    @app.route("/api/convert", methods=["POST"])
    def convert_units() -> tuple[Response, int] | Response:
        """Convert cooking measurements."""
        data = request.get_json(silent=True) or {}
        amount = data.get("amount")
        from_unit = data.get("from_unit")
        to_unit = data.get("to_unit")

        if amount is None or not from_unit or not to_unit:
            return jsonify({"error": "Missing required fields"}), 400

        volume_to_ml = {
            "ml": 1,
            "l": 1000,
            "cup": 236.588,
            "cups": 236.588,
            "tbsp": 14.787,
            "tablespoon": 14.787,
            "tsp": 4.929,
            "teaspoon": 4.929,
            "fl_oz": 29.574,
            "fluid_ounce": 29.574,
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

        from_clean = from_unit.lower().replace(" ", "_")
        to_clean = to_unit.lower().replace(" ", "_")

        if from_clean in volume_to_ml and to_clean in volume_to_ml:
            ml_value = amount * volume_to_ml[from_clean]
            result = ml_value / volume_to_ml[to_clean]
            return jsonify(
                {
                    "original": {"amount": amount, "unit": from_unit},
                    "converted": {"amount": round(result, 2), "unit": to_unit},
                    "type": "volume",
                }
            )

        if from_clean in weight_to_g and to_clean in weight_to_g:
            g_value = amount * weight_to_g[from_clean]
            result = g_value / weight_to_g[to_clean]
            return jsonify(
                {
                    "original": {"amount": amount, "unit": from_unit},
                    "converted": {"amount": round(result, 2), "unit": to_unit},
                    "type": "weight",
                }
            )

        return jsonify({"error": "Unable to convert between these units"}), 400

    @app.route("/api/session/reset", methods=["POST"])
    def reset_session() -> Response:
        data = request.get_json(silent=True) or {}
        session_id = data.get("session_id", "default")

        if session_id in agents:
            agents[session_id].reset()
            del agents[session_id]

        return jsonify({"status": "reset", "session_id": session_id})

    return app


app = create_app()


if __name__ == "__main__":
    # Development entry point only. Use gunicorn (or another WSGI server) in
    # production: ``gunicorn --bind 0.0.0.0:5000 --workers 2 app.api:app``.
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
