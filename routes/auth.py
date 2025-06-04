from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db import users  # שימוש בקולקציה מתוך db.py
from pymongo.errors import PyMongoError

router = APIRouter()

# מודל התחברות
class LoginRequest(BaseModel):
    userName: str
    password: str

# נקודת קצה לבדוק התחברות
@router.post("/login")
def login_user(data: LoginRequest):
    print(f"🔐 ניסיון התחברות עם: {data.userName}")

    try:
        user = users.find_one({
            "userName": data.userName,
            "password": data.password  # בעתיד: הצפנה!
        })
    except PyMongoError as e:
        print(f"❌ שגיאה בגישה למסד הנתונים: {e}")
        raise HTTPException(status_code=500, detail="שגיאה במסד הנתונים")

    if not user:
        raise HTTPException(status_code=401, detail="שם משתמש או סיסמה שגויים")

    role = user.get("role", "mentee")  # ברירת מחדל
    full_name = user.get("fullName", "")

    return {
        "message": "התחברות הצליחה!",
        "userId": str(user["_id"]),  #
        "name": full_name,
        "role": role,
        "redirectTo": f"/dashboard/{role}"
    }
