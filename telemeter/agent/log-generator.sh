#!/bin/bash

NODE_LOG="/var/log/node/app.log"
REDIS_LOG="/var/log/redis/redis.log"
MYSQL_LOG="/var/log/mysql/mysql.log"

INTERVAL=1

# Ensure directories exist
mkdir -p /var/log/node
mkdir -p /var/log/redis
mkdir -p /var/log/mysql

touch $NODE_LOG $REDIS_LOG $MYSQL_LOG

mkdir -p /var/log/node /var/log/redis /var/log/mysql
touch $NODE_LOG $REDIS_LOG $MYSQL_LOG

while true; do
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")
    PID=$((RANDOM % 9000 + 1000))
    RAND=$((RANDOM % 100))

    if [ $RAND -lt 80 ]; then
        echo "$TIMESTAMP INFO pid=$PID request processed successfully" >> $NODE_LOG

    elif [ $RAND -lt 95 ]; then
        echo "$TIMESTAMP WARN cache miss for key=user_$PID" >> $REDIS_LOG

    else
        echo "$TIMESTAMP ERROR pid=$PID query failed due to timeout" >> $MYSQL_LOG
    fi

    sleep $INTERVAL
done