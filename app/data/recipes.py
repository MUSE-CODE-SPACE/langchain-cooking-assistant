"""
Recipe Database - Comprehensive recipe collection for the cooking assistant
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Cuisine(Enum):
    KOREAN = "korean"
    JAPANESE = "japanese"
    CHINESE = "chinese"
    ITALIAN = "italian"
    MEXICAN = "mexican"
    AMERICAN = "american"
    FRENCH = "french"
    THAI = "thai"
    INDIAN = "indian"
    MEDITERRANEAN = "mediterranean"


class DietaryTag(Enum):
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    LOW_CARB = "low_carb"
    HIGH_PROTEIN = "high_protein"
    KETO = "keto"
    PALEO = "paleo"


@dataclass
class Ingredient:
    """Represents a recipe ingredient."""
    name: str
    amount: str
    unit: str
    notes: str | None = None
    substitutes: list[str] = field(default_factory=list)


@dataclass
class NutritionInfo:
    """Nutritional information per serving."""
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float = 0
    sodium_mg: int = 0


@dataclass
class Recipe:
    """Represents a complete recipe."""
    id: str
    name: str
    description: str
    cuisine: Cuisine
    difficulty: Difficulty
    prep_time_min: int
    cook_time_min: int
    servings: int
    ingredients: list[Ingredient]
    instructions: list[str]
    tips: list[str]
    dietary_tags: list[DietaryTag] = field(default_factory=list)
    nutrition: NutritionInfo | None = None
    image_url: str | None = None


# =============================================================================
# RECIPE DATABASE
# =============================================================================

RECIPES_DB: dict[str, Recipe] = {
    "kimchi_fried_rice": Recipe(
        id="kimchi_fried_rice",
        name="Kimchi Fried Rice (Kimchi Bokkeumbap)",
        description="A quick and flavorful Korean fried rice dish made with aged kimchi, perfect for using up leftover rice.",
        cuisine=Cuisine.KOREAN,
        difficulty=Difficulty.EASY,
        prep_time_min=10,
        cook_time_min=15,
        servings=2,
        ingredients=[
            Ingredient("Cooked rice (day-old preferred)", "3", "cups", "Cold rice works best"),
            Ingredient("Kimchi (aged)", "1", "cup", "Chopped", ["Fresh cabbage with gochugaru"]),
            Ingredient("Kimchi juice", "2", "tbsp"),
            Ingredient("Pork belly or bacon", "100", "g", "Diced", ["Spam", "Tofu for vegetarian"]),
            Ingredient("Vegetable oil", "2", "tbsp"),
            Ingredient("Sesame oil", "1", "tbsp"),
            Ingredient("Soy sauce", "1", "tbsp"),
            Ingredient("Green onions", "2", "stalks", "Chopped"),
            Ingredient("Eggs", "2", "", "For topping"),
            Ingredient("Sesame seeds", "1", "tsp", "For garnish"),
        ],
        instructions=[
            "Heat vegetable oil in a large pan or wok over high heat.",
            "Add diced pork belly and cook until crispy, about 3-4 minutes.",
            "Add chopped kimchi and stir-fry for 2-3 minutes until slightly caramelized.",
            "Add the cold rice, breaking up any clumps with your spatula.",
            "Pour in kimchi juice and soy sauce, mixing everything well.",
            "Stir-fry for 3-4 minutes until rice is heated through and slightly crispy.",
            "Drizzle sesame oil and add green onions, tossing to combine.",
            "In a separate pan, fry eggs sunny-side up.",
            "Serve rice in bowls, top with fried egg and sesame seeds."
        ],
        tips=[
            "Day-old refrigerated rice works best as it's drier and won't get mushy",
            "Use well-aged, sour kimchi for the best flavor",
            "Add gochujang for extra spiciness",
            "Top with nori strips for extra umami"
        ],
        dietary_tags=[DietaryTag.HIGH_PROTEIN],
        nutrition=NutritionInfo(calories=520, protein_g=18, carbs_g=62, fat_g=22, fiber_g=3, sodium_mg=980)
    ),

    "pasta_aglio_olio": Recipe(
        id="pasta_aglio_olio",
        name="Pasta Aglio e Olio",
        description="Classic Italian pasta with garlic and olive oil - simple, quick, and incredibly delicious.",
        cuisine=Cuisine.ITALIAN,
        difficulty=Difficulty.EASY,
        prep_time_min=5,
        cook_time_min=15,
        servings=4,
        ingredients=[
            Ingredient("Spaghetti", "400", "g"),
            Ingredient("Extra virgin olive oil", "1/2", "cup"),
            Ingredient("Garlic", "8", "cloves", "Thinly sliced"),
            Ingredient("Red pepper flakes", "1/2", "tsp", "Adjust to taste"),
            Ingredient("Fresh parsley", "1/4", "cup", "Chopped"),
            Ingredient("Salt", "1", "tbsp", "For pasta water"),
            Ingredient("Parmesan cheese", "1/4", "cup", "Grated, optional", ["Nutritional yeast for vegan"]),
            Ingredient("Black pepper", "", "", "To taste"),
        ],
        instructions=[
            "Bring a large pot of salted water to boil and cook spaghetti according to package directions until al dente.",
            "While pasta cooks, heat olive oil in a large pan over medium-low heat.",
            "Add sliced garlic and cook slowly, stirring occasionally, until golden (not brown), about 4-5 minutes.",
            "Add red pepper flakes to the oil and remove from heat.",
            "Reserve 1 cup of pasta water before draining the spaghetti.",
            "Add drained pasta directly to the garlic oil pan.",
            "Toss well, adding pasta water a little at a time to create a light sauce.",
            "Add parsley and toss again.",
            "Serve immediately with Parmesan and black pepper."
        ],
        tips=[
            "Cook garlic low and slow - burnt garlic will make the dish bitter",
            "Save pasta water! The starch helps create a silky sauce",
            "Use good quality extra virgin olive oil as it's the star of this dish",
            "Adding a squeeze of lemon juice at the end brightens the flavors"
        ],
        dietary_tags=[DietaryTag.VEGETARIAN],
        nutrition=NutritionInfo(calories=450, protein_g=11, carbs_g=56, fat_g=20, fiber_g=3, sodium_mg=320)
    ),

    "chicken_stir_fry": Recipe(
        id="chicken_stir_fry",
        name="Easy Chicken Stir-Fry",
        description="A quick and healthy chicken stir-fry with colorful vegetables in a savory sauce.",
        cuisine=Cuisine.CHINESE,
        difficulty=Difficulty.EASY,
        prep_time_min=15,
        cook_time_min=10,
        servings=4,
        ingredients=[
            Ingredient("Chicken breast", "500", "g", "Sliced thin", ["Tofu", "Shrimp"]),
            Ingredient("Bell peppers", "2", "", "Mixed colors, sliced"),
            Ingredient("Broccoli florets", "2", "cups"),
            Ingredient("Carrots", "2", "", "Sliced diagonally"),
            Ingredient("Garlic", "3", "cloves", "Minced"),
            Ingredient("Ginger", "1", "tbsp", "Minced"),
            Ingredient("Soy sauce", "3", "tbsp"),
            Ingredient("Oyster sauce", "2", "tbsp", "", ["Hoisin sauce"]),
            Ingredient("Sesame oil", "1", "tbsp"),
            Ingredient("Cornstarch", "1", "tbsp"),
            Ingredient("Vegetable oil", "2", "tbsp"),
            Ingredient("Chicken broth", "1/4", "cup"),
        ],
        instructions=[
            "Mix soy sauce, oyster sauce, sesame oil, cornstarch, and chicken broth in a bowl for the sauce.",
            "Heat 1 tbsp oil in a wok or large pan over high heat.",
            "Add chicken and stir-fry until cooked through, about 4-5 minutes. Remove and set aside.",
            "Add remaining oil to the pan. Stir-fry garlic and ginger for 30 seconds.",
            "Add carrots and broccoli, stir-fry for 2 minutes.",
            "Add bell peppers, stir-fry for another 2 minutes.",
            "Return chicken to the pan.",
            "Pour sauce over everything and toss until sauce thickens and coats all ingredients.",
            "Serve immediately over steamed rice."
        ],
        tips=[
            "Cut all ingredients to similar sizes for even cooking",
            "Don't overcrowd the pan - cook in batches if needed",
            "High heat is key for that restaurant-style sear",
            "Prep everything before you start cooking - stir-frying is fast!"
        ],
        dietary_tags=[DietaryTag.HIGH_PROTEIN, DietaryTag.DAIRY_FREE],
        nutrition=NutritionInfo(calories=320, protein_g=35, carbs_g=18, fat_g=12, fiber_g=4, sodium_mg=890)
    ),

    "tacos_al_pastor": Recipe(
        id="tacos_al_pastor",
        name="Tacos al Pastor",
        description="Traditional Mexican tacos with marinated pork, pineapple, and fresh toppings.",
        cuisine=Cuisine.MEXICAN,
        difficulty=Difficulty.MEDIUM,
        prep_time_min=30,
        cook_time_min=20,
        servings=6,
        ingredients=[
            Ingredient("Pork shoulder", "700", "g", "Sliced thin"),
            Ingredient("Dried guajillo chiles", "4", "", "Stemmed and seeded"),
            Ingredient("Achiote paste", "2", "tbsp"),
            Ingredient("Pineapple", "1/2", "", "Cubed"),
            Ingredient("White onion", "1", "", "Quartered"),
            Ingredient("Garlic", "4", "cloves"),
            Ingredient("Apple cider vinegar", "2", "tbsp"),
            Ingredient("Cumin", "1", "tsp"),
            Ingredient("Oregano", "1", "tsp"),
            Ingredient("Corn tortillas", "12", "", "Small"),
            Ingredient("Fresh cilantro", "1/2", "cup", "Chopped"),
            Ingredient("White onion", "1/2", "", "Diced, for topping"),
            Ingredient("Lime wedges", "6", ""),
        ],
        instructions=[
            "Rehydrate guajillo chiles in hot water for 15 minutes.",
            "Blend soaked chiles with achiote paste, 1/4 onion, garlic, vinegar, cumin, oregano, and 1/2 cup water until smooth.",
            "Marinate sliced pork in the chile mixture for at least 2 hours (overnight is best).",
            "Heat a large skillet or grill pan over high heat.",
            "Cook marinated pork in batches until charred and cooked through, about 3-4 minutes per side.",
            "In the same pan, quickly sear pineapple cubes until caramelized.",
            "Chop cooked pork and pineapple together.",
            "Warm tortillas on a dry pan.",
            "Serve pork and pineapple on tortillas with cilantro, diced onion, and lime."
        ],
        tips=[
            "Freeze pork slightly for easier thin slicing",
            "Marinate overnight for the most flavorful tacos",
            "Char the pineapple for authentic flavor",
            "Double the corn tortillas for structural integrity"
        ],
        dietary_tags=[DietaryTag.DAIRY_FREE, DietaryTag.GLUTEN_FREE],
        nutrition=NutritionInfo(calories=380, protein_g=28, carbs_g=32, fat_g=15, fiber_g=4, sodium_mg=420)
    ),

    "vegetable_curry": Recipe(
        id="vegetable_curry",
        name="Vegetable Curry",
        description="A rich and aromatic vegetable curry with coconut milk, perfect for a comforting meal.",
        cuisine=Cuisine.INDIAN,
        difficulty=Difficulty.MEDIUM,
        prep_time_min=20,
        cook_time_min=30,
        servings=4,
        ingredients=[
            Ingredient("Chickpeas", "1", "can", "Drained", ["Tofu cubes"]),
            Ingredient("Cauliflower", "2", "cups", "Cut into florets"),
            Ingredient("Potatoes", "2", "medium", "Cubed"),
            Ingredient("Spinach", "2", "cups", "Fresh"),
            Ingredient("Coconut milk", "400", "ml"),
            Ingredient("Diced tomatoes", "1", "can"),
            Ingredient("Onion", "1", "large", "Diced"),
            Ingredient("Garlic", "4", "cloves", "Minced"),
            Ingredient("Ginger", "2", "tbsp", "Grated"),
            Ingredient("Curry powder", "2", "tbsp"),
            Ingredient("Garam masala", "1", "tsp"),
            Ingredient("Turmeric", "1", "tsp"),
            Ingredient("Cumin", "1", "tsp"),
            Ingredient("Vegetable oil", "2", "tbsp"),
            Ingredient("Salt", "", "", "To taste"),
        ],
        instructions=[
            "Heat oil in a large pot over medium heat. Add onion and cook until softened, about 5 minutes.",
            "Add garlic and ginger, cook for 1 minute until fragrant.",
            "Add curry powder, garam masala, turmeric, and cumin. Stir for 30 seconds.",
            "Add potatoes and cauliflower, stirring to coat with spices.",
            "Pour in diced tomatoes and coconut milk. Bring to a simmer.",
            "Cover and cook for 15-20 minutes until vegetables are tender.",
            "Add chickpeas and spinach, cook for another 5 minutes.",
            "Season with salt to taste.",
            "Serve over basmati rice with naan bread on the side."
        ],
        tips=[
            "Toast the spices briefly in oil to bloom their flavors",
            "Add a splash of lime juice at the end for brightness",
            "Adjust consistency with vegetable broth if too thick",
            "Top with fresh cilantro and a dollop of yogurt"
        ],
        dietary_tags=[DietaryTag.VEGAN, DietaryTag.VEGETARIAN, DietaryTag.GLUTEN_FREE, DietaryTag.DAIRY_FREE],
        nutrition=NutritionInfo(calories=380, protein_g=12, carbs_g=42, fat_g=20, fiber_g=9, sodium_mg=580)
    ),

    "pad_thai": Recipe(
        id="pad_thai",
        name="Pad Thai",
        description="Thailand's famous stir-fried noodle dish with a perfect balance of sweet, sour, and savory flavors.",
        cuisine=Cuisine.THAI,
        difficulty=Difficulty.MEDIUM,
        prep_time_min=20,
        cook_time_min=15,
        servings=4,
        ingredients=[
            Ingredient("Rice noodles (flat)", "250", "g"),
            Ingredient("Shrimp or chicken", "200", "g", "", ["Tofu for vegetarian"]),
            Ingredient("Eggs", "2", ""),
            Ingredient("Bean sprouts", "1", "cup"),
            Ingredient("Green onions", "3", "stalks", "Cut into 2-inch pieces"),
            Ingredient("Garlic", "3", "cloves", "Minced"),
            Ingredient("Tamarind paste", "2", "tbsp"),
            Ingredient("Fish sauce", "2", "tbsp", "", ["Soy sauce for vegetarian"]),
            Ingredient("Palm sugar", "2", "tbsp", "", ["Brown sugar"]),
            Ingredient("Rice vinegar", "1", "tbsp"),
            Ingredient("Chili flakes", "1/2", "tsp"),
            Ingredient("Vegetable oil", "3", "tbsp"),
            Ingredient("Crushed peanuts", "1/4", "cup"),
            Ingredient("Lime wedges", "4", ""),
            Ingredient("Fresh cilantro", "", "", "For garnish"),
        ],
        instructions=[
            "Soak rice noodles in warm water for 30-40 minutes until pliable. Drain.",
            "Mix tamarind paste, fish sauce, palm sugar, and rice vinegar for the sauce.",
            "Heat 1 tbsp oil in a wok over high heat. Scramble eggs and set aside.",
            "Add remaining oil. Stir-fry protein until cooked. Set aside.",
            "Add garlic to the wok, fry for 30 seconds.",
            "Add drained noodles and the sauce. Toss continuously for 2-3 minutes.",
            "Return eggs and protein to the wok.",
            "Add bean sprouts and green onions, toss for 1 minute.",
            "Serve topped with peanuts, cilantro, and lime wedges."
        ],
        tips=[
            "Don't over-soak noodles - they should be pliable but firm",
            "High heat is essential for authentic wok hei flavor",
            "Cook in batches if making large quantities",
            "Serve immediately - pad thai doesn't keep well"
        ],
        dietary_tags=[DietaryTag.DAIRY_FREE],
        nutrition=NutritionInfo(calories=420, protein_g=22, carbs_g=48, fat_g=16, fiber_g=3, sodium_mg=1100)
    ),

    "caesar_salad": Recipe(
        id="caesar_salad",
        name="Classic Caesar Salad",
        description="Crisp romaine lettuce with creamy Caesar dressing, crunchy croutons, and Parmesan.",
        cuisine=Cuisine.AMERICAN,
        difficulty=Difficulty.EASY,
        prep_time_min=15,
        cook_time_min=10,
        servings=4,
        ingredients=[
            Ingredient("Romaine lettuce", "2", "heads", "Chopped"),
            Ingredient("Egg yolks", "2", "", "Pasteurized"),
            Ingredient("Garlic", "2", "cloves", "Minced"),
            Ingredient("Anchovy fillets", "3", "", "", ["1 tbsp anchovy paste"]),
            Ingredient("Dijon mustard", "1", "tsp"),
            Ingredient("Lemon juice", "2", "tbsp"),
            Ingredient("Worcestershire sauce", "1", "tsp"),
            Ingredient("Olive oil", "1/2", "cup"),
            Ingredient("Parmesan cheese", "1/2", "cup", "Freshly grated"),
            Ingredient("Bread", "4", "slices", "Cubed for croutons"),
            Ingredient("Butter", "2", "tbsp"),
            Ingredient("Black pepper", "", "", "To taste"),
        ],
        instructions=[
            "For croutons: Cube bread, toss with melted butter. Bake at 375°F (190°C) for 10-12 minutes until golden.",
            "For dressing: Mash anchovies and garlic into a paste.",
            "Whisk in egg yolks, mustard, lemon juice, and Worcestershire sauce.",
            "Slowly drizzle in olive oil while whisking to emulsify.",
            "Stir in half the Parmesan cheese.",
            "In a large bowl, toss romaine with dressing.",
            "Add croutons and toss again.",
            "Top with remaining Parmesan and fresh black pepper.",
            "Serve immediately."
        ],
        tips=[
            "Use pasteurized eggs for food safety",
            "Make dressing in advance - it keeps well refrigerated",
            "Tear lettuce by hand for better texture",
            "Add grilled chicken for a complete meal"
        ],
        dietary_tags=[DietaryTag.VEGETARIAN],
        nutrition=NutritionInfo(calories=380, protein_g=12, carbs_g=18, fat_g=30, fiber_g=4, sodium_mg=680)
    ),

    "miso_soup": Recipe(
        id="miso_soup",
        name="Miso Soup",
        description="Traditional Japanese soup with miso paste, tofu, and wakame seaweed.",
        cuisine=Cuisine.JAPANESE,
        difficulty=Difficulty.EASY,
        prep_time_min=10,
        cook_time_min=10,
        servings=4,
        ingredients=[
            Ingredient("Dashi stock", "4", "cups", "", ["4 cups water + 1 tbsp dashi powder"]),
            Ingredient("White miso paste", "3", "tbsp"),
            Ingredient("Silken tofu", "200", "g", "Cubed"),
            Ingredient("Dried wakame seaweed", "2", "tbsp"),
            Ingredient("Green onions", "2", "stalks", "Thinly sliced"),
        ],
        instructions=[
            "Rehydrate wakame in water for 5 minutes, then drain.",
            "Bring dashi stock to a gentle simmer in a pot.",
            "Add tofu cubes and wakame, simmer for 2 minutes.",
            "Remove pot from heat.",
            "Place miso paste in a ladle, lower into broth, and stir to dissolve. Do not boil after adding miso.",
            "Serve in bowls topped with green onions."
        ],
        tips=[
            "Never boil miso - it destroys the flavor and probiotics",
            "Use a combination of white and red miso for depth",
            "Add other ingredients like mushrooms, clams, or vegetables",
            "Homemade dashi makes a significant difference"
        ],
        dietary_tags=[DietaryTag.VEGETARIAN, DietaryTag.VEGAN, DietaryTag.LOW_CARB],
        nutrition=NutritionInfo(calories=85, protein_g=6, carbs_g=8, fat_g=3, fiber_g=2, sodium_mg=720)
    ),

    "french_omelette": Recipe(
        id="french_omelette",
        name="Classic French Omelette",
        description="A perfectly cooked, silky French-style omelette with soft, creamy curds.",
        cuisine=Cuisine.FRENCH,
        difficulty=Difficulty.MEDIUM,
        prep_time_min=5,
        cook_time_min=5,
        servings=1,
        ingredients=[
            Ingredient("Eggs", "3", "", "Room temperature"),
            Ingredient("Butter", "1", "tbsp"),
            Ingredient("Salt", "1/8", "tsp"),
            Ingredient("White pepper", "", "", "Pinch"),
            Ingredient("Chives", "1", "tbsp", "Finely chopped, optional"),
            Ingredient("Gruyere cheese", "2", "tbsp", "Grated, optional"),
        ],
        instructions=[
            "Beat eggs with salt and pepper until just combined - don't overbeat.",
            "Heat an 8-inch non-stick pan over medium-high heat.",
            "Add butter and swirl to coat the pan as it melts and foams.",
            "When foam subsides, add eggs.",
            "Immediately stir eggs with a fork or chopsticks while shaking the pan.",
            "When eggs are almost set but still creamy, stop stirring.",
            "Add cheese and chives if using to the center.",
            "Tilt pan and use a spatula to fold the omelette in thirds onto a plate.",
            "Serve immediately with a small pat of butter on top."
        ],
        tips=[
            "Room temperature eggs cook more evenly",
            "Medium-high heat and constant movement create the signature curds",
            "The whole process should take under 2 minutes",
            "Practice makes perfect - don't be discouraged by first attempts"
        ],
        dietary_tags=[DietaryTag.VEGETARIAN, DietaryTag.LOW_CARB, DietaryTag.KETO, DietaryTag.GLUTEN_FREE],
        nutrition=NutritionInfo(calories=310, protein_g=18, carbs_g=1, fat_g=26, fiber_g=0, sodium_mg=450)
    ),

    "greek_salad": Recipe(
        id="greek_salad",
        name="Greek Salad (Horiatiki)",
        description="Fresh Mediterranean salad with tomatoes, cucumbers, olives, and feta cheese.",
        cuisine=Cuisine.MEDITERRANEAN,
        difficulty=Difficulty.EASY,
        prep_time_min=15,
        cook_time_min=0,
        servings=4,
        ingredients=[
            Ingredient("Tomatoes", "4", "large", "Cut into wedges"),
            Ingredient("Cucumber", "1", "large", "Sliced"),
            Ingredient("Red onion", "1", "small", "Thinly sliced"),
            Ingredient("Green bell pepper", "1", "", "Sliced"),
            Ingredient("Kalamata olives", "1/2", "cup"),
            Ingredient("Feta cheese", "200", "g", "Block, not crumbled"),
            Ingredient("Extra virgin olive oil", "4", "tbsp"),
            Ingredient("Red wine vinegar", "1", "tbsp"),
            Ingredient("Dried oregano", "1", "tsp"),
            Ingredient("Salt", "", "", "To taste"),
        ],
        instructions=[
            "Cut tomatoes into large wedges and place in a bowl.",
            "Add sliced cucumber, red onion, and bell pepper.",
            "Add olives to the bowl.",
            "Season with salt and dried oregano.",
            "Drizzle with olive oil and vinegar, gently toss.",
            "Place the block of feta cheese on top.",
            "Drizzle more olive oil over the feta.",
            "Serve immediately with crusty bread."
        ],
        tips=[
            "Use ripe, flavorful tomatoes - they're the star",
            "Traditional Greek salad uses feta as a whole block, not crumbled",
            "Don't add lettuce - it's not authentic",
            "Let it sit for 10 minutes for flavors to meld"
        ],
        dietary_tags=[DietaryTag.VEGETARIAN, DietaryTag.GLUTEN_FREE, DietaryTag.LOW_CARB],
        nutrition=NutritionInfo(calories=290, protein_g=9, carbs_g=12, fat_g=24, fiber_g=3, sodium_mg=820)
    ),
}


# =============================================================================
# INGREDIENT DATABASE
# =============================================================================

INGREDIENTS_DB: dict[str, dict] = {
    "chicken_breast": {
        "name": "Chicken Breast",
        "category": "protein",
        "storage": "Refrigerate raw up to 2 days, freeze up to 9 months",
        "substitutes": ["Turkey breast", "Pork tenderloin", "Tofu"],
        "nutrition_per_100g": {"calories": 165, "protein": 31, "fat": 3.6, "carbs": 0}
    },
    "olive_oil": {
        "name": "Olive Oil",
        "category": "oil",
        "storage": "Store in cool, dark place for up to 2 years",
        "substitutes": ["Avocado oil", "Canola oil", "Butter"],
        "nutrition_per_100g": {"calories": 884, "protein": 0, "fat": 100, "carbs": 0}
    },
    "garlic": {
        "name": "Garlic",
        "category": "vegetable",
        "storage": "Store in cool, dry place for up to 3 months",
        "substitutes": ["Garlic powder (1/4 tsp = 1 clove)", "Shallots"],
        "nutrition_per_100g": {"calories": 149, "protein": 6.4, "fat": 0.5, "carbs": 33}
    },
    "rice": {
        "name": "Rice",
        "category": "grain",
        "storage": "Store in airtight container for up to 2 years",
        "substitutes": ["Quinoa", "Cauliflower rice", "Couscous"],
        "nutrition_per_100g": {"calories": 130, "protein": 2.7, "fat": 0.3, "carbs": 28}
    },
    "eggs": {
        "name": "Eggs",
        "category": "protein",
        "storage": "Refrigerate for up to 5 weeks",
        "substitutes": ["Flax egg (1 tbsp flax + 3 tbsp water)", "Chia egg", "Aquafaba"],
        "nutrition_per_100g": {"calories": 155, "protein": 13, "fat": 11, "carbs": 1.1}
    },
    "soy_sauce": {
        "name": "Soy Sauce",
        "category": "condiment",
        "storage": "Refrigerate after opening for up to 2 years",
        "substitutes": ["Tamari (gluten-free)", "Coconut aminos", "Worcestershire sauce"],
        "nutrition_per_100g": {"calories": 53, "protein": 8, "fat": 0, "carbs": 5}
    },
    "butter": {
        "name": "Butter",
        "category": "dairy",
        "storage": "Refrigerate for up to 1 month, freeze for up to 6 months",
        "substitutes": ["Margarine", "Coconut oil", "Olive oil (for cooking)"],
        "nutrition_per_100g": {"calories": 717, "protein": 0.9, "fat": 81, "carbs": 0.1}
    },
    "tomatoes": {
        "name": "Tomatoes",
        "category": "vegetable",
        "storage": "Room temperature until ripe, then refrigerate up to 1 week",
        "substitutes": ["Canned tomatoes", "Sun-dried tomatoes", "Red bell pepper"],
        "nutrition_per_100g": {"calories": 18, "protein": 0.9, "fat": 0.2, "carbs": 3.9}
    }
}


# =============================================================================
# COOKING TECHNIQUES
# =============================================================================

TECHNIQUES_DB: dict[str, dict] = {
    "saute": {
        "name": "Sauté",
        "description": "Cooking food quickly in a small amount of fat over high heat",
        "best_for": ["Vegetables", "Thin cuts of meat", "Shrimp"],
        "tips": [
            "Use a wide pan to avoid overcrowding",
            "Have all ingredients prepped before you start",
            "Keep the food moving",
            "Use high smoke-point oils"
        ]
    },
    "braise": {
        "name": "Braise",
        "description": "Slow-cooking in liquid after initial browning",
        "best_for": ["Tough cuts of meat", "Root vegetables", "Beans"],
        "tips": [
            "Brown the meat well first",
            "Use flavorful liquid like wine or stock",
            "Keep liquid at a gentle simmer",
            "Low and slow is the key"
        ]
    },
    "roast": {
        "name": "Roast",
        "description": "Cooking with dry heat in an oven",
        "best_for": ["Large cuts of meat", "Whole vegetables", "Poultry"],
        "tips": [
            "Preheat oven thoroughly",
            "Use a meat thermometer",
            "Let meat rest before carving",
            "Baste occasionally for moisture"
        ]
    },
    "stir_fry": {
        "name": "Stir-Fry",
        "description": "Quick cooking over very high heat with constant stirring",
        "best_for": ["Vegetables", "Thin sliced meats", "Noodles"],
        "tips": [
            "Use a wok if possible",
            "Cut ingredients uniformly",
            "Cook in batches to maintain heat",
            "Have sauce ready before cooking"
        ]
    },
    "poach": {
        "name": "Poach",
        "description": "Gently cooking in simmering liquid",
        "best_for": ["Eggs", "Fish", "Chicken", "Fruit"],
        "tips": [
            "Keep liquid just below boiling",
            "Use flavorful poaching liquid",
            "Don't overcook",
            "A splash of vinegar helps eggs hold shape"
        ]
    }
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_recipe(recipe_id: str) -> Recipe | None:
    """Get a recipe by ID."""
    return RECIPES_DB.get(recipe_id)


def search_recipes(
    query: str = "",
    cuisine: Cuisine | None = None,
    difficulty: Difficulty | None = None,
    dietary_tags: list[DietaryTag] | None = None,
    max_time_min: int | None = None,
) -> list[Recipe]:
    """Search recipes by various criteria."""
    results = []

    for recipe in RECIPES_DB.values():
        # Filter by query
        if query:
            query_lower = query.lower()
            if not (query_lower in recipe.name.lower() or
                    query_lower in recipe.description.lower() or
                    any(query_lower in ing.name.lower() for ing in recipe.ingredients)):
                continue

        # Filter by cuisine
        if cuisine and recipe.cuisine != cuisine:
            continue

        # Filter by difficulty
        if difficulty and recipe.difficulty != difficulty:
            continue

        # Filter by dietary tags
        if dietary_tags and not all(
            tag in recipe.dietary_tags for tag in dietary_tags
        ):
            continue

        # Filter by time
        if max_time_min:
            total_time = recipe.prep_time_min + recipe.cook_time_min
            if total_time > max_time_min:
                continue

        results.append(recipe)

    return results


def get_recipes_by_ingredient(ingredient: str) -> list[Recipe]:
    """Find recipes containing a specific ingredient."""
    ingredient_lower = ingredient.lower()
    results = []

    for recipe in RECIPES_DB.values():
        for ing in recipe.ingredients:
            if ingredient_lower in ing.name.lower():
                results.append(recipe)
                break

    return results


def get_ingredient_info(ingredient_name: str) -> dict | None:
    """Get information about an ingredient."""
    ingredient_key = ingredient_name.lower().replace(" ", "_")
    return INGREDIENTS_DB.get(ingredient_key)


def get_technique_info(technique_name: str) -> dict | None:
    """Get information about a cooking technique."""
    technique_key = technique_name.lower().replace(" ", "_").replace("-", "_")
    return TECHNIQUES_DB.get(technique_key)


def get_all_cuisines() -> list[str]:
    """Get list of all available cuisines."""
    return [c.value for c in Cuisine]


def get_all_dietary_tags() -> list[str]:
    """Get list of all dietary tags."""
    return [t.value for t in DietaryTag]
