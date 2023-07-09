#!/bin/bash

pip install fastapi uvicorn psycopg2 pymongo pydantic

#-------------------PostgreSQL Container-------------------

# Define the Docker container and PostgreSQL connection details
POSTGRES_CONTAINER_NAME="bank-system-postgres"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="my_password"
POSTGRES_DB="my_database"
export PGPASSWORD="$POSTGRES_PASSWORD"

# Check if the container is already created
if docker ps -a -q -f "name=$POSTGRES_CONTAINER_NAME" --format '{{.Names}}' | grep -q "$POSTGRES_CONTAINER_NAME"; then
    echo "Starting existing PostgreSQL container..."
    docker start "$POSTGRES_CONTAINER_NAME"
else
  # Container does not exist, create and run it
  echo "Creating and running PostgreSQL container..."
  docker run -d --name "$POSTGRES_CONTAINER_NAME" \
    -e POSTGRES_USER="$POSTGRES_USER" \
    -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
    -e POSTGRES_DB="$POSTGRES_DB" \
    -p 5434:5432 \
    postgres
  sleep 10
fi

sleep 5

  # Define the SQL statements to create the tables
  SQL_CREATE_TABLE_1="CREATE TABLE IF NOT EXISTS accounts ( \
    CBU TEXT NOT NULL PRIMARY KEY, \
    username TEXT NOT NULL, \
    balance DECIMAL NOT NULL, \
    AFK_key TEXT UNIQUE  \
  );"

  SQL_INSERT_ACCOUNT_1="INSERT INTO accounts (cbu, username, balance, AFK_key) VALUES ('1111111000000000000000', 'Lucas', 1500, null)"
  SQL_INSERT_ACCOUNT_2="INSERT INTO accounts (cbu, username, balance, AFK_key) VALUES ('1111111000000000000001', 'Roman', 783, null)"
  SQL_INSERT_ACCOUNT_3="INSERT INTO accounts (cbu, username, balance, AFK_key) VALUES ('1111111000000000000002', 'Tomas', 1000, null)"
  SQL_INSERT_ACCOUNT_4="INSERT INTO accounts (cbu, username, balance, AFK_key) VALUES ('1111111000000000000003', 'Cecilia', 19462, null)"
  SQL_INSERT_ACCOUNT_5="INSERT INTO accounts (cbu, username, balance, AFK_key) VALUES ('1111111000000000000004', 'Ariel', 2000, null)"
  SQL_INSERT_ACCOUNT_6="INSERT INTO accounts (cbu, username, balance, AFK_key) VALUES ('1111111000000000000005', 'Roberto', 0, null)"

  # Execute the SQL statements inside the container
  docker exec -it "$POSTGRES_CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c "$SQL_CREATE_TABLE_1" \
  -c "$SQL_INSERT_ACCOUNT_1" \
  -c "$SQL_INSERT_ACCOUNT_2" \
  -c "$SQL_INSERT_ACCOUNT_3" \
  -c "$SQL_INSERT_ACCOUNT_4" \
  -c "$SQL_INSERT_ACCOUNT_5" \
  -c "$SQL_INSERT_ACCOUNT_6" 
