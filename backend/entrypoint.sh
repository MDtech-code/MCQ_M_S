#!/bin/sh

# wait for MySQL to be ready
echo "Waiting for MySQL..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.5
done
echo "MySQL is up - executing command"



python manage.py runserver 0.0.0.0:8000