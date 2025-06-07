from fastapi import APIRouter, HTTPException
from bson import ObjectId
from fastapi.responses import FileResponse
import pandas as pd
from db import users, requests

import os

router = APIRouter()


@router.get("/api/mentees")
def get_mentees():
    print("\U0001F680 מתחיל לטעון חניכים...")
    mentees = list(users.find({"role": "mentee"}))

    for mentee in mentees:
        mentee["_id"] = str(mentee["_id"])
        mentee.setdefault("fullName", "")
        mentee.setdefault("idNumber", "")
        mentee.setdefault("userName", "")
        mentee.setdefault("phoneNumber", "")
        mentee.setdefault("school", "")
        mentee.setdefault("studyYear", "")
        mentee.setdefault("menteeHourQuota", 0)

    print(f"\U0001F4E4 שולח {len(mentees)} חניכים ל־frontend")
    return mentees


@router.get("/api/export-matches/{mentee_id}")
def export_matches(mentee_id: str):
    try:
        print(f"\U0001F4E5 קיבלתי בקשת ייצוא ל־mentee_id: {mentee_id}")
        mentee_object_id = ObjectId(mentee_id)

        mentee = users.find_one({"_id": mentee_object_id})
        if not mentee:
            raise HTTPException(status_code=404, detail="חניך לא נמצא")

        request = requests.find_one({"menteeId": mentee_object_id})
        print("\U0001F50E בקשת שיבוץ שנמצאה:", request)

        course_name = request.get("course", "") if request else ""

        mentor = None
        if request and request.get("mentorEmail"):
            mentor = users.find_one({"userName": request["mentorEmail"]})

        data = [{
            "שם חניך": mentee.get("fullName", ""),
            "מייל חניך": mentee.get("userName", ""),
            "הקורס הנדרש לחניכה": course_name,
            "שם חונך": mentor.get("fullName", "") if mentor else "",
            "מייל חונך": mentor.get("userName", "") if mentor else "",
            "סטטוס שיבוץ": "משובץ" if mentor else "לא משובץ"
        }]

        filename = f"shibutz_{mentee_id}.xlsx"
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False)
        print(f"✅ הקובץ נוצר בהצלחה: {filename}")

        return FileResponse(
            path=filename,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        print(f"❌ שגיאה בייצוא שיבוצים: {str(e)}")
        raise HTTPException(status_code=500, detail="שגיאה פנימית בשרת")
