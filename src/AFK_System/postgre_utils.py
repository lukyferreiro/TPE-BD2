import psycopg2

connection = psycopg2.connect(
    host="localhost",
    port=5433,
    database="my_database",
    user="postgres",
    password="my_password"
)