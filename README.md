# AI Cooking Assistant

LangChain-powered intelligent cooking assistant that helps you discover recipes,
learn techniques, and master your kitchen.

## Live Demo

[**View Demo**](https://yoon-k.github.io/langchain-cooking-assistant/)

## Features

- **Recipe Search**: Find recipes by cuisine, ingredient, dietary requirements, or cooking time
- **Step-by-Step Instructions**: Detailed recipes with ingredients and cooking steps
- **Ingredient Substitutions**: Find alternatives when you're missing ingredients
- **Cooking Techniques**: Learn about sautéing, braising, roasting, and more
- **Unit Conversions**: Convert between cups, grams, tablespoons, and temperatures
- **Nutrition Calculator**: Get calorie and macro information for recipes
- **Meal Planning**: Generate weekly meal plans with variety
- **Cooking Times**: Get perfect timing for meats, eggs, and vegetables

## Quick Start

### Using `pip`

```bash
git clone https://github.com/yoon-k/langchain-cooking-assistant.git
cd langchain-cooking-assistant

python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Editable install with dev extras (pytest, ruff, mypy).
pip install -e ".[dev]"

# (optional) configure LLM keys
cp .env.example .env

# Start the dev server
python -m app.api
```

### Using `uv`

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev]"
python -m app.api
```

### Using `make`

```bash
make install
make dev
make test
make lint
```

## LLM Modes

The agent supports two execution modes and selects one automatically at startup:

| Mode | When it activates | Behavior |
|------|-------------------|----------|
| **LLM-backed** | `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` is set | LangChain LCEL `create_tool_calling_agent` + `AgentExecutor`, with the cooking tools bound to the model |
| **Keyword router (fallback)** | No API keys present, or `LLM_PROVIDER=none` | Pure-Python rule-based responses, no external calls. Useful for demos, tests, and CI |

You can force a provider with `LLM_PROVIDER=anthropic|openai|none`. Default
models are `claude-haiku-4-5-20251001` (Anthropic) and `gpt-4o-mini` (OpenAI),
overridable via `ANTHROPIC_MODEL` / `OPENAI_MODEL`.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | auto-detect | `anthropic`, `openai`, or `none` |
| `ANTHROPIC_API_KEY` | — | Anthropic API key for the Claude provider |
| `ANTHROPIC_MODEL` | `claude-haiku-4-5-20251001` | Override the Claude model id |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | Override the OpenAI model id |
| `PORT` | `5000` | Port for the Flask dev server / gunicorn |
| `FLASK_DEBUG` | `1` | Set to `0` to disable Werkzeug debug mode |

A ready-to-edit template lives at `.env.example`.

## Docker

```bash
# Build the image (multi-stage, runs as non-root, gunicorn 2 workers)
make docker-build

# Run with your local .env mounted
make docker-run

# ...or directly
docker build -t cooking-assistant:dev .
docker run --rm -p 5000:5000 --env-file .env cooking-assistant:dev
```

The image is based on `python:3.12-slim`, installs runtime deps from
`requirements.txt`, drops to a non-root `app` user, and serves the Flask app
via gunicorn.

## Architecture

```
langchain-cooking-assistant/
├── app/
│   ├── agents/
│   │   └── cooking_agent.py      # Main cooking assistant agent (LLM or fallback)
│   ├── tools/
│   │   └── cooking_tools.py      # LangChain cooking tools
│   ├── data/
│   │   └── recipes.py            # Recipe and ingredient database
│   └── api.py                    # Flask API endpoints
├── tests/
│   └── test_smoke.py             # Smoke tests (no API keys required)
├── docs/                         # Static GitHub Pages demo
├── Dockerfile                    # Production-ready image (gunicorn)
├── Makefile                      # install / dev / test / lint / docker
├── pyproject.toml                # PEP 621 metadata + ruff/pytest/mypy config
└── requirements.txt              # Pinned runtime dependencies
```

## LangChain Components

### Custom Tools
- `RecipeSearchTool`: Search recipes with multiple filters
- `RecipeDetailTool`: Get complete recipe with instructions
- `IngredientSubstituteTool`: Find ingredient alternatives
- `CookingTechniqueTool`: Learn cooking techniques
- `MealPlanTool`: Generate meal plans
- `UnitConversionTool`: Convert measurements
- `NutritionCalculatorTool`: Calculate recipe nutrition
- `TimerCalculatorTool`: Get cooking times

### Agent Architecture

```python
from app.agents.cooking_agent import create_cooking_agent

agent = create_cooking_agent()       # picks LLM if a key is present
print(agent.llm_enabled)             # True / False
print(agent.chat("Show me Italian recipes"))
print(agent.chat("How do I make Pasta Aglio e Olio?"))
print(agent.chat("What can I substitute for Parmesan?"))
```

### Recipe Database

```python
from app.data.recipes import RECIPES_DB, search_recipes, Cuisine, DietaryTag

italian_recipes = search_recipes(cuisine=Cuisine.ITALIAN)
quick_recipes   = search_recipes(max_time_min=30)
vegan_recipes   = search_recipes(dietary_tags=[DietaryTag.VEGAN])

recipe = RECIPES_DB["kimchi_fried_rice"]
print(recipe.instructions)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health probe (includes `llm_enabled`) |
| `/api/chat` | POST | Main chat endpoint |
| `/api/recipes` | GET | List all recipes |
| `/api/recipes/<id>` | GET | Get recipe details |
| `/api/recipes/search` | GET | Search with filters |
| `/api/techniques` | GET | List cooking techniques |
| `/api/cuisines` | GET | List available cuisines |
| `/api/dietary-tags` | GET | List dietary options |
| `/api/convert` | POST | Convert measurements |
| `/api/session/reset` | POST | Reset an agent session |

## Supported Cuisines

Korean, Japanese, Chinese, Italian, Mexican, American, French, Thai, Indian, Mediterranean.

## Dietary Options

Vegetarian, Vegan, Gluten-Free, Dairy-Free, Low-Carb, High-Protein, Keto, Paleo.

## Featured Recipes

Kimchi Fried Rice, Pasta Aglio e Olio, Chicken Stir-Fry, Tacos al Pastor,
Vegetable Curry, Pad Thai, Caesar Salad, Miso Soup, French Omelette, Greek Salad.

## Tech Stack

- **LangChain 0.3** (`langchain`, `langchain-core`, `langchain-community`)
- **Provider SDKs**: `langchain-anthropic`, `langchain-openai`
- **Flask 3.1** + `flask-cors`
- **Pydantic v2** for tool input schemas
- **Python 3.12** (PEP 585 / PEP 604 typing throughout)
- **Tooling**: `ruff`, `pytest`, `mypy`, `gunicorn`, Docker

## Contributing

Contributions are welcome! Feel free to add new recipes, cuisines, or features.
Please run `make lint` and `make test` before opening a PR.

## License

MIT License - feel free to use this project for learning and development.

---

## 한국어

LangChain 0.3 기반의 쿠킹 어시스턴트입니다. 레시피 검색, 재료 대체, 단위 변환,
주간 식단 등을 지원하며, API 키가 있으면 Anthropic Claude / OpenAI GPT 중 자동
선택해 LLM + 툴콜링으로 응답합니다. 키가 없으면 내장된 키워드 라우터로 폴백되어
외부 호출 없이도 동작합니다.

### 빠른 시작

```bash
git clone https://github.com/yoon-k/langchain-cooking-assistant.git
cd langchain-cooking-assistant

python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env   # 필요 시 API 키 입력
python -m app.api
```

`uv` 사용자는 `uv venv --python 3.12 && uv pip install -e ".[dev]"`도 OK.
간단히 쓰려면 `make install && make dev`.

### LLM 모드

| 조건 | 동작 |
|------|------|
| `ANTHROPIC_API_KEY`만 있음 | Claude (`claude-haiku-4-5-20251001`) + 툴콜링 |
| `OPENAI_API_KEY`만 있음 | OpenAI (`gpt-4o-mini`) + 툴콜링 |
| 둘 다 있음 | Anthropic 우선 |
| 둘 다 없음 | 키워드 라우터로 폴백 (외부 호출 없음) |

`LLM_PROVIDER=anthropic|openai|none`으로 강제 지정할 수 있고,
`ANTHROPIC_MODEL` / `OPENAI_MODEL`로 모델을 바꿀 수 있습니다.

### 환경변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `LLM_PROVIDER` | 자동 감지 | `anthropic` / `openai` / `none` |
| `ANTHROPIC_API_KEY` | — | Claude 사용 시 필수 |
| `OPENAI_API_KEY` | — | GPT 사용 시 필수 |
| `PORT` | `5000` | Flask / gunicorn 포트 |
| `FLASK_DEBUG` | `1` | 0이면 디버그 모드 OFF |

### Docker로 실행

```bash
make docker-build
make docker-run
```

이미지는 `python:3.12-slim` 기반, gunicorn 2 워커, 비루트 사용자로 실행됩니다.

### 테스트 & 린트

```bash
make test    # pytest 스모크 테스트
make lint    # ruff check
make format  # ruff format + auto-fix
```

테스트는 `LLM_PROVIDER=none`으로 실행되어 API 키 없이도 통과합니다.
