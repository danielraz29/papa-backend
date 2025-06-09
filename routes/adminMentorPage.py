from fastapi import APIRouter, HTTPException
from db import users, meetings
from typing import Dict
from utils.email_util import send_email
from bson import ObjectId
from bson.errors import InvalidId
from fastapi.responses import FileResponse
import pandas as pd
import random
import string
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
    print("📨 בקשת עדכון סטטוס התקבלה:", payload)

    user_name = payload.get("userName")
    new_status_raw = payload.get("status")

    status_map = {
        "פעיל": "active",
        "לא פעיל": "inactive",
        "ממתין לאישור ⏳": "pending"
    }

    new_status = status_map.get(new_status_raw, new_status_raw)

    if not user_name or not new_status:
        raise HTTPException(status_code=400, detail="userName או status חסרים")

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
        print(f"📤 ייצוא מפגשים עבור mentorId: {mentor_id}")

        try:
            mentor_obj_id = ObjectId(mentor_id)
        except InvalidId:
            print("❌ ObjectId לא תקף")
            raise HTTPException(status_code=400, detail="ID של החונך לא תקין")

        mentor = users.find_one({"_id": mentor_obj_id})
        if not mentor:
            print("❌ חונך לא נמצא")
            raise HTTPException(status_code=404, detail="החונך לא נמצא")

        mentor_name = mentor.get("fullName", "חונך ללא שם")

        meetings_list = list(meetings.find({"mentorId": mentor_obj_id}))
        print(f"🔍 נמצאו {len(meetings_list)} מפגשים")

        if not meetings_list:
            raise HTTPException(status_code=404, detail="לא נמצאו מפגשים לחונך זה")

        data = []
        for i, meeting in enumerate(meetings_list):
            try:
                mentee_name = "חניך לא ידוע"
                mentee_id = meeting.get("menteeId")

                if mentee_id and ObjectId.is_valid(str(mentee_id)):
                    mentee = users.find_one({"_id": ObjectId(mentee_id)})
                    if mentee:
                        mentee_name = mentee.get("fullName", "חניך ללא שם")
                else:
                    print(f"⚠️ menteeId לא תקף במפגש {i}: {mentee_id}")

                data.append({
                    "שם חונך": mentor_name,
                    "שם חניך": mentee_name,
                    "נושא": meeting.get("summary", ""),
                    "תיאור": meeting.get("description") or "",
                    "תאריך התחלה": str(meeting.get("startDateTime") or ""),
                    "תאריך סיום": str(meeting.get("endDateTime") or ""),
                    "סטטוס מפגש": meeting.get("status") or ""
                })
            except Exception as inner_e:
                print(f"❌ שגיאה בעיבוד מפגש מס׳ {i}: {inner_e}")

        print("📊 יצירת DataFrame עם הנתונים")
        df = pd.DataFrame(data)

        filename = f"/tmp/meetings_{mentor_id}.xlsx"
        df.to_excel(filename, index=False)

        if not os.path.exists(filename):
            print("❌ הקובץ לא נוצר בפועל")
            raise HTTPException(status_code=500, detail="הקובץ לא נוצר כראוי")

        print(f"✅ הקובץ מוכן ונשלח: {filename}")
        return FileResponse(
            path=filename,
            filename=os.path.basename(filename),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except HTTPException as http_err:
        raise http_err

    except Exception as e:
        print(f"❌ שגיאה כללית ביצוא מפגשים: {str(e)}")
        raise HTTPException(status_code=500, detail=f"שגיאה פנימית בשרת: {str(e)}")
