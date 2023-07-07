#!/bin/bash

pip install fastapi uvicorn psycopg2 pymongo

#-------------------PostgreSQL Container-------------------

# Define the Docker container and PostgreSQL connection details
POSTGRES_CONTAINER_NAME="afk-system-postgres"
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
    balance TEXT NOT NULL, \
    AFK_key TEXT UNIQUE  \
  );"
  

  # Execute the SQL statements inside the container
  docker exec -it "$POSTGRES_CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$SQL_CREATE_TABLE_1"