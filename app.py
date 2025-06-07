from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth  # נניח שזה הקובץ ששלחת לי קודם
from routes import handleDashboardMentees
from routes import mentorSwipe
from routes import createMentor
from routes import adminMentorPage
from routes import meetingsPage
from routes import traineesPage
from routes import mentor_dashboard

app = FastAPI()

# הגדרות CORS כדי לאפשר קריאה מה-React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # אפשר לשים דומיין ספציפי כאן למשל "http://localhost:3000"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# רישום הנתיב של auth
app.include_router(auth.router)
app.include_router(mentorSwipe.router)
app.include_router(handleDashboardMentees.router)
app.include_router(createMentor.router)

app.include_router(adminMentorPage.router)
app.include_router(meetingsPage.router)
app.include_router(traineesPage.router)
app.include_router(mentor_dashboard.router)

# נקודת התחלה לבדיקת תקינות
@app.get("/")
def read_root():
    return {"message": "ברוך הבא למערכת פאפא (PAPA system)!"}
