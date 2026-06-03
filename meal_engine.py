import random
import json
import os
from calculator import calculate_macros

# Load recipes
def load_recipes():
    path = os.path.join(os.path.dirname(__file__), "data", "recipes.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# Ingredient categories for shopping list
INGREDIENT_CATEGORIES = {
    "主食": ["大米", "小米", "面粉", "红薯", "紫薯", "玉米", "酵母",
             "面条（干）", "即食燕麦片"],
    "肉类": ["猪里脊肉", "猪肋排", "五花肉", "猪肉末", "牛腩", "牛里脊", "鸡胸肉", "鸡腿肉",
             "鸡翅中", "鸡腿块", "鸭块"],
    "水产": ["鲈鱼", "基围虾", "虾仁", "虾皮", "巴沙鱼"],
    "蛋奶豆": ["鸡蛋", "嫩豆腐", "老豆腐", "南豆腐", "牛奶", "原味酸奶", "黄豆", "豆腐皮"],
    "蔬菜": ["青椒", "红椒", "尖椒", "干辣椒", "番茄", "黄瓜", "胡萝卜", "土豆", "西兰花", "菜花",
             "生菜", "油菜", "白菜", "卷心菜", "空心菜", "四季豆", "豆芽", "茄子", "冬瓜",
             "洋葱", "大葱", "葱", "葱花", "蒜苗", "蒜", "姜", "木耳", "干香菇", "香菇",
             "笋", "菠菜", "芹菜", "香菜", "金针菇", "青豆", "香蕉"],
    "调料": ["盐", "糖", "酱油", "醋", "料酒", "蚝油", "豆瓣酱", "番茄酱", "豆豉", "泡椒",
             "花椒", "花椒粉", "胡椒粉", "孜然粉", "辣椒粉", "八角", "香油", "食用油",
             "蒸鱼豉油", "淀粉", "椒盐", "可乐", "咖喱粉", "椰浆", "火锅底料", "黄豆酱"],
    "熟食成品": ["豆浆（成品）", "馒头（成品）", "速冻馄饨", "火锅丸子",
                "全麦面包", "包子（成品）", "火腿片"],
    "其他": ["花生米", "花生酱", "混合坚果", "紫菜", "水"]
}

CATEGORY_ORDER = ["主食", "肉类", "水产", "蛋奶豆", "蔬菜", "熟食成品", "调料", "其他"]

CATEGORY_ICONS = {
    "主食": "🍚", "肉类": "🥩", "水产": "🐟", "蛋奶豆": "🥚",
    "蔬菜": "🥬", "熟食成品": "🏪", "调料": "🧂", "其他": "📦"
}


def categorize_ingredients(shopping_list):
    """Group ingredients by category for a cleaner shopping list."""
    categorized = {}
    uncategorized = []

    for name, amount in shopping_list.items():
        found = False
        for cat, keywords in INGREDIENT_CATEGORIES.items():
            if name in keywords:
                if cat not in categorized:
                    categorized[cat] = []
                categorized[cat].append({"name": name, "amount_g": amount})
                found = True
                break
        if not found:
            uncategorized.append({"name": name, "amount_g": amount})

    # Sort categories
    result = []
    for cat in CATEGORY_ORDER:
        if cat in categorized:
            # Sort items within category by amount desc
            items = sorted(categorized[cat], key=lambda x: x["amount_g"], reverse=True)
            result.append({
                "category": cat,
                "icon": CATEGORY_ICONS.get(cat, ""),
                "ingredients": items
            })

    if uncategorized:
        result.append({
            "category": "其他",
            "icon": "📦",
            "ingredients": sorted(uncategorized, key=lambda x: x["amount_g"], reverse=True)
        })

    return result


def filter_by_preferences(recipes, tastes, restrictions):
    """Filter recipes based on user taste preferences and dietary restrictions."""
    result = []
    for r in recipes:
        # Check allergens / restrictions
        if restrictions:
            blocked = False
            for allergen in r.get("allergens", []):
                if allergen in restrictions:
                    blocked = True
                    break
            if blocked:
                continue

        # Check taste preferences (if user selected specific tastes, not "all")
        if tastes and "all" not in tastes:
            # Recipe should match at least one preferred taste
            recipe_tastes = r.get("taste", [])
            if not any(t in recipe_tastes for t in tastes):
                continue

        result.append(r)
    return result


def get_pool(recipes, meal_type):
    """Get recipe pool for a specific meal type."""
    if meal_type == "breakfast":
        return [r for r in recipes if r["meal_type"] == "breakfast"]
    elif meal_type == "lunch_dinner":
        return [r for r in recipes if r["meal_type"] in ("lunch_dinner",)]
    elif meal_type == "snack":
        return [r for r in recipes if r["meal_type"] == "snack"]
    return recipes


def select_breakfast(pool, target_calories, used_ids):
    """Select breakfast items to match calorie target."""
    available = [r for r in pool if r["id"] not in used_ids]
    if not available:
        available = pool

    # Try to find best match
    best = None
    best_diff = float("inf")
    for r in available:
        diff = abs(r["nutrition"]["calories"] - target_calories)
        if diff < best_diff:
            best_diff = diff
            best = r

    if best:
        # Scale portions if needed
        scale = target_calories / max(best["nutrition"]["calories"], 1)
        scale = max(0.5, min(2.0, scale))  # Limit scaling between 0.5x and 2x
        scaled_ingredients = []
        for ing in best["ingredients"]:
            scaled_ingredients.append({
                "name": ing["name"],
                "amount_g": round(ing["amount_g"] * scale)
            })
        scaled_nutrition = {
            "calories": round(best["nutrition"]["calories"] * scale),
            "protein_g": round(best["nutrition"]["protein_g"] * scale, 1),
            "fat_g": round(best["nutrition"]["fat_g"] * scale, 1),
            "carbs_g": round(best["nutrition"]["carbs_g"] * scale, 1)
        }
        return {
            "recipe": best,
            "scale": round(scale, 2),
            "ingredients": scaled_ingredients,
            "nutrition": scaled_nutrition
        }
    return None


def select_staple(pool, target_calories, used_ids):
    """Select a staple food and adjust portion to match target carbs."""
    available = [r for r in pool if r["id"] not in used_ids and r["category"] == "staple"]
    if not available:
        available = [r for r in pool if r["category"] == "staple"]

    if not available:
        return None

    # Pick first available staple
    staple = available[0]

    # Scale to match target calories
    scale = target_calories / max(staple["nutrition"]["calories"], 1)
    scale = max(0.5, min(1.5, scale))
    scale = round(scale * 20) / 20  # Round to nearest 0.05

    scaled_ingredients = []
    for ing in staple["ingredients"]:
        scaled_ingredients.append({
            "name": ing["name"],
            "amount_g": round(ing["amount_g"] * scale)
        })

    scaled_nutrition = {
        "calories": round(staple["nutrition"]["calories"] * scale),
        "protein_g": round(staple["nutrition"]["protein_g"] * scale, 1),
        "fat_g": round(staple["nutrition"]["fat_g"] * scale, 1),
        "carbs_g": round(staple["nutrition"]["carbs_g"] * scale, 1)
    }

    return {
        "recipe": staple,
        "scale": round(scale, 2),
        "ingredients": scaled_ingredients,
        "nutrition": scaled_nutrition
    }


def select_dish(pool, target_calories, used_ids, category=None, prefer_cheat=False):
    """Select a dish to match target calories."""
    if prefer_cheat:
        available = [r for r in pool if r.get("category") == "cheat" and r["id"] not in used_ids]
    else:
        available = [r for r in pool if r["id"] not in used_ids]

    if category:
        available = [r for r in available if r.get("category") == category]

    if not available:
        available = [r for r in pool if r["id"] not in used_ids]
    if not available:
        available = pool

    if not available:
        return None

    best = None
    best_diff = float("inf")
    for r in available:
        diff = abs(r["nutrition"]["calories"] - target_calories)
        if diff < best_diff:
            best_diff = diff
            best = r

    if best:
        scale = target_calories / max(best["nutrition"]["calories"], 1)
        scale = max(0.6, min(1.5, scale))
        scale = round(scale * 20) / 20

        scaled_ingredients = []
        for ing in best["ingredients"]:
            scaled_ingredients.append({
                "name": ing["name"],
                "amount_g": round(ing["amount_g"] * scale)
            })

        scaled_nutrition = {
            "calories": round(best["nutrition"]["calories"] * scale),
            "protein_g": round(best["nutrition"]["protein_g"] * scale, 1),
            "fat_g": round(best["nutrition"]["fat_g"] * scale, 1),
            "carbs_g": round(best["nutrition"]["carbs_g"] * scale, 1)
        }

        return {
            "recipe": best,
            "scale": round(scale, 2),
            "ingredients": scaled_ingredients,
            "nutrition": scaled_nutrition
        }
    return None


def generate_meal(target_calories, all_recipes, used_ids, meal_type, is_cheat=False, simple_mode=False):
    """Generate a single meal (set of dishes) matching the calorie target."""
    used = set(used_ids)
    meal_items = []

    if meal_type == "breakfast":
        breakfast_pool = [r for r in all_recipes if r["meal_type"] == "breakfast"]
        item = select_breakfast(breakfast_pool, target_calories, used)
        if item:
            meal_items.append(item)
            used.add(item["recipe"]["id"])

    elif meal_type in ("lunch", "dinner"):
        staple_pool = [r for r in all_recipes if r["category"] == "staple"]
        meat_pool = [r for r in all_recipes if r["category"] in ("meat", "cheat")]
        veg_pool = [r for r in all_recipes if r["category"] == "veg"]
        soup_pool = [r for r in all_recipes if r["category"] == "soup"]

        if simple_mode:
            # Simple: randomly alternate between "combo dish" and "rice + one dish"
            # Combo dishes = 面/盖饭/麻辣烫/馄饨 etc (饭菜合一)
            # Rice mode = 白米饭 + one main dish
            combo_pool = [r for r in all_recipes if r.get("category") == "combo"]
            rice_only = [r for r in staple_pool if r["id"] == "st01"]  # Only 白米饭

            # Alternate based on day/meal to ensure variety
            use_combo = (len(used_ids) // 2) % 2 == 0 and len(combo_pool) > 0

            if use_combo and combo_pool:
                # One-pot meal: 面/盖饭/麻辣烫 etc
                item = select_dish(combo_pool, target_calories, used, prefer_cheat=is_cheat)
                if item:
                    meal_items.append(item)
                    used.add(item["recipe"]["id"])
            else:
                # 白米饭 + one dish
                staple_cal = round(target_calories * 0.45)
                main_cal = round(target_calories * 0.55)

                item = select_staple(rice_only, staple_cal, used)
                if item:
                    meal_items.append(item)
                    used.add(item["recipe"]["id"])

                # One dish from meat+veg pool
                combined_pool = meat_pool + veg_pool
                item = select_dish(combined_pool, main_cal, used, prefer_cheat=is_cheat)
                if item:
                    meal_items.append(item)
                    used.add(item["recipe"]["id"])
        else:
            # Expert: staple ~40%, meat ~35%, veg ~15%, soup ~10%
            staple_cal = round(target_calories * 0.40)
            meat_cal = round(target_calories * 0.35)
            veg_cal = round(target_calories * 0.15)
            soup_cal = round(target_calories * 0.10)

            # Staple
            item = select_staple(staple_pool, staple_cal, used)
            if item:
                meal_items.append(item)
                used.add(item["recipe"]["id"])

            # Meat dish (or cheat dish)
            item = select_dish(meat_pool, meat_cal, used, prefer_cheat=is_cheat)
            if item:
                meal_items.append(item)
                used.add(item["recipe"]["id"])

            # Veg dish
            item = select_dish(veg_pool, veg_cal, used, category="veg")
            if item:
                meal_items.append(item)
                used.add(item["recipe"]["id"])

            # Soup (optional, only if there's calorie room)
            if soup_cal > 40:
                item = select_dish(soup_pool, soup_cal, used, category="soup")
                if item:
                    meal_items.append(item)
                    used.add(item["recipe"]["id"])

    elif meal_type == "snack":
        snack_pool = [r for r in all_recipes if r["meal_type"] == "snack"]
        item = select_dish(snack_pool, target_calories, used)
        if item:
            meal_items.append(item)
            used.add(item["recipe"]["id"])

    # Calculate totals
    total_nutrition = {"calories": 0, "protein_g": 0, "fat_g": 0, "carbs_g": 0}
    for item in meal_items:
        for k in total_nutrition:
            total_nutrition[k] += item["nutrition"][k]
    total_nutrition = {k: round(v, 1) for k, v in total_nutrition.items()}

    return {
        "dishes": meal_items,
        "total_nutrition": total_nutrition,
        "target_calories": target_calories
    }


def generate_weekly_plan(params, all_recipes):
    """
    Generate a 7-day meal plan.

    params: dict with keys:
        gender, age, height_cm, weight_kg, activity_level, goal,
        tastes, restrictions, meal_count, cheat_day (0-6 or None), cheat_meal (0-based or None)
    """
    from calculator import (
        calculate_bmr, calculate_tdee, calculate_target_calories,
        get_meal_calories, DAY_NAMES, MEAL_NAMES
    )

    bmr = calculate_bmr(params["gender"], params["weight_kg"], params["height_cm"], params["age"])
    tdee = calculate_tdee(bmr, params["activity_level"])
    daily_calories = calculate_target_calories(tdee, params["goal"])
    maintenance_calories = calculate_target_calories(tdee, "maintain")
    daily_macros = calculate_macros(daily_calories)

    meal_count = params["meal_count"]
    meal_names = MEAL_NAMES[meal_count]
    cheat_day = params.get("cheat_day")
    cheat_meal = params.get("cheat_meal")
    cooking_skill = params.get("cooking_skill", "expert")
    simple_mode = (cooking_skill == "simple")

    # Filter recipes by preferences
    filtered_recipes = filter_by_preferences(
        all_recipes,
        params.get("tastes", []),
        params.get("restrictions", [])
    )

    # Generate 7 days
    week_plan = []
    recent_used_ids = []  # Sliding window of recently used dish IDs (keep last ~15)

    for day_idx in range(7):
        is_cheat_day = (cheat_day is not None and day_idx == cheat_day)

        meals = get_meal_calories(
            daily_calories, meal_count,
            is_cheat_day=is_cheat_day,
            cheat_meal_index=cheat_meal if is_cheat_day else None,
            maintenance_calories=maintenance_calories
        )

        day_meals = []
        for meal in meals:
            # Determine meal type for recipe selection
            meal_name = meal["name"]
            if "早餐" in meal_name:
                recipe_meal_type = "breakfast"
            elif "加餐" in meal_name or "snack" in meal_name.lower():
                recipe_meal_type = "snack"
            elif "午餐" in meal_name:
                recipe_meal_type = "lunch"
            else:
                recipe_meal_type = "dinner"

            generated = generate_meal(
                meal["calories"],
                filtered_recipes,
                recent_used_ids[-15:],  # Avoid dishes used recently
                recipe_meal_type,
                is_cheat=meal.get("is_cheat", False),
                simple_mode=simple_mode
            )

            # Track used dish IDs
            for item in generated["dishes"]:
                recent_used_ids.append(item["recipe"]["id"])

            day_meals.append({
                "name": meal["name"],
                "is_cheat": meal.get("is_cheat", False),
                "target_calories": meal["calories"],
                "meal": generated
            })

        # Calculate day totals
        day_total = {"calories": 0, "protein_g": 0, "fat_g": 0, "carbs_g": 0}
        for dm in day_meals:
            for k in day_total:
                day_total[k] += dm["meal"]["total_nutrition"][k]
        day_total = {k: round(v, 1) for k, v in day_total.items()}

        week_plan.append({
            "day_index": day_idx,
            "day_name": DAY_NAMES[day_idx],
            "is_cheat_day": is_cheat_day,
            "meals": day_meals,
            "day_total": day_total
        })

    # Calculate weekly totals
    week_total = {"calories": 0, "protein_g": 0, "fat_g": 0, "carbs_g": 0}
    for day in week_plan:
        for k in week_total:
            week_total[k] += day["day_total"][k]
    week_total = {k: round(v, 1) for k, v in week_total.items()}

    # Aggregate shopping list
    shopping_list = {}
    for day in week_plan:
        for meal in day["meals"]:
            for item in meal["meal"]["dishes"]:
                for ing in item["ingredients"]:
                    name = ing["name"]
                    if name in shopping_list:
                        shopping_list[name] += ing["amount_g"]
                    else:
                        shopping_list[name] = ing["amount_g"]

    # Categorize shopping list
    categorized_shopping = categorize_ingredients(shopping_list)

    return {
        "week_plan": week_plan,
        "week_total": week_total,
        "shopping_list": categorized_shopping,
        "simple_mode": simple_mode,
        "user_params": {
            "bmr": bmr,
            "tdee": tdee,
            "daily_calories": daily_calories,
            "daily_macros": daily_macros,
            "maintenance_calories": maintenance_calories
        }
    }
