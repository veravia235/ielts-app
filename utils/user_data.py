import json
import os

def load_user_data(username):
    """读取用户的专属本地JSON存档"""
    file_name = f"save_{username}.json"
    if os.path.exists(file_name):
        with open(file_name, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "word_bank": [],
        "failed_words": [],
        "last_lesson": "尚未开启首日课程",
        "study_sessions": 0
    }

def save_user_data(username, word_bank, failed_words, last_lesson, study_sessions):
    """保存进度到用户专属本地JSON存档"""
    if username:
        data = {
            "word_bank": word_bank,
            "failed_words": list(failed_words),
            "last_lesson": last_lesson,
            "study_sessions": study_sessions
        }
        with open(f"save_{username}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)