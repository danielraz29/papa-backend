from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes import auth
from routes import handleDashboardMentees
from routes import mentorSwipe
from routes import createMentor
from routes import adminMentorPage
from routes import meetingsPage
from routes import traineesPage
from routes import mentor_dashboard
from routes import createMentee

app = FastAPI()

# הגדרת Static Files עבור קבצי PDF של קורות חיים
app.mount("/temp_uploads", StaticFiles(directory="temp_uploads"), name="temp_uploads")

# הגדרות CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # מומלץ להחליף לדומיין מדויק בפרודקשן
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# רישום הנתיבים
app.include_router(auth.router)
app.include_router(mentorSwipe.router)
app.include_router(handleDashboardMentees.router)
app.include_router(createMentor.router)
app.include_router(createMentee.router)
app.include_router(adminMentorPage.router)
app.include_router(meetingsPage.router)
app.include_router(traineesPage.router)
app.include_router(mentor_dashboard.router)

# בדיקת תקינות ראשונית
@app.get("/")
def read_root():
    return {"message": "ברוך הבא למערכת פאפא (PAPA system)!"}
