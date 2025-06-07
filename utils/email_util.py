import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bson import ObjectId
from db import users
from dotenv import load_dotenv

load_dotenv()

# שליחת מייל כללי - משתמש בפונקציה הזו במקרים שונים (למשל סיסמה)
def send_email(to_email, subject, body):
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")

    if not sender_email or not sender_password:
        print("❌ פרטי התחברות למייל חסרים בקובץ .env")
        return

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)
        server.quit()
        print("✅ מייל נשלח ל:", to_email)
    except Exception as e:
        print(f"❌ שגיאה בשליחת המייל ל-{to_email}: {e}")


# פונקציה לשליפת המייל של החונך לפי מזהה
def get_mentor_email(mentor_id):
    mentor = users.find_one({"_id": ObjectId(mentor_id)})
    if mentor:
        return mentor.get("gmail")
    return None

# שליחת מייל על שיבוץ חניך (נשאר ללא שינוי)
def send_email_to_mentor(mentor_id, mentee_name, course_name):
    mentor_email = get_mentor_email(mentor_id)
    if not mentor_email:
        print("❌ לא נמצא מייל לחונך")
        return

    subject = "נמצא לך חניך!"
    body = f"""
שלום 👋,

נמצא לך חניך חדש בשם {mentee_name} 🎓
הקורס שבו הוא צריך עזרה הוא: {course_name}

אנא התחבר למערכת כדי לראות את הפרטים המלאים.

צוות פאפא 📚
"""
    send_email(mentor_email, subject, body)
