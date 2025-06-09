from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime
from db import meetings, requests, users

router = APIRouter()

@router.get("/api/mentor-meetings")
def get_meetings_by_mentor(userId: str):
    if not ObjectId.is_valid(userId):
        raise HTTPException(status_code=400, detail="Invalid userId")

    mentor = users.find_one({"_id": ObjectId(userId)})
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")

    result = list(meetings.find({"mentorId": mentor["_id"]}))
    for m in result:
        m["_id"] = str(m["_id"])
        m["mentorId"] = str(m["mentorId"])
        m["menteeId"] = str(m["menteeId"])
        if "matchId" in m:
            m["matchId"] = str(m["matchId"])
    return result


@router.get("/api/mentor-assigned")
def get_mentees_by_mentor(userId: str):
    if not ObjectId.is_valid(userId):
        raise HTTPException(status_code=400, detail="Invalid userId")

    mentor = users.find_one({"_id": ObjectId(userId)})
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")

    result = list(requests.find({"mentorId": mentor["_id"]}))
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


@router.post("/api/meetings")
def create_meeting(meeting: dict):
    required_fields = ["mentorId", "menteeId", "summary", "description", "status", "startDateTime", "endDateTime"]
    if not all(field in meeting for field in required_fields):
        raise HTTPException(status_code=400, detail="Missing fields")

    try:
        start_dt = datetime.fromisoformat(meeting["startDateTime"].replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(meeting["endDateTime"].replace("Z", "+00:00"))
        duration_hours = int((end_dt - start_dt).total_seconds() // 3600)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    if not ObjectId.is_valid(meeting["mentorId"]) or not ObjectId.is_valid(meeting["menteeId"]):
        raise HTTPException(status_code=400, detail="Invalid ObjectId")

    mentor_id = ObjectId(meeting["mentorId"])
    mentee_id = ObjectId(meeting["menteeId"])

    if meeting["status"] == "done":
        users.update_one({"_id": mentor_id}, {"$inc": {"menteeHourQuota": -duration_hours}})

    meeting["startDateTime"] = start_dt
    meeting["endDateTime"] = end_dt
    meeting["mentorId"] = mentor_id
    meeting["menteeId"] = mentee_id

    result = meetings.insert_one(meeting)

    meeting["_id"] = str(result.inserted_id)
    meeting["mentorId"] = str(mentor_id)
    meeting["menteeId"] = str(mentee_id)
    return meeting


@router.put("/api/meetings/{meeting_id}")
def update_meeting(meeting_id: str, meeting: dict):
    if not ObjectId.is_valid(meeting_id):
        raise HTTPException(status_code=400, detail="Invalid meeting ID")

    required_fields = ["mentorId", "menteeId", "summary", "description", "status", "startDateTime", "endDateTime"]
    if not all(field in meeting for field in required_fields):
        raise HTTPException(status_code=400, detail="Missing fields")

    try:
        start_dt = datetime.fromisoformat(meeting["startDateTime"].replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(meeting["endDateTime"].replace("Z", "+00:00"))
        duration_hours = int((end_dt - start_dt).total_seconds() // 3600)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    if not ObjectId.is_valid(meeting["mentorId"]) or not ObjectId.is_valid(meeting["menteeId"]):
        raise HTTPException(status_code=400, detail="Invalid ObjectId")

    mentor_id = ObjectId(meeting["mentorId"])
    mentee_id = ObjectId(meeting["menteeId"])

    existing = meetings.find_one({"_id": ObjectId(meeting_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Meeting not found")

    prev_status = existing.get("status")
    new_status = meeting["status"]

    if prev_status != new_status:
        if new_status == "done":
            users.update_one({"_id": mentor_id}, {"$inc": {"menteeHourQuota": -duration_hours}})
        elif prev_status == "done" and new_status in ["open", "cancel"]:
            users.update_one({"_id": mentor_id}, {"$inc": {"menteeHourQuota": duration_hours}})

    meeting["startDateTime"] = start_dt
    meeting["endDateTime"] = end_dt
    meeting["mentorId"] = mentor_id
    meeting["menteeId"] = mentee_id

    meetings.update_one(
        {"_id": ObjectId(meeting_id)},
        {"$set": meeting}
    )

    meeting["_id"] = meeting_id
    meeting["mentorId"] = str(mentor_id)
    meeting["menteeId"] = str(mentee_id)
    return meeting


@router.get("/api/mentor-name")
def get_mentor_name(userId: str):
    if not ObjectId.is_valid(userId):
        raise HTTPException(status_code=400, detail="Invalid userId")
    mentor = users.find_one({"_id": ObjectId(userId)})
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")
    return {"fullName": mentor.get("fullName", "")}


@router.delete("/api/meetings/{meeting_id}")
def delete_meeting(meeting_id: str):
    if not ObjectId.is_valid(meeting_id):
        raise HTTPException(status_code=400, detail="Invalid meeting ID")

    result = meetings.delete_one({"_id": ObjectId(meeting_id)})
    if result.deleted_count == 1:
        return {"message": "Deleted"}
    raise HTTPException(status_code=404, detail="Meeting not found")
