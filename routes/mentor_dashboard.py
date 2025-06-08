from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime
from db import meetings, requests, users

router = APIRouter()

@router.get("/mentor-meetings")
def get_meetings_by_mentor(userName: str):
    mentor = users.find_one({"userName": userName})
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")

    mentor_id = mentor["_id"]
    result = list(meetings.find({"mentorId": mentor_id}))
    for m in result:
        m["_id"] = str(m["_id"])
        m["mentorId"] = str(m["mentorId"])
        m["menteeId"] = str(m["menteeId"])
        if "matchId" in m:
            m["matchId"] = str(m["matchId"])
    return result

@router.get("/mentor-assigned")
def get_mentees_by_mentor(userName: str):
    mentor = users.find_one({"userName": userName})
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")

    mentor_id = mentor["_id"]
    result = list(requests.find({"mentorId": mentor_id}))
    enriched = []

    for r in result:
        mentee = users.find_one({"_id": r["menteeId"]})
        if mentee:
            enriched.append({
                "menteeId": str(mentee["_id"]),
                "fullName": mentee.get("fullName"),
                "email": mentee.get("userName"),
                "phone": mentee.get("phoneNumber"),
                "status": mentee.get("status"),
                "school": mentee.get("school"),
                "idNumber": mentee.get("idNumber")
            })

    return enriched

@router.post("/meetings")
def create_meeting(meeting: dict):
    required_fields = ["mentorId", "menteeId", "summary", "startDateTime", "endDateTime"]
    if not all(field in meeting for field in required_fields):
        raise HTTPException(status_code=400, detail="Missing fields")

    try:
        meeting["startDateTime"] = datetime.fromisoformat(meeting["startDateTime"])
        meeting["endDateTime"] = datetime.fromisoformat(meeting["endDateTime"])
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    mentor = users.find_one({"userName": meeting["mentorId"]})
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")
    meeting["mentorId"] = mentor["_id"]

    meeting["menteeId"] = ObjectId(meeting["menteeId"])

    result = meetings.insert_one(meeting)
    meeting["_id"] = str(result.inserted_id)
    meeting["mentorId"] = str(meeting["mentorId"])
    meeting["menteeId"] = str(meeting["menteeId"])
    return meeting

@router.get("/mentor-name")
def get_mentor_name(userName: str):
    mentor = users.find_one({"userName": userName})
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")
    return {"fullName": mentor.get("fullName", "")}

@router.delete("/meetings/{meeting_id}")
def delete_meeting(meeting_id: str):
    result = meetings.delete_one({"_id": ObjectId(meeting_id)})
    if result.deleted_count == 1:
        return {"message": "Deleted"}
    raise HTTPException(status_code=404, detail="Meeting not found")
