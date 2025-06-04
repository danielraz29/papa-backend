from fastapi import APIRouter
from bson import ObjectId
from fastapi.responses import FileResponse
import pandas as pd
import os
from db import users, requests

router = APIRouter()

@router.get("/api/mentees")
def get_mentees():
    print("🚀 מתחיל לטעון חניכים...")
    mentees = list(users.find({"role": "mentee"}))
    print("✅ שלפתי חניכים!", mentees)

    for mentee in mentees:
        mentee["_id"] = str(mentee["_id"])
        mentee.setdefault("fullName", "")
        mentee.setdefault("idNumber", "")
        mentee.setdefault("userName", "")
        mentee.setdefault("phoneNumber", "")
        mentee.setdefault("school", "")
        mentee.setdefault("studyYear", "")
        mentee.setdefault("availableHours", [])
        mentee.setdefault("availableDays", [])
        mentee.setdefault("menteeHourQuota", 0)

    print("📤 מחזיר חניכים ל-frontend")
    return mentees

@router.get("/api/export-matches/{mentee_id}")
def export_matches(mentee_id: str):
    from bson import ObjectId
    mentee_object_id = ObjectId(mentee_id)

    mentee = users.find_one({"_id": mentee_object_id})
    request = requests.find_one({"menteeId": mentee_object_id})

    print("👤 חניך:", mentee)
    print("📄 בקשת שיבוץ:", request)

    if not mentee:
        return {"error": "חניך לא נמצא"}

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

    return FileResponse(
        path=filename,
        filename=filename,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
