import random
import datetime
import json
import os
import difflib
import requests
import openai

# === 設定 ===

def load_config(path="config.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

config = load_config()
openai.api_key = config["openai_api_key"]
WEBHOOK_URL = config["google_chat_webhook"]

HISTORY_FILE = "message_history.json"
SIMILARITY_THRESHOLD = 0.85  # 類似度しきい値

# === プロンプト候補（ランダム） ===
static_prompt = "従業員向けの健康情報の発信をお願いします。簡単なアドバイスを一つ、簡潔にアナウンスしてください。今日は以下のテーマでお願いします。\n\n"
prompt_templates = [
    "健康に関する簡単なアドバイスを1つ教えてください。",
    "体重管理のための健康アドバイスを教えてください。",
    "ストレス管理のための健康アドバイスを教えてください。",
    
    "健康に関する豆知識を1つ教えてください。",
    "健康に関する面白いエピソードを教えてください。",
    "今日の健康に関する名言を教えてください。",
    "健康に関する面白い事実を1つ教えてください。",
    "今日の健康に関するクイズを出してください。",

    "健康に関するヒントを1つ教えてください。",
    "日常生活で簡単に実践できる健康習慣を教えてください。",

    "健康に関する最近の研究結果を教えてください。",
    "健康に関する最近のキャンペーンを教えてください。",
    "病気の予防に関する最近のニュースを教えてください。",
    "生活習慣病に関する最近の研究を教えてください。",
    "メンタルヘルスに関する最近の研究を教えてください。",
    "運動不足に関する最近の研究を教えてください。",
    "健康に関する最近のトピックを教えてください。",

    "医療ではなく、ライフスタイル面での健康のヒントを1つ教えてください。",


    "座り仕事の多い人向けの健康アドバイスを教えてください。",
    "ストレス解消に役立つ健康アドバイスを教えてください。",
    "運動不足を解消するための健康アドバイスを教えてください。",
    "食生活を改善するための健康アドバイスを教えてください。",
    "睡眠の質を向上させるための健康アドバイスを教えてください。",
]

# === 履歴の読み書き ===
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(message):
    history = load_history()
    history.append({"date": datetime.date.today().isoformat(), "message": message})
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[-30:], f, ensure_ascii=False, indent=2)

def is_similar_to_history(message):
    history = load_history()
    for entry in history:
        similarity = difflib.SequenceMatcher(None, entry["message"], message).ratio()
        if similarity > SIMILARITY_THRESHOLD:
            return True
    return False

# === ChatGPTからメッセージ生成 ===
def get_chatgpt_message():
    random.seed(datetime.date.today().isoformat())
    prompt = static_prompt + random.choice(prompt_templates)

    for _ in range(5):  # 最大5回試す
        response = openai.ChatCompletion.create(
            model="gpt-4",
            temperature=0.9,
            messages=[
                {"role": "system", "content": "あなたは健康情報を社内チャットへアナウンスする広報担当者です。"},
                {"role": "user", "content": prompt}
            ]
        )
        message = response['choices'][0]['message']['content'].strip()
        if not is_similar_to_history(message):
            return message
    return message  # 最後のものを採用

# === Google Chatへ送信 ===
def send_to_google_chat(message):
    payload = {"text": f"🩺 今日の健康アドバイス\n\n{message}"}
    response = requests.post(WEBHOOK_URL, json=payload)
    return response.status_code

# === メイン処理 ===
if __name__ == "__main__":
    message = get_chatgpt_message()
    status = send_to_google_chat(message)
    if status == 200:
        save_history(message)
        print("✅ メッセージを送信しました。")
    else:
        print("⚠️ 送信失敗。ステータスコード:", status)
