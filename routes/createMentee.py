from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db import users
from datetime import datetime
import random
import string

router = APIRouter()

class MenteePayload(BaseModel):
    fullName: str
    idNumber: str
    userName: str
    phoneNumber: str
    school: str
    studyYear: str

@router.post("/api/create-mentee")
def create_mentee(data: MenteePayload):
    # האם המשתמש כבר קיים?
    if users.find_one({"userName": data.userName}):
        raise HTTPException(status_code=409, detail="משתמש כבר קיים")

    # יצירת סיסמה רנדומלית – 4 ספרות + 4 אותיות גדולות
    digits = ''.join(random.choices(string.digits, k=4))
    letters = ''.join(random.choices(string.ascii_uppercase, k=4))
    password = digits + letters

    user = {
        "fullName": data.fullName,
        "idNumber": data.idNumber,
        "userName": data.userName,
        "password": password,
        "phoneNumber": data.phoneNumber,
        "school": data.school,
        "studyYear": data.studyYear,
        "menteeHourQuota": 30,
        "role": "mentee",
        "status": "active",
        "createdAt": datetime.utcnow()
    }

    result = users.insert_one(user)

    if result.inserted_id:
        return {"message": "נוצר חניך חדש בהצלחה", "password": password}
    else:
        raise HTTPException(status_code=500, detail="שגיאה בהכנסת החניך")
