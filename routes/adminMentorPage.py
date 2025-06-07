from fastapi import APIRouter, HTTPException
from db import users
from typing import Dict
import random
import string
from utils.email_util import send_email  # נשלח בהמשך
from bson import ObjectId

router = APIRouter()

def generate_password():
    letters = ''.join(random.choices(string.ascii_uppercase, k=4))
    digits = ''.join(random.choices(string.digits, k=4))
    return letters + digits

@router.get("/api/mentors")
def get_mentors():
    mentors = list(users.find({"role": "mentor"}))
    for mentor in mentors:
        mentor["_id"] = str(mentor["_id"])
        mentor.setdefault("fullName", "")
        mentor.setdefault("idNumber", "")
        mentor.setdefault("userName", "")
        mentor.setdefault("phoneNumber", "")
        mentor.setdefault("school", "")
        mentor.setdefault("averageGrade", "")
        mentor.setdefault("availableDays", [])
        mentor.setdefault("availableHours", [])
        mentor.setdefault("cvUrl", "")
        mentor.setdefault("status", "")
    return mentors

@router.post("/api/update-status")
def update_status(payload: Dict):
    print("📨 הגיע בקשת עדכון סטטוס:")
    print("payload:", payload)

    user_name = payload.get("userName")
    new_status_raw = payload.get("status")

    status_map = {
        "פעיל": "active",
        "לא פעיל": "inactive",
        "ממתין לאישור ⏳": "pending"
    }

    new_status = status_map.get(new_status_raw, new_status_raw)

    if not user_name or not new_status:
        raise HTTPException(status_code=400, detail="חסר userName או סטטוס")

    result = users.update_one(
        {"userName": user_name},
        {"$set": {"status": new_status}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="משתמש לא נמצא")

    # שליחת מייל אם הסטטוס הוא פעיל
    if new_status == "active":
        mentor = users.find_one({"userName": user_name})
        if mentor and mentor.get("gmail"):
            password = generate_password()
            users.update_one({"userName": user_name}, {"$set": {"password": password}})
            try:
                send_email(
                    to_email=mentor["gmail"],
                    subject="פרטי התחברות למערכת פאפה",
                    body=f"""שלום {mentor.get('fullName', '')},

הסטטוס שלך עודכן ל־פעיל במערכת החונכות של פאפה.
הסיסמה שלך להתחברות היא: {password}

בהצלחה!
צוות פאפה
"""
                )
            except Exception as e:
                print("❌ שגיאה בשליחת מייל:", str(e))

    return {"message": "הסטטוס עודכן בהצלחה"}
