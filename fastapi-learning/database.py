import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("MONGO_DB", "taskdb")

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

users_collection = db["users"]
tasks_collection = db["tasks"]
