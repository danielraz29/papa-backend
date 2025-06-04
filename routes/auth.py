from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db import users
from pymongo.errors import PyMongoError
import bcrypt

router = APIRouter()

class LoginRequest(BaseModel):
    userName: str
    password: str

@router.post("/login")
def login_user(data: LoginRequest):
    print(f"🔐 ניסיון התחברות עם: {data.userName}")

    try:
        user = users.find_one({"userName": data.userName})
    except PyMongoError as e:
        print(f"❌ שגיאה בגישה למסד הנתונים: {e}")
        raise HTTPException(status_code=500, detail="שגיאה במסד הנתונים")

    if not user:
        raise HTTPException(status_code=401, detail="שם משתמש או סיסמה שגויים")

    # בדיקת מצב חשבון
    if user.get("status") != "active":
        raise HTTPException(status_code=403, detail="החשבון לא פעיל או ממתין לאישור. אנא פנה לצוות ההנהלה.")

    # השוואת סיסמה מוצפנת
    hashed_password = user.get("password")
    if not hashed_password or not bcrypt.checkpw(data.password.encode("utf-8"), hashed_password.encode("utf-8")):
        raise HTTPException(status_code=401, detail="שם משתמש או סיסמה שגויים")

    role = user.get("role", "mentee")
    full_name = user.get("fullName", "")

    return {
        "message": "התחברות הצליחה!",
        "userId": str(user["_id"]),
        "name": full_name,
        "role": role,
        "redirectTo": f"/dashboard/{role}"
    }
