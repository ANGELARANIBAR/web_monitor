#!/bin/bash
echo "Starting Django Web Monitor..."
echo ""
echo "1. Starting Redis server..."
redis-server &
sleep 3

echo "2. Starting Celery worker..."
celery -A webmonitor_project worker --loglevel=info &
sleep 3

echo "3. Starting Celery beat (scheduler)..."
celery -A webmonitor_project beat --loglevel=info &
sleep 3

echo "4. Starting Django development server..."
echo ""
echo "Dashboard will be available at: http://127.0.0.1:8000"
echo ""
python manage.py runserver
