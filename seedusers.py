from pymongo import MongoClient

uri = "mongodb+srv://papaAdmin:mama1234!@papa-mongodb.global.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"
client = MongoClient(uri)

try:
    print(client.list_database_names())
    print("✅ חיבור תקין!")
except Exception as e:
    print(f"❌ שגיאה: {e}")
print("✅ Connected!")
print("Databases:", client.list_database_names())
