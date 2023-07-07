from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["transactions_db"]
collection = db["transactions"]