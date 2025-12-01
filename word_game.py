from flask import Flask, render_template, jsonify, request
import pandas as pd
import random
import json
import os

app = Flask(__name__)

# ==================================================
# 🧩 隨機抽題（支援 file 參數）
# ==================================================
def get_random_question(file_option="junior"):
    try:
        if file_option == "senior":
            df = pd.read_csv("高中5000單字.csv")
        else:
            df = pd.read_csv("國中2000單字.csv")
    except FileNotFoundError:
        return None

    row = df.sample(1).iloc[0]
    return {
        "question": row["題目"],
        "option1": row["選項1."],
        "option2": row["選項2."],
        "option3": row["選項3."],
        "option4": row["選項4."],
        "correct_answer": int(row["標準答案"])
    }

# ==================================================
# 🏠 首頁
# ==================================================
@app.route("/")
def home():
    return render_template("index.html")

# ==================================================
# 🎮 賺罐罐主頁
# ==================================================
@app.route("/earn")
def earn():
    file_option = request.args.get("file", "junior")
    data = get_random_question(file_option)
    if not data:
        return f"❌ 找不到題目資料檔（請確認對應的 CSV 是否存在）"
    return render_template("earn.html", **data, selected_file=file_option)

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"success": False, "message": "帳號或密碼不可為空"})

    if len(username) > 10:
        return jsonify({"success": False, "message": "暱稱不可以超過10個字"})

    users = []
    if os.path.exists("users.json"):
        with open("users.json", "r", encoding="utf-8") as f:
            try:
                users = json.load(f)
            except json.JSONDecodeError:
                users = []

    # 檢查帳號是否已存在
    if any(u["username"] == username for u in users):
        return jsonify({"success": False, "message": "帳號已存在"})

    # 新增帳號，預設罐頭數0
    users.append({"username": username, "password": password, "cans": 0})

    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

    return jsonify({"success": True, "username": username})


# 取得使用者罐頭數
@app.route("/get_cans", methods=["POST"])
def get_cans():
    data = request.get_json()
    username = data.get("username")
    if not username or not os.path.exists("users.json"):
        return jsonify({"success": False, "message": "帳號不存在"})

    with open("users.json", "r", encoding="utf-8") as f:
        users = json.load(f)

    for user in users:
        if user["username"] == username:
            return jsonify({"success": True, "cans": user.get("cans", 0)})

    return jsonify({"success": False, "message": "帳號不存在"})

# 新增更新罐頭數 API（遊戲答題後更新）
@app.route("/update_cans", methods=["POST"])
def update_cans():
    data = request.get_json()
    username = data.get("username")
    new_cans = data.get("cans")

    if not username or new_cans is None:
        return jsonify({"success": False, "message": "更新失敗"})

    if not os.path.exists("users.json"):
        return jsonify({"success": False, "message": "使用者資料不存在"})

    with open("users.json", "r", encoding="utf-8") as f:
        users = json.load(f)

    updated = False
    for user in users:
        if user["username"] == username:
            user["cans"] = new_cans
            updated = True
            break

    if not updated:
        return jsonify({"success": False, "message": "帳號不存在"})

    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

    return jsonify({"success": True, "cans": new_cans})

# 🧧 下一題 API
@app.route("/next_question")
def next_question():
    file_option = request.args.get("file", "junior")
    data = get_random_question(file_option)
    if not data:
        return jsonify({"error": "題目檔不存在"}), 404
    return jsonify(data)

# ==================================================
# 🎰 轉蛋主頁
# ==================================================
@app.route("/gachapon")
def gachapon():
    return render_template("gachapon.html")

# 🎰 轉蛋抽取 API
@app.route("/draw_gacha")
def draw_gacha():
    try:
        df = pd.read_csv("轉蛋.csv")
    except FileNotFoundError:
        return jsonify({"error": "找不到轉蛋資料檔（轉蛋.csv）"}), 404

    roll = random.random()
    rarity = "超激稀有" if roll < 0.05 else "稀有"

    subset = df[df["稀有度"] == rarity]
    if subset.empty:
        return jsonify({"error": f"沒有符合稀有度 '{rarity}' 的角色"}), 404

    row = subset.sample(1).iloc[0]
    result = {
        "character": row["角色"],
        "image": row["圖片"],
        "rarity": row["稀有度"]
    }
    return jsonify(result)

# ==================================================
# 🔐 登入 API
# ==================================================
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    # 檢查 users.json 是否存在
    if not os.path.exists("users.json"):
        return jsonify({"success": False, "message": "找不到使用者資料檔"})

    with open("users.json", "r", encoding="utf-8") as f:
        try:
            users = json.load(f)
        except json.JSONDecodeError:
            return jsonify({"success": False, "message": "使用者資料檔格式錯誤"})

    # 驗證帳密
    for user in users:
        if user["username"] == username and user["password"] == password:
            return jsonify({
                "success": True,
                "username": user["username"],
                "cans": user.get("cans", 0)
            })

    return jsonify({"success": False, "message": "帳號不存在或密碼錯誤"})

# ==================================================
# 🚀 本地開發
# ==================================================
if __name__ == "__main__":
    app.run(debug=True)

