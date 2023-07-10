#!/bin/bash

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
fi

sleep 5

SQL_DELETE_TABLE_1="DROP TABLE afkKeys"
SQL_DELETE_TABLE_2="DROP TABLE users"
SQL_DELETE_TABLE_3="DROP TABLE financialEntities"

# Execute the SQL statements inside the container
docker exec -it "$POSTGRES_CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    -c "$SQL_DELETE_TABLE_1" \
    -c "$SQL_DELETE_TABLE_2" \
    -c "$SQL_DELETE_TABLE_3" \

#-------------------MongoDB Container-------------------
MONGO_CONTAINER_NAME="afk-system-mongo"
MONGO_PORT=27018
MONGO_DATABASE="transactions_db"
COLLECTION_NAME="transactions"

# Check if the container is already running
if [[ "$(docker ps -a -q -f name=$MONGO_CONTAINER_NAME)" ]]; then
    echo "MongoDB container is already running"
    docker start $MONGO_CONTAINER_NAME
fi

sleep 5

docker exec -it $MONGO_CONTAINER_NAME mongo $MONGO_DATABASE --eval "db.$COLLECTION_NAME.drop()" --quiet