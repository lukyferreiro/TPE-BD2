#!/bin/bash

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
fi

sleep 5

# Define the SQL statements to create the tables
SQL_DELETE_TABLE_1="DROP TABLE accounts"

# Execute the SQL statements inside the container
docker exec -it "$POSTGRES_CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    -c "$SQL_DELETE_TABLE_1" \