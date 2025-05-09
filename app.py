from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth  # נניח שזה הקובץ ששלחת לי קודם

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

# נקודת התחלה לבדיקת תקינות
@app.get("/")
def read_root():
    return {"message": "ברוך הבא למערכת פאפא (PAPA system)!"}
