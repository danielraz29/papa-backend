from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from db import users, requests
from pymongo.errors import PyMongoError
import re
import tempfile
import fitz  # PyMuPDF
import docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import difflib
import requests as http_requests  # for CV download
from datetime import datetime
from utils.email_util import send_email_to_mentor

router = APIRouter()

class MatchRequest(BaseModel):
    menteeId: str
    course: str
    preferredDays: List[str]
    preferredHours: List[str]
    expectations: Optional[str] = ""

class MatchSelection(BaseModel):
    menteeId: str
    mentorId: Optional[str] = None
    course: str  # החלק הזה יוחלף בקורס שהתאים בפועל
    preferredDays: List[str]
    preferredHours: List[str]
    expectations: Optional[str] = ""

def extract_text_from_pdf(url):
    response = http_requests.get(url)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(response.content)
        tmp_file.flush()
        doc = fitz.open(tmp_file.name)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
    return text

def extract_text_from_docx(url):
    response = http_requests.get(url)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
        tmp_file.write(response.content)
        tmp_file.flush()
        doc = docx.Document(tmp_file.name)
        return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_cv(url):
    if url.endswith(".pdf"):
        return extract_text_from_pdf(url)
    elif url.endswith(".docx"):
        return extract_text_from_docx(url)
    return ""

def calculate_cv_score(expectations, cv_text):
    if not expectations or not cv_text:
        return 0

    keywords = [w.strip() for w in expectations.split(",")]
    score_fuzzy = 0
    for kw in keywords:
        matches = difflib.get_close_matches(kw, cv_text.split(), cutoff=0.7)
        if matches:
            score_fuzzy += 5

    try:
        tfidf = TfidfVectorizer().fit_transform([expectations, cv_text])
        cosine_sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        score_semantic = cosine_sim * 20
    except:
        score_semantic = 0

    return min(score_fuzzy + score_semantic, 20)

@router.post("/api/match-mentors")
def match_mentors(data: MatchRequest):
    try:
        if not ObjectId.is_valid(data.menteeId):
            raise HTTPException(status_code=400, detail="ID לא תקין")

        if not data.course.strip():
            return []

        day_map = {
            "א": "ראשון", "ב": "שני", "ג": "שלישי", "ד": "רביעי", "ה": "חמישי",
            "ראשון": "ראשון", "שני": "שני", "שלישי": "שלישי", "רביעי": "רביעי", "חמישי": "חמישי"
        }
        preferred_days_normalized = [day_map.get(day, day) for day in data.preferredDays]

        mentors = list(users.find({
            "role": "mentor",
            "mentorStatus": "available",
            "mentorAmountQuota": {"$gt": 0}
        }))

        matching_mentors = []

        for mentor in mentors:
            score = 0
            mentor_courses = mentor.get("mentoringCourses", [])

            matched_course = None
            for c in mentor_courses:
                if re.search(data.course, c, re.IGNORECASE):
                    matched_course = c
                    break
                if difflib.get_close_matches(data.course, [c], cutoff=0.7):
                    matched_course = c
                    break

            if not matched_course:
                continue

            common_days = set(preferred_days_normalized) & set(mentor.get("availableDays", []))
            score += len(common_days) * 20

            common_hours = set(data.preferredHours) & set(mentor.get("availableHours", []))
            score += len(common_hours) * 10

            if data.expectations and mentor.get("cvUrl"):
                try:
                    cv_text = extract_text_from_cv(mentor["cvUrl"])
                    score += calculate_cv_score(data.expectations, cv_text)
                except:
                    pass

            mentor_image = mentor.get("image", "")
            mentor_mime = mentor.get("imageMimeType", "")
            mentor_picture = f"data:{mentor_mime};base64,{mentor_image}" if mentor_image and mentor_mime else ""

            matching_mentors.append({
                "mentorId": str(mentor["_id"]),
                "mentorName": mentor.get("fullName", ""),
                "mentorPicture": mentor_picture,
                "description": mentor.get("description", ""),
                "courses": mentor_courses,
                "availableDays": mentor.get("availableDays", []),
                "availableHours": mentor.get("availableHours", []),
                "score": min(score, 100),
                "matchedCourse": matched_course
            })

        sorted_mentors = sorted(matching_mentors, key=lambda x: x["score"], reverse=True)

        if not sorted_mentors:
            now = datetime.utcnow()
            requests.insert_one({
                "menteeId": ObjectId(data.menteeId),
                "course": data.course,
                "preferredDays": data.preferredDays,
                "preferredHours": data.preferredHours,
                "expectations": data.expectations,
                "mentorId": None,
                "status": "noMatch",
                "createdAt": now,
                "updatedAt": now
            })

        return sorted_mentors

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/select-mentor")
def select_mentor(data: MatchSelection):
    try:
        if not ObjectId.is_valid(data.menteeId):
            raise HTTPException(status_code=400, detail="menteeId לא תקין")

        mentor_object_id = ObjectId(data.mentorId) if data.mentorId and ObjectId.is_valid(data.mentorId) else None

        matched_mentor = users.find_one({"_id": mentor_object_id}) if mentor_object_id else None

        matched_course = ""
        if matched_mentor:
            for c in matched_mentor.get("mentoringCourses", []):
                if re.search(data.course, c, re.IGNORECASE):
                    matched_course = c
                    break
                if difflib.get_close_matches(data.course, [c], cutoff=0.7):
                    matched_course = c
                    break

        now = datetime.utcnow()

        new_request = {
            "menteeId": ObjectId(data.menteeId),
            "mentorId": mentor_object_id,
            "course": matched_course or data.course,
            "preferredDays": data.preferredDays,
            "preferredHours": data.preferredHours,
            "expectations": data.expectations,
            "status": "in progress" if mentor_object_id else "noMatch",
            "createdAt": now,
            "updatedAt": now
        }

        requests.insert_one(new_request)

        if matched_mentor and matched_mentor.get("mentorAmountQuota", 0) > 0:
            new_quota = matched_mentor["mentorAmountQuota"] - 1
            new_status = "available" if new_quota > 0 else "unavailable"
            users.update_one(
                {"_id": mentor_object_id},
                {"$set": {"mentorAmountQuota": new_quota, "mentorStatus": new_status}}
            )

            mentee_user = users.find_one({"_id": ObjectId(data.menteeId)})
            mentee_name = mentee_user.get("fullName", "חניך ללא שם") if mentee_user else "חניך לא מזוהה"
            send_email_to_mentor(str(mentor_object_id), mentee_name, matched_course or data.course)

        return {"message": "Mentor request saved successfully."}

    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=str(e))
