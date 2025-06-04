from fastapi import APIRouter, UploadFile, Form, HTTPException
from typing import Optional
from datetime import datetime
from db import users
from bson import ObjectId
import base64
import shutil
import os
import json

router = APIRouter()

@router.post("/mentor-request")
async def submit_mentor_request(
    fulllName: str = Form(...),
    idNumber: str = Form(...),
    personalEmail: str = Form(...),
    collegeEmail: str = Form(...),
    phoneNumber: str = Form(...),
    school: str = Form(...),
    averageGrade: str = Form(...),
    studyYear: str = Form(...),
    availableDays: str = Form(...),
    status: str = Form(...),
    degrees: str = Form(...),  # מגיע כ־JSON string מ-FormData
    cvUrl: UploadFile = Form(...),
    profilePic: UploadFile = Form(...)
):
    try:
        # בדיקת משתמש כפול לפי מייל מכללה (userName)
        if users.find_one({"userName": collegeEmail}):
            raise HTTPException(status_code=400, detail="משתמש עם המייל הזה כבר קיים במערכת")

        # המרת תמונה ל־base64
        image_bytes = await profilePic.read()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        image_mime = profilePic.content_type

        # שמירת קורות חיים לקובץ זמני
        os.makedirs("temp_uploads", exist_ok=True)
        temp_cv_path = f"temp_uploads/{cvUrl.filename}"
        with open(temp_cv_path, "wb") as buffer:
            shutil.copyfileobj(cvUrl.file, buffer)

        # המרת רשימת הקורסים
        try:
            mentoringCourses = json.loads(degrees)
            if not isinstance(mentoringCourses, list):
                raise ValueError()
        except Exception:
            raise HTTPException(status_code=400, detail="פורמט קורסים לא תקין. יש לשלוח JSON array תקני")

        # המרת זמינות לימי ושעות
        availability_dict = json.loads(availableDays)
        availableDaysList = list(availability_dict.keys())
        availableHoursList = list(set(availability_dict.values()))

        # יצירת מסמך מנטור
        mentor = {
            "fullName": fulllName,
            "idNumber": idNumber,
            "gmail": personalEmail,
            "userName": collegeEmail,
            "phoneNumber": phoneNumber,
            "school": school,
            "mentoringCourses": mentoringCourses,
            "averageGrade": int(averageGrade),
            "studyYear": studyYear,
            "availableDays": availableDaysList,
            "availableHours": availableHoursList,
            "cvUrl": temp_cv_path,
            "image": image_base64,
            "imageMimeType": image_mime,
            "role": "mentor",
            "status": "pending",
            "mentorStatus": "available",
            "mentorAmountQuota": 5,
            "createdAt": datetime.utcnow()
        }

        users.insert_one(mentor)

        return {"message": "Mentor request submitted successfully"}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
