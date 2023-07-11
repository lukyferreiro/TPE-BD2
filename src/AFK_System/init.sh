#!/bin/bash

pip install fastapi uvicorn psycopg2 pymongo pydantic pydantic[email] requests

#-------------------PostgreSQL Container-------------------
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
    userId SERIAL NOT NULL PRIMARY KEY, \
    name TEXT NOT NULL, \
    password TEXT NOT NULL, \
    email TEXT NOT NULL UNIQUE, \
    isBusiness BOOLEAN NOT NULL DEFAULT FALSE \
  );"
  SQL_CREATE_TABLE_2="CREATE TABLE IF NOT EXISTS financialEntities ( \
    financialId VARCHAR(7) NOT NULL PRIMARY KEY CHECK (LENGTH(financialId) = 7), \
    name TEXT NOT NULL, \
    apiLink TEXT NOT NULL \
  );"
  SQL_CREATE_TABLE_3="CREATE TABLE IF NOT EXISTS afkKeys ( \
    userId INT NOT NULL, \
    financialId VARCHAR(7) NOT NULL CHECK (LENGTH(financialId) = 7), \
    value TEXT NOT NULL UNIQUE, \
    FOREIGN KEY (userId) REFERENCES users (userId) ON DELETE CASCADE, \
    FOREIGN KEY (financialId) REFERENCES financialEntities (financialId) ON DELETE CASCADE \
  );"

  # TODO: Modify according to your codespace. Remove last "/"
  API_LINK_1="https://lukyferreiro-potential-cod-qgjg5w6qv7fpqj-8001.preview.app.github.dev"
  SQL_INSERT_FINANCIAL_ENTITY_1="INSERT INTO financialEntities (financialId, name, apiLink) VALUES ('1111111', 'Santander', '$API_LINK_1')"

  API_LINK_2="..."
  SQL_INSERT_FINANCIAL_ENTITY_2="INSERT INTO financialEntities (financialId, name, apiLink) VALUES ('2222222', 'BBVA', '$API_LINK_2')"

  API_LINK_3="..."
  SQL_INSERT_FINANCIAL_ENTITY_2="INSERT INTO financialEntities (financialId, name, apiLink) VALUES ('3333333', 'Galicia', '$API_LINK_3')"

  # Execute the SQL statements inside the container
  docker exec -it "$POSTGRES_CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    -c "$SQL_CREATE_TABLE_1" \
    -c "$SQL_CREATE_TABLE_2" \
    -c "$SQL_CREATE_TABLE_3" \
    -c "$SQL_INSERT_FINANCIAL_ENTITY_1" \
    -c "$SQL_INSERT_FINANCIAL_ENTITY_2" \
    -c "$SQL_INSERT_FINANCIAL_ENTITY_3" 

#-------------------MongoDB Container-------------------
MONGO_CONTAINER_NAME="afk-system-mongo"
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

docker exec -it $MONGO_CONTAINER_NAME mongosh $MONGO_DATABASE --eval "db.$COLLECTION_NAME.createIndex({ userId_from: 1 })" --quiet