from fastapi import APIRouter, HTTPException
from db import users, meetings
from typing import Dict
import random
import string
from utils.email_util import send_email
from bson import ObjectId
from fastapi.responses import FileResponse
import pandas as pd
import os

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

@router.get("/api/export-meetings/{mentor_id}")
def export_meetings(mentor_id: str):
    try:
        print(f"📦 בקשת ייצוא עבור mentorId: {mentor_id}")
        mentor_obj_id = ObjectId(mentor_id)
        mentor = users.find_one({"_id": mentor_obj_id})

        if not mentor:
            raise HTTPException(status_code=404, detail="חונך לא נמצא")

        full_name = mentor.get("fullName", "")
        meetings_list = list(meetings.find({"mentorId": mentor_obj_id}))

        if not meetings_list:
            raise HTTPException(status_code=404, detail="לא נמצאו מפגשים לחונך זה")

        data = []
        for m in meetings_list:
            mentee = users.find_one({"_id": m["menteeId"]})
            data.append({
                "נושא": m.get("summary", ""),
                "תיאור": m.get("description", ""),
                "שם חונך": full_name,
                "שם חניך": mentee.get("fullName", "") if mentee else "לא ידוע",
                "תאריך התחלה": m.get("startDateTime"),
                "תאריך סיום": m.get("endDateTime"),
                "סטטוס": m.get("status", "")
            })

        df = pd.DataFrame(data)
        filename = f"meetings_{mentor_id}.xlsx"
        df.to_excel(filename, index=False)

        print(f"✅ הקובץ נוצר: {filename}")
        return FileResponse(
            path=filename,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        print(f"❌ שגיאה: {str(e)}")
        raise HTTPException(status_code=500, detail="שגיאה פנימית בשרת")

