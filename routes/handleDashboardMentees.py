from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from pymongo.errors import PyMongoError

from db import users, requests, meetings  # שימוש בקולקציות מתוך db.py

router = APIRouter()

# Define Israel timezone offset manually (UTC+3 for summer time)
ISRAEL_TZ = timezone(timedelta(hours=3))

class Meeting(BaseModel):
    mentorId: str
    menteeId: str
    startDateTime: datetime
    endDateTime: datetime
    matchId: Optional[str] = None
    summary: str
    description: Optional[str] = None
    status: str = "open"
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

@router.get("/api/meetings")
def get_meetings(menteeId: str):
    try:
        if not ObjectId.is_valid(menteeId):
            raise HTTPException(status_code=400, detail="Mentee ID לא תקין")

        result = list(meetings.find({"menteeId": ObjectId(menteeId)}))
        for m in result:
            m["_id"] = str(m["_id"])
            m["menteeId"] = str(m["menteeId"])
            m["mentorId"] = str(m["mentorId"])
            if "matchId" in m:
                m["matchId"] = str(m["matchId"])
        return result
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/meetings")
def add_meeting(meeting: Meeting):
    try:
        if not ObjectId.is_valid(meeting.menteeId) or not ObjectId.is_valid(meeting.mentorId):
            raise HTTPException(status_code=400, detail="Mentee ID או Mentor ID לא תקינים")

        matched = requests.find_one({
            "menteeId": ObjectId(meeting.menteeId),
            "mentorId": ObjectId(meeting.mentorId),
            "status": "in progress"
        })
        if not matched:
            raise HTTPException(status_code=400, detail="החונך שנבחר אינו שייך לשיבוץ פעיל")

        meeting_dict = meeting.dict()
        meeting_dict["menteeId"] = ObjectId(meeting_dict["menteeId"])
        meeting_dict["mentorId"] = ObjectId(meeting_dict["mentorId"])
        meeting_dict["matchId"] = matched["_id"]

        # Convert to UTC assuming input is local (Israel time)
        meeting_dict["startDateTime"] = meeting.startDateTime.astimezone(ISRAEL_TZ).astimezone(timezone.utc)
        meeting_dict["endDateTime"] = meeting.endDateTime.astimezone(ISRAEL_TZ).astimezone(timezone.utc)

        meeting_dict["createdAt"] = datetime.utcnow()
        meeting_dict["updatedAt"] = datetime.utcnow()
        meeting_dict["description"] = None
        meeting_dict["status"] = "open"

        res = meetings.insert_one(meeting_dict)
        saved = meetings.find_one({"_id": res.inserted_id})
        saved["_id"] = str(saved["_id"])
        saved["menteeId"] = str(saved["menteeId"])
        saved["mentorId"] = str(saved["mentorId"])
        saved["matchId"] = str(saved["matchId"])
        return saved
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/meetings/{meeting_id}")
def delete_meeting(meeting_id: str):
    if not ObjectId.is_valid(meeting_id):
        raise HTTPException(status_code=400, detail="ID של הפגישה אינו תקין")
    result = meetings.delete_one({"_id": ObjectId(meeting_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="הפגישה לא נמצאה")
    return {"message": "הפגישה נמחקה בהצלחה"}

@router.get("/api/mentor-requests")
def get_assignments(menteeId: str, status: str = "in progress"):
    try:
        if not ObjectId.is_valid(menteeId):
            raise HTTPException(status_code=400, detail="menteeId לא תקין")

        result = list(requests.find({
            "menteeId": ObjectId(menteeId),
            "mentorId": {"$ne": None},
            "status": status
        }))
        for a in result:
            a["_id"] = str(a["_id"])
            a["menteeId"] = str(a["menteeId"])
            a["mentorId"] = str(a["mentorId"])
            mentor = users.find_one({"_id": ObjectId(a["mentorId"])});
            a["mentorName"] = mentor["fullName"] if mentor else "לא ידוע"
        return result
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=str(e))
