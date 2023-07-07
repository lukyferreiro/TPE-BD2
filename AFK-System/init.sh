#!/bin/bash

pip install fastapi uvicorn psycopg2 pymongo

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
    -p 5433:5432 \
    postgres
  sleep 10
fi

sleep 5

  # Define the SQL statements to create the tables
  SQL_CREATE_TABLE_1="CREATE TABLE IF NOT EXISTS users ( \
    id SERIAL NOT NULL PRIMARY KEY, \
    name TEXT NOT NULL, \
    password TEXT NOT NULL, \
    email TEXT NOT NULL UNIQUE, \
    isBusiness BOOLEAN NOT NULL DEFAULT FALSE \
  );"
  SQL_CREATE_TABLE_2="CREATE TABLE IF NOT EXISTS financial_entity ( \
    id SERIAL NOT NULL PRIMARY KEY, \
    apiLink TEXT NOT NULL \
  );"
  SQL_CREATE_TABLE_3="CREATE TABLE IF NOT EXISTS afk_keys ( \
    userId INT NOT NULL, \
    financialId INT NOT NULL, \
    keyValue TEXT NOT NULL, \
    keyType TEXT NOT NULL, \
    PRIMARY KEY(userId, financialId), \
    UNIQUE(keyType, keyValue), \
    FOREIGN KEY (userId) REFERENCES users (userId) ON DELETE CASCADE, \
    FOREIGN KEY (financialId) REFERENCES financial_entity (financialId) ON DELETE CASCADE \
  );"

  # Execute the SQL statements inside the container
  docker exec -it "$POSTGRES_CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    -c "$SQL_CREATE_TABLE_1" \
    -c "$SQL_CREATE_TABLE_2" \
    -c "$SQL_CREATE_TABLE_3" 


MONGO_CONTAINER_NAME="afk-mongo"
MONGO_PORT=27018
MONGO_DATABASE="transactions_db"
COLLECTION_NAME="transactions"

# Check if the container is already running
if [[ "$(docker ps -a -q -f name=$MONGO_CONTAINER_NAME)" ]]; then
    echo "MongoDB container is already running"
    docker start $MONGO_CONTAINER_NAME
else
    # Run the MongoDB container
    docker run -d --name $MONGO_CONTAINER_NAME -p $MONGO_PORT:27017 -e MONGO_INITDB_DATABASE=$MONGO_DATABASE mongo
    echo "MongoDB container started"
fi

sleep 5

docker exec -it $MONGO_CONTAINER_NAME mongosh $MONGO_DATABASE --eval "db.$COLLECTION_NAME.createIndex({ user_id: 1 })" --quiet