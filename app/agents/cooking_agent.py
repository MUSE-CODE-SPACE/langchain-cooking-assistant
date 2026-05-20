"""
Cooking Agent - LangChain agent for cooking assistance.

Supports two execution modes:
1. LLM-backed mode (preferred): uses an Anthropic or OpenAI chat model with
   tool-calling via LangChain's LCEL ``create_tool_calling_agent`` +
   ``AgentExecutor``. Selected automatically when an API key is present.
2. Keyword router fallback: zero-dependency rule-based responder, used when no
   LLM credentials are available. Keeps the demo functional without API keys.
"""

from __future__ import annotations

import logging
import os
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.data.recipes import (
    RECIPES_DB,
    TECHNIQUES_DB,
    Cuisine,
    DietaryTag,
    Difficulty,
    get_recipes_by_ingredient,
    search_recipes,
)
from app.tools.cooking_tools import get_cooking_tools

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

DEFAULT_ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


@dataclass
class CookingContext:
    """Maintains cooking session context."""
    user_id: str = "default"
    current_recipe: str | None = None
    dietary_preferences: list[str] = field(default_factory=list)
    favorite_cuisines: list[str] = field(default_factory=list)
    cooking_skill: str = "intermediate"
    searched_recipes: list[str] = field(default_factory=list)


def _resolve_llm() -> BaseChatModel | None:
    """Return a chat model based on env config, or ``None`` if unavailable.

    Selection logic:
    - ``LLM_PROVIDER`` env var, one of ``anthropic`` / ``openai`` / ``none``.
    - Otherwise auto-detect from ``ANTHROPIC_API_KEY`` / ``OPENAI_API_KEY``.
    - Returns ``None`` if no provider is usable; caller falls back to the
      keyword router.
    """
    provider = (os.environ.get("LLM_PROVIDER") or "").strip().lower()

    has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
    has_openai = bool(os.environ.get("OPENAI_API_KEY"))

    if provider == "none":
        return None

    if not provider:
        if has_anthropic:
            provider = "anthropic"
        elif has_openai:
            provider = "openai"
        else:
            return None

    try:
        if provider == "anthropic":
            if not has_anthropic:
                logger.warning("LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is missing.")
                return None
            from langchain_anthropic import ChatAnthropic

            model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
            return ChatAnthropic(model=model, temperature=0.3)

        if provider == "openai":
            if not has_openai:
                logger.warning("LLM_PROVIDER=openai but OPENAI_API_KEY is missing.")
                return None
            from langchain_openai import ChatOpenAI

            model = os.environ.get("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
            return ChatOpenAI(model=model, temperature=0.3)
    except Exception as exc:
        logger.warning("Failed to construct LLM for provider %s: %s", provider, exc)
        return None

    logger.warning("Unknown LLM_PROVIDER=%s; falling back to keyword router.", provider)
    return None


class CookingAssistantAgent:
    """Cooking assistant with optional LLM-backed tool calling."""

    SYSTEM_PROMPT = """You are a friendly and knowledgeable cooking assistant.

Your capabilities:
1. **Recipe Search**: Find recipes by ingredients, cuisine, dietary needs, or cooking time
2. **Recipe Details**: Provide full recipes with ingredients and instructions
3. **Substitutions**: Suggest ingredient substitutes for allergies or availability
4. **Techniques**: Explain cooking techniques and methods
5. **Conversions**: Convert between cooking measurements
6. **Nutrition**: Calculate nutritional information
7. **Meal Planning**: Create weekly meal plans
8. **Timing**: Suggest cooking times for various foods

Guidelines:
- Be enthusiastic and encouraging about cooking
- Provide practical tips and suggestions
- Consider dietary restrictions when mentioned
- Offer alternatives when ingredients aren't available
- Give safety tips when relevant (food temperatures, allergies)
- Make cooking accessible for all skill levels
- Prefer using the provided tools to ground answers in the recipe database

You have access to a database of recipes from various cuisines including Korean, Italian, Mexican, Japanese, Thai, Indian, French, Mediterranean, and American."""

    def __init__(
        self,
        llm: BaseChatModel | None = None,
        verbose: bool = False,
        history_window: int = 10,
    ) -> None:
        """Initialize the cooking assistant.

        Args:
            llm: Optional pre-built chat model. If ``None``, one is auto-resolved
                from env (or the keyword router fallback is used).
            verbose: Enable agent executor verbose logging.
            history_window: Number of recent conversation turns to retain.
        """
        self.verbose = verbose
        self.context = CookingContext()
        self.conversation_history: list[dict[str, str]] = []
        # Rolling window of recent (role, content) pairs for context display.
        self._recent_turns: deque[tuple[str, str]] = deque(maxlen=history_window * 2)

        self.tools: list[BaseTool] = get_cooking_tools()
        self.llm: BaseChatModel | None = llm if llm is not None else _resolve_llm()

        self._agent_executor: Any | None = None
        if self.llm is not None:
            self._agent_executor = self._build_agent_executor()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def llm_enabled(self) -> bool:
        """``True`` if requests are answered by an LLM-backed agent."""
        return self._agent_executor is not None

    def chat(self, user_message: str) -> str:
        """Process user message and generate response."""
        timestamp = datetime.now(UTC).isoformat()
        self.conversation_history.append(
            {"role": "user", "content": user_message, "timestamp": timestamp}
        )
        self._recent_turns.append(("user", user_message))

        try:
            response = self._generate_response(user_message)
        except Exception as exc:
            logger.exception("Agent failed; falling back to keyword router: %s", exc)
            response = self._keyword_response(user_message)

        self.conversation_history.append(
            {
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        self._recent_turns.append(("assistant", response))
        return response

    def reset(self) -> None:
        """Reset the cooking assistant session state."""
        self.context = CookingContext()
        self.conversation_history = []
        self._recent_turns.clear()

    # ------------------------------------------------------------------
    # LLM-backed agent
    # ------------------------------------------------------------------
    def _build_agent_executor(self) -> Any:
        """Construct a LangChain tool-calling agent executor."""
        # Imported lazily so we only require these when an LLM is configured.
        from langchain.agents import AgentExecutor, create_tool_calling_agent

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.SYSTEM_PROMPT),
                MessagesPlaceholder("chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=self.verbose,
            max_iterations=6,
            handle_parsing_errors=True,
        )

    def _build_chat_history_messages(self) -> list[tuple[str, str]]:
        """Return prior turns formatted for LangChain message placeholders."""
        # Skip the most recent user turn (it is passed as ``input``).
        history = list(self._recent_turns)[:-1]
        return [
            ("human" if role == "user" else "ai", content) for role, content in history
        ]

    def _generate_response(self, message: str) -> str:
        """Dispatch to LLM-backed agent or keyword router."""
        if self._agent_executor is None:
            return self._keyword_response(message)

        result = self._agent_executor.invoke(
            {
                "input": message,
                "chat_history": self._build_chat_history_messages(),
            }
        )
        output = result.get("output")
        if isinstance(output, list):
            # Some providers return content blocks rather than a string.
            parts: list[str] = []
            for block in output:
                if isinstance(block, dict) and "text" in block:
                    parts.append(str(block["text"]))
                else:
                    parts.append(str(block))
            return "\n".join(parts).strip() or self._keyword_response(message)
        if isinstance(output, str) and output.strip():
            return output
        return self._keyword_response(message)

    # ------------------------------------------------------------------
    # Keyword-router fallback (used when no LLM is available)
    # ------------------------------------------------------------------
    def _keyword_response(self, message: str) -> str:
        """Generate a response using simple keyword routing."""
        message_lower = message.lower()

        if any(
            word in message_lower
            for word in ["recipe", "cook", "make", "prepare", "dish"]
        ):
            return self._handle_recipe_query(message)

        if any(
            word in message_lower
            for word in ["substitute", "replace", "instead of", "alternative"]
        ):
            return self._handle_substitute_query(message)

        if any(
            word in message_lower
            for word in [
                "how to",
                "technique",
                "method",
                "sauté",
                "braise",
                "roast",
                "grill",
            ]
        ):
            return self._handle_technique_query(message)

        if any(
            word in message_lower
            for word in [
                "convert",
                "cups to",
                "grams to",
                "tablespoon",
                "teaspoon",
                "ml",
                "ounce",
            ]
        ):
            return self._handle_conversion_query(message)

        if any(
            word in message_lower
            for word in ["meal plan", "weekly", "plan meals", "what to cook"]
        ):
            return self._handle_meal_plan_query(message)

        if any(
            word in message_lower
            for word in ["calories", "nutrition", "protein", "carbs", "healthy"]
        ):
            return self._handle_nutrition_query(message)

        if any(
            word in message_lower
            for word in ["how long", "time", "minutes", "temperature", "done"]
        ):
            return self._handle_timing_query(message)

        if any(
            word in message_lower
            for word in [
                "vegetarian",
                "vegan",
                "gluten",
                "dairy",
                "keto",
                "low carb",
            ]
        ):
            return self._handle_dietary_query(message)

        return self._handle_general_query(message)

    def _handle_recipe_query(self, message: str) -> str:
        """Handle recipe search and detail requests."""
        message_lower = message.lower()

        for recipe_id, recipe in RECIPES_DB.items():
            if (
                recipe_id.replace("_", " ") in message_lower
                or recipe.name.lower() in message_lower
            ):
                self.context.current_recipe = recipe_id
                return self._format_recipe(recipe)

        cuisine_map = {
            "korean": Cuisine.KOREAN,
            "japanese": Cuisine.JAPANESE,
            "italian": Cuisine.ITALIAN,
            "mexican": Cuisine.MEXICAN,
            "thai": Cuisine.THAI,
            "indian": Cuisine.INDIAN,
            "french": Cuisine.FRENCH,
            "chinese": Cuisine.CHINESE,
            "american": Cuisine.AMERICAN,
            "mediterranean": Cuisine.MEDITERRANEAN,
        }

        for cuisine_name, cuisine_enum in cuisine_map.items():
            if cuisine_name in message_lower:
                recipes = search_recipes(cuisine=cuisine_enum)
                return self._format_recipe_list(recipes, f"{cuisine_name.title()} Recipes")

        common_ingredients = [
            "chicken",
            "beef",
            "pork",
            "tofu",
            "rice",
            "pasta",
            "noodle",
            "vegetable",
            "egg",
        ]
        for ingredient in common_ingredients:
            if ingredient in message_lower:
                recipes = get_recipes_by_ingredient(ingredient)
                if recipes:
                    return self._format_recipe_list(
                        recipes, f"Recipes with {ingredient.title()}"
                    )

        if any(word in message_lower for word in ("easy", "simple", "quick")):
            recipes = search_recipes(difficulty=Difficulty.EASY)
            return self._format_recipe_list(recipes, "Easy Recipes")

        all_recipes = list(RECIPES_DB.values())
        return self._format_recipe_list(all_recipes, "Available Recipes")

    def _format_recipe(self, recipe) -> str:
        """Format a full recipe for display."""
        response = f"# {recipe.name}\n\n"
        response += f"*{recipe.description}*\n\n"

        response += f"**Cuisine:** {recipe.cuisine.value.title()} | "
        response += f"**Difficulty:** {recipe.difficulty.value.title()}\n"
        response += f"**Prep Time:** {recipe.prep_time_min} min | "
        response += f"**Cook Time:** {recipe.cook_time_min} min | "
        response += f"**Servings:** {recipe.servings}\n\n"

        if recipe.dietary_tags:
            tags = [tag.value.replace("_", " ").title() for tag in recipe.dietary_tags]
            response += f"**Dietary:** {', '.join(tags)}\n\n"

        response += "## Ingredients\n\n"
        for ing in recipe.ingredients:
            line = f"- {ing.amount} {ing.unit} {ing.name}".strip()
            if ing.notes:
                line += f" *({ing.notes})*"
            response += line + "\n"

        response += "\n## Instructions\n\n"
        for i, step in enumerate(recipe.instructions, 1):
            response += f"{i}. {step}\n"

        if recipe.tips:
            response += "\n## Tips\n\n"
            for tip in recipe.tips:
                response += f"- {tip}\n"

        if recipe.nutrition:
            response += "\n## Nutrition (per serving)\n\n"
            response += f"- Calories: {recipe.nutrition.calories}\n"
            response += f"- Protein: {recipe.nutrition.protein_g}g\n"
            response += f"- Carbs: {recipe.nutrition.carbs_g}g\n"
            response += f"- Fat: {recipe.nutrition.fat_g}g\n"

        return response

    def _format_recipe_list(self, recipes: list, title: str) -> str:
        """Format a list of recipes."""
        if not recipes:
            return f"# {title}\n\nNo recipes found. Try a different search!"

        response = f"# {title}\n\n"
        response += f"Found {len(recipes)} recipe(s):\n\n"

        for recipe in recipes[:10]:
            time_total = recipe.prep_time_min + recipe.cook_time_min
            response += f"### {recipe.name}\n"
            response += (
                f"{recipe.description[:100]}...\n"
                if len(recipe.description) > 100
                else f"{recipe.description}\n"
            )
            response += (
                f"{time_total} min | {recipe.difficulty.value.title()} | "
                f"{recipe.servings} servings\n\n"
            )

        response += "\n---\n*Ask me for the full recipe of any dish!*"
        return response

    def _handle_substitute_query(self, message: str) -> str:
        """Handle ingredient substitution requests."""
        common_subs = {
            "egg": [
                "Flax egg (1 tbsp ground flax + 3 tbsp water)",
                "Chia egg",
                "Mashed banana",
                "Applesauce",
            ],
            "butter": ["Coconut oil", "Olive oil", "Margarine", "Avocado"],
            "milk": ["Oat milk", "Almond milk", "Soy milk", "Coconut milk"],
            "cream": ["Coconut cream", "Cashew cream", "Silken tofu blended"],
            "flour": [
                "Almond flour",
                "Oat flour",
                "Rice flour",
                "Coconut flour (use less)",
            ],
            "sugar": ["Honey", "Maple syrup", "Coconut sugar", "Stevia"],
            "soy sauce": ["Tamari (gluten-free)", "Coconut aminos", "Worcestershire sauce"],
            "garlic": [
                "Garlic powder (1/4 tsp per clove)",
                "Shallots",
                "Garlic-infused oil",
            ],
        }

        response = "# Ingredient Substitutions\n\n"

        found_match = False
        for ingredient, subs in common_subs.items():
            if ingredient in message.lower():
                found_match = True
                response += f"## Substitutes for {ingredient.title()}\n\n"
                for sub in subs:
                    response += f"- {sub}\n"
                response += "\n"

        if not found_match:
            response += "Here are some common ingredient substitutions:\n\n"
            for ingredient, subs in list(common_subs.items())[:5]:
                response += f"**{ingredient.title()}:** {', '.join(subs[:2])}\n"
            response += "\n*Ask about a specific ingredient for more options!*"

        return response

    def _handle_technique_query(self, message: str) -> str:
        """Handle cooking technique questions."""
        response = "# Cooking Techniques\n\n"

        for tech_id, tech in TECHNIQUES_DB.items():
            if tech_id in message.lower() or tech["name"].lower() in message.lower():
                response += f"## {tech['name']}\n\n"
                response += f"{tech['description']}\n\n"
                response += "**Best for:**\n"
                for item in tech["best_for"]:
                    response += f"- {item}\n"
                response += "\n**Tips:**\n"
                for tip in tech["tips"]:
                    response += f"- {tip}\n"
                return response

        for _tech_id, tech in TECHNIQUES_DB.items():
            response += f"### {tech['name']}\n"
            response += f"{tech['description']}\n\n"

        response += "*Ask about any technique for detailed tips!*"
        return response

    def _handle_conversion_query(self, message: str) -> str:
        """Handle measurement conversion requests."""
        response = "# Cooking Measurement Conversions\n\n"

        response += "## Volume\n"
        response += "| Measurement | Equivalent |\n"
        response += "|-------------|------------|\n"
        response += "| 1 cup | 240 ml / 16 tbsp |\n"
        response += "| 1 tablespoon (tbsp) | 15 ml / 3 tsp |\n"
        response += "| 1 teaspoon (tsp) | 5 ml |\n"
        response += "| 1 fluid ounce | 30 ml / 2 tbsp |\n\n"

        response += "## Weight\n"
        response += "| Measurement | Equivalent |\n"
        response += "|-------------|------------|\n"
        response += "| 1 ounce (oz) | 28 grams |\n"
        response += "| 1 pound (lb) | 454 grams |\n"
        response += "| 1 kilogram | 2.2 pounds |\n\n"

        response += "## Temperature\n"
        response += "| Fahrenheit | Celsius | Description |\n"
        response += "|------------|---------|-------------|\n"
        response += "| 325F | 165C | Low oven |\n"
        response += "| 350F | 175C | Moderate oven |\n"
        response += "| 375F | 190C | Moderate-high |\n"
        response += "| 400F | 200C | Hot oven |\n"
        response += "| 425F | 220C | Very hot |\n\n"

        response += "*Need a specific conversion? Just ask!*"
        return response

    def _handle_meal_plan_query(self, message: str) -> str:
        """Handle meal planning requests."""
        recipes = list(RECIPES_DB.values())

        response = "# Weekly Meal Plan\n\n"
        response += "Here's a suggested meal plan with variety:\n\n"

        days = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

        for i, day in enumerate(days):
            recipe = recipes[i % len(recipes)]
            time_total = recipe.prep_time_min + recipe.cook_time_min
            response += f"### {day}: {recipe.name}\n"
            response += f"*{recipe.cuisine.value.title()}* | {time_total} min\n\n"

        response += "---\n"
        response += (
            "*Ask for any full recipe, or let me know your dietary preferences for a "
            "customized plan!*"
        )
        return response

    def _handle_nutrition_query(self, message: str) -> str:
        """Handle nutrition-related questions."""
        response = "# Nutrition Information\n\n"

        for recipe_id, recipe in RECIPES_DB.items():
            if (
                recipe_id.replace("_", " ") in message.lower()
                or recipe.name.lower() in message.lower()
            ) and recipe.nutrition:
                response += f"## {recipe.name} (per serving)\n\n"
                response += f"- **Calories:** {recipe.nutrition.calories}\n"
                response += f"- **Protein:** {recipe.nutrition.protein_g}g\n"
                response += f"- **Carbohydrates:** {recipe.nutrition.carbs_g}g\n"
                response += f"- **Fat:** {recipe.nutrition.fat_g}g\n"
                response += f"- **Fiber:** {recipe.nutrition.fiber_g}g\n"
                response += f"- **Sodium:** {recipe.nutrition.sodium_mg}mg\n"
                return response

        response += "Here's nutrition info for our recipes:\n\n"
        for recipe in RECIPES_DB.values():
            if recipe.nutrition:
                response += f"**{recipe.name}** ({recipe.servings} servings)\n"
                response += f"Per serving: {recipe.nutrition.calories} cal | "
                response += f"{recipe.nutrition.protein_g}g protein | "
                response += f"{recipe.nutrition.carbs_g}g carbs | "
                response += f"{recipe.nutrition.fat_g}g fat\n\n"

        return response

    def _handle_timing_query(self, message: str) -> str:
        """Handle cooking time questions."""
        response = "# Cooking Times Guide\n\n"

        response += "## Proteins\n\n"
        response += "### Chicken Breast\n"
        response += "- **Bake (375F):** 20-25 min\n"
        response += "- **Grill:** 6-8 min per side\n"
        response += "- **Pan-fry:** 6-7 min per side\n"
        response += "- *Internal temp: 165F (74C)*\n\n"

        response += "### Steak (1-inch thick)\n"
        response += "- **Rare:** 2-3 min per side (125F)\n"
        response += "- **Medium-rare:** 3-4 min per side (135F)\n"
        response += "- **Medium:** 4-5 min per side (145F)\n\n"

        response += "## Eggs\n"
        response += "- **Soft boil:** 6-7 min\n"
        response += "- **Medium boil:** 9-10 min\n"
        response += "- **Hard boil:** 12-13 min\n"
        response += "- **Poach:** 3-4 min\n\n"

        response += "## Basics\n"
        response += "- **Pasta:** 8-12 min (check package)\n"
        response += "- **White rice:** 18-20 min + 5 min rest\n"
        response += "- **Brown rice:** 40-45 min\n\n"

        response += "*Always use a meat thermometer for safety!*"
        return response

    def _handle_dietary_query(self, message: str) -> str:
        """Handle dietary preference queries."""
        message_lower = message.lower()

        dietary_map = {
            "vegetarian": DietaryTag.VEGETARIAN,
            "vegan": DietaryTag.VEGAN,
            "gluten": DietaryTag.GLUTEN_FREE,
            "dairy": DietaryTag.DAIRY_FREE,
            "keto": DietaryTag.KETO,
            "low carb": DietaryTag.LOW_CARB,
        }

        for keyword, tag in dietary_map.items():
            if keyword in message_lower:
                recipes = search_recipes(dietary_tags=[tag])
                return self._format_recipe_list(
                    recipes, f"{tag.value.replace('_', ' ').title()} Recipes"
                )

        response = "# Dietary Options\n\n"
        response += "I can find recipes for these dietary needs:\n\n"
        response += "- **Vegetarian** - No meat\n"
        response += "- **Vegan** - No animal products\n"
        response += "- **Gluten-Free** - No wheat/gluten\n"
        response += "- **Dairy-Free** - No dairy products\n"
        response += "- **Keto** - Low carb, high fat\n"
        response += "- **High Protein** - Protein-rich dishes\n\n"
        response += "*Just tell me your dietary needs!*"
        return response

    def _handle_general_query(self, message: str) -> str:
        """Handle general queries with welcome message."""
        response = "# Cooking Assistant\n\n"
        response += "Hello! I'm your AI cooking companion. I can help you with:\n\n"

        response += "**Recipes**\n"
        response += "- Search recipes by cuisine, ingredient, or dietary needs\n"
        response += "- Get step-by-step cooking instructions\n\n"

        response += "**Substitutions**\n"
        response += "- Find alternatives for ingredients you don't have\n\n"

        response += "**Conversions**\n"
        response += "- Convert between cups, grams, tablespoons, etc.\n\n"

        response += "**Timing**\n"
        response += "- Get cooking times for meats, eggs, and more\n\n"

        response += "**Nutrition**\n"
        response += "- Check calories and macros for recipes\n\n"

        response += "**Meal Planning**\n"
        response += "- Create weekly meal plans\n\n"

        response += "---\n"
        response += "**Try asking:**\n"
        response += '- *"Show me Italian recipes"*\n'
        response += '- *"How do I make kimchi fried rice?"*\n'
        response += '- *"What can I substitute for eggs?"*\n'
        response += '- *"How long should I bake chicken?"*\n'

        return response


def create_cooking_agent(
    llm: BaseChatModel | None = None, verbose: bool = False
) -> CookingAssistantAgent:
    """Factory function to create a cooking assistant."""
    return CookingAssistantAgent(llm=llm, verbose=verbose)
