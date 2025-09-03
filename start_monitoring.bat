@echo off
echo Starting Django Web Monitor...
echo.
echo 1. Starting Redis server...
start "Redis" redis-server
timeout /t 3 /nobreak > nul

echo 2. Starting Celery worker...
start "Celery Worker" celery -A webmonitor_project worker --loglevel=info
timeout /t 3 /nobreak > nul

echo 3. Starting Celery beat (scheduler)...
start "Celery Beat" celery -A webmonitor_project beat --loglevel=info
timeout /t 3 /nobreak > nul

echo 4. Starting Django development server...
echo.
echo Dashboard will be available at: http://127.0.0.1:8000
echo.
python manage.py runserver

pause
