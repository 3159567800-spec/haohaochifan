import math

# Activity level multipliers
ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,         # 久坐少动
    "light": 1.375,            # 轻度活动
    "moderate": 1.55,          # 中度活动
    "heavy": 1.725             # 高强度
}

ACTIVITY_LABELS = {
    "sedentary": "久坐少动",
    "light": "轻度活动",
    "moderate": "中度活动",
    "heavy": "高强度"
}

GOAL_LABELS = {
    "lose": "减脂",
    "maintain": "保持体重",
    "gain": "增肌"
}

# Macro split: protein 30%, carbs 45%, fat 25%
MACRO_PROTEIN_RATIO = 0.30
MACRO_CARBS_RATIO = 0.45
MACRO_FAT_RATIO = 0.25

KCAL_PER_G_PROTEIN = 4
KCAL_PER_G_CARBS = 4
KCAL_PER_G_FAT = 9

# Meal distribution for different meal counts
# [meal_1, meal_2, meal_3, meal_4, meal_5]
MEAL_DISTRIBUTION = {
    2: [0.40, 0.60, 0, 0, 0],
    3: [0.30, 0.40, 0.30, 0, 0],
    4: [0.25, 0.35, 0.25, 0.15, 0],
    5: [0.20, 0.30, 0.20, 0.15, 0.15]
}

MEAL_NAMES = {
    2: ["早餐", "午餐"],
    3: ["早餐", "午餐", "晚餐"],
    4: ["早餐", "午餐", "晚餐", "加餐"],
    5: ["早餐", "午餐", "晚餐", "加餐1", "加餐2"]
}

DAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def calculate_bmr(gender, weight_kg, height_cm, age):
    """Mifflin-St Jeor equation"""
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age
    if gender == "male":
        bmr += 5
    else:
        bmr -= 161
    return round(bmr)


def calculate_tdee(bmr, activity_level):
    """Total Daily Energy Expenditure"""
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)
    return round(bmr * multiplier)


def calculate_target_calories(tdee, goal):
    """Target daily calories based on goal"""
    adjustments = {"lose": -300, "maintain": 0, "gain": 300}
    return tdee + adjustments.get(goal, 0)


def calculate_macros(calories):
    """Calculate macro nutrient targets in grams"""
    protein_g = round(calories * MACRO_PROTEIN_RATIO / KCAL_PER_G_PROTEIN)
    carbs_g = round(calories * MACRO_CARBS_RATIO / KCAL_PER_G_CARBS)
    fat_g = round(calories * MACRO_FAT_RATIO / KCAL_PER_G_FAT)
    return {
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "calories": calories
    }


def get_meal_calories(daily_calories, meal_count, is_cheat_day=False, cheat_meal_index=None, maintenance_calories=None):
    """
    Calculate calories per meal.

    On cheat day: the cheat meal uses maintenance-level calories for that meal slot,
    while other meals use the normal deficit/surplus distribution.
    """
    distribution = MEAL_DISTRIBUTION[meal_count]
    meal_names = MEAL_NAMES[meal_count]

    meals = []
    for i in range(meal_count):
        ratio = distribution[i]
        if is_cheat_day and i == cheat_meal_index and maintenance_calories:
            # Cheat meal: use maintenance-level calories
            maintenance_ratio = distribution[i]
            calories = round(maintenance_calories * maintenance_ratio * 1.3)  # 30% extra on maintenance
        else:
            calories = round(daily_calories * ratio)
        meals.append({
            "index": i,
            "name": meal_names[i],
            "ratio": ratio,
            "calories": calories,
            "is_cheat": is_cheat_day and i == cheat_meal_index
        })

    # Adjust non-cheat meals on cheat day to keep total close to target
    if is_cheat_day and cheat_meal_index is not None:
        cheat_cal = meals[cheat_meal_index]["calories"]
        remaining_cal = daily_calories - cheat_cal
        remaining_ratio_sum = sum(m["ratio"] for m in meals if m["index"] != cheat_meal_index)
        if remaining_ratio_sum > 0:
            for m in meals:
                if m["index"] != cheat_meal_index:
                    m["calories"] = round(remaining_cal * m["ratio"] / remaining_ratio_sum)

    return meals


def get_daily_macros_for_meal(calories):
    """Get macros for a single meal based on its calorie target"""
    return calculate_macros(calories)
