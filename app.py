import os
from flask import Flask, render_template, request
from calculator import (
    calculate_bmr, calculate_tdee, calculate_target_calories,
    calculate_macros, get_meal_calories, DAY_NAMES, MEAL_NAMES,
    ACTIVITY_LABELS, GOAL_LABELS
)
from meal_engine import load_recipes, generate_weekly_plan

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html",
                           activity_labels=ACTIVITY_LABELS,
                           goal_labels=GOAL_LABELS,
                           day_names=DAY_NAMES)


@app.route("/plan", methods=["POST"])
def plan():
    # Parse form data
    gender = request.form.get("gender", "male")
    age = int(request.form.get("age", 30))
    height_cm = int(request.form.get("height_cm", 170))
    weight_kg = float(request.form.get("weight_kg", 70))
    activity_level = request.form.get("activity_level", "moderate")
    goal = request.form.get("goal", "maintain")
    meal_count = int(request.form.get("meal_count", 3))

    # Parse tastes (checkboxes)
    tastes = request.form.getlist("tastes")
    if "all" in tastes:
        tastes = ["all"]

    # Parse restrictions (checkboxes)
    restrictions = request.form.getlist("restrictions")
    if "none" in restrictions:
        restrictions = []

    # Parse cooking skill
    cooking_skill = request.form.get("cooking_skill", "expert")

    # Parse cheat day settings
    cheat_day = None
    cheat_meal = None
    if goal in ("lose", "gain"):
        cheat_day_str = request.form.get("cheat_day", "")
        if cheat_day_str:
            cheat_day = int(cheat_day_str)
        cheat_meal = 1  # Default to lunch (index 1 in most distributions)

    # Load recipes
    all_recipes = load_recipes()

    # Generate plan
    params = {
        "gender": gender,
        "age": age,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "activity_level": activity_level,
        "goal": goal,
        "tastes": tastes,
        "restrictions": restrictions,
        "meal_count": meal_count,
        "cheat_day": cheat_day,
        "cheat_meal": cheat_meal,
        "cooking_skill": cooking_skill
    }

    result = generate_weekly_plan(params, all_recipes)

    # Add display-friendly labels
    result["display"] = {
        "gender": "男" if gender == "male" else "女",
        "age": age,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "activity_level": ACTIVITY_LABELS.get(activity_level, activity_level),
        "goal": GOAL_LABELS.get(goal, goal),
        "meal_count": meal_count,
        "meal_names": MEAL_NAMES[meal_count],
        "cheat_day": DAY_NAMES[cheat_day] if cheat_day is not None else None,
        "tastes": tastes,
        "restrictions": restrictions,
        "cooking_skill": "做饭达人" if cooking_skill == "expert" else "不爱做饭"
    }

    return render_template("plan.html", **result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, host="0.0.0.0", port=port)
