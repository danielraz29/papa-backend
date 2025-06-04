from fastapi import APIRouter, HTTPException
from db import users

router = APIRouter()

@router.get("/api/mentors")
def get_mentors():
    mentors = list(users.find({"role": "mentor"}))
    for mentor in mentors:
        mentor["_id"] = str(mentor["_id"])
        mentor.setdefault("fullName", "")
        mentor.setdefault("idNumber", "")  # ← חדש
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
def update_status(payload: dict):
    print("📨 הגיע בקשת עדכון סטטוס:")
    print("payload:", payload)

    user_name = payload.get("userName")
    new_status = payload.get("status")

    if not user_name or not new_status:
        raise HTTPException(status_code=400, detail="חסר userName או סטטוס")

    result = users.update_one(
        {"userName": user_name},
        {"$set": {"status": new_status}}
    )

    print("🛠️ כמה רשומות עודכנו בפועל:", result.matched_count)

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="משתמש לא נמצא")

    return {"message": "הסטטוס עודכן בהצלחה"}
