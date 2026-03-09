#!/bin/bash

NODE_LOG="/var/log/node/app.log"
REDIS_LOG="/var/log/redis/redis.log"
MYSQL_LOG="/var/log/mysql/mysql.log"

INTERVAL=1   # seconds between log entries

mkdir -p /var/log/node /var/log/redis /var/log/mysql
touch $NODE_LOG $REDIS_LOG $MYSQL_LOG

while true; do
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")
    PID=$((RANDOM % 9000 + 1000))
    RAND=$((RANDOM % 100))

    # 80% INFO
    if [ $RAND -lt 80 ]; then
        echo "$TIMESTAMP INFO pid=$PID request processed successfully" >> $NODE_LOG
    fi

    # 15% WARN
    if [ $RAND -ge 80 ] && [ $RAND -lt 95 ]; then
        echo "$TIMESTAMP WARN cache miss for key=user_$PID" >> $REDIS_LOG
    fi

    # 5% ERROR
    if [ $RAND -ge 95 ]; then
        echo "$TIMESTAMP ERROR pid=$PID query failed due to timeout" >> $MYSQL_LOG
    fi

    sleep $INTERVAL
done