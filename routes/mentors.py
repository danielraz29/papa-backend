from pymongo import MongoClient

client = MongoClient(
    "mongodb+srv://papaAdmin:mama1234!@papa-mongodb.mongocluster.cosmos.azure.com/?tls=true&retrywrites=false&authMechanism=SCRAM-SHA-256",
    tlsCAFile="/Users/danielraz/PycharmProjects/papa-backend/certs/azure.pem"
)

print(client.list_database_names())
