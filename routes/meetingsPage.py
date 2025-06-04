from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from bson import ObjectId
import pandas as pd
from io import BytesIO
from db import users, meetings
from datetime import datetime

router = APIRouter()

def format_datetime(dt_str):
    try:
        dt = datetime.fromisoformat(str(dt_str).replace("Z", "").split("+")[0])
        return dt.date(), dt.time().strftime("%H:%M")
    except:
        return "", ""

@router.post("/api/meetings-by-mentor")
async def export_meetings(request: Request):
    data = await request.json()
    user_name = data.get("userName")

    if not user_name:
        raise HTTPException(status_code=400, detail="Missing userName in request")

    mentor = users.find_one({"userName": user_name})
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")

    mentor_id = mentor["_id"]
    mentor_meetings = list(meetings.find({"mentorId": mentor_id}))
    if not mentor_meetings:
        raise HTTPException(status_code=404, detail="No meetings found")

    enriched = []
    for m in mentor_meetings:
        mentee = None
        mentee_id = m.get("menteeId")
        if mentee_id:
            try:
                mentee = users.find_one({"_id": ObjectId(mentee_id)})
            except Exception as e:
                print("⚠️ שגיאה בשליפת חניך:", e)

        date, start_time = format_datetime(m.get("startDateTime", ""))
        _, end_time = format_datetime(m.get("endDateTime", ""))

        enriched.append({
            "שם חונך": mentor.get("fullName", "לא נמצא"),
            "מייל חונך": mentor.get("userName", "לא נמצא"),
            "שם חניך": mentee.get("fullName", "לא נמצא") if mentee else "לא נמצא",
            "מייל חניך": mentee.get("userName", "לא נמצא") if mentee else "לא נמצא",
            "תאריך המפגש": date,
            "שעת התחלה": start_time,
            "שעת סיום": end_time,
            "סטטוס": m.get("status", ""),
            "תיאור המפגש": m.get("description", ""),
            "תקציר": m.get("summary", "")
        })

    df = pd.DataFrame(enriched)
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    safe_name = user_name.split("@")[0]
    filename = f"meetings_{safe_name}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
    )
