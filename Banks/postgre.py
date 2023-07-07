import psycopg2

connection = psycopg2.connect(
    host="localhost",
    database="your_database",
    user="your_user",
    password="your_password"
)