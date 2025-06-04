import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bson import ObjectId
from db import users
from dotenv import load_dotenv

load_dotenv()

# פונקציה לשליפת המייל של החונך לפי מזהה
def get_mentor_email(mentor_id):
    mentor = users.find_one({"_id": ObjectId(mentor_id)})
    if mentor:
        return mentor.get("gmail")  # מחזיר את המייל של החונך
    return None  # אם לא נמצא חונך

# פונקציה לשליחת מייל לחונך
def send_email_to_mentor(mentor_id, mentee_name, course_name):
    mentor_email = get_mentor_email(mentor_id)  # שליפת המייל של החונך ממסד הנתונים
    if not mentor_email:
        print("❌ לא נמצא מייל לחונך")
        return

    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")

    if not sender_email or not sender_password:
        print("❌ פרטי התחברות למייל חסרים בקובץ הסביבה .env")
        return

    subject = "נמצא לך חניך!"
    body = f"""
    שלום 👋,

    נמצא לך חניך חדש בשם {mentee_name} 🎓
    הקורס שבו הוא צריך עזרה הוא: {course_name}

    אנא התחבר למערכת כדי לראות את הפרטים המלאים.

    צוות פאפא 📚
    """

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = mentor_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)
        server.quit()
        print("✅ המייל נשלח בהצלחה")
    except Exception as e:
        print(f"❌ שגיאה בשליחת המייל: {e}")
