from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27018")
db = client["transactions_db"]
collection = db["transactions"]