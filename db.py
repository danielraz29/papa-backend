from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()  # יטען את .env בעת ריצה מקומית

mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["papa-production"]  # שם הדאטהבייס שלך בענן

users = db["users"]
requests = db["mentorshipRequests"]
meetings = db["meetings"]
