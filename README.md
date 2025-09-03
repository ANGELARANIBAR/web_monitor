# Django Web Monitoring Dashboard

A real-time web monitoring system built with Django, Selenium, and Celery.

## Features

- Real-time website monitoring using Selenium WebDriver
- Response time and load time tracking
- HTTP status code monitoring (200, 404, etc.)
- Uptime percentage calculation
- Beautiful dashboard with Bootstrap UI
- WebSocket support for real-time updates
- Background task processing with Celery
- Screenshot capture for failed pages

## Prerequisites

- Python 3.8+
- Redis server
- Microsoft Edge browser
- msedgedriver.exe (included)

## Installation

1. Activate the virtual environment:
   ```bash
   .\venv\Scripts\Activate.ps1
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run migrations:
   ```bash
   python manage.py migrate
   ```

4. Load websites from JSON:
   ```bash
   python manage.py shell -c "from webmonitor.services.monitoring_service import WebMonitoringService; service = WebMonitoringService(); service.load_websites_from_json(
urls-o.json); service.cleanup()"
   ```

## Running the Application

### Option 1: Manual Start (Recommended for Development)

1. Start Redis server:
   ```bash
   redis-server
   ```

2. Start Celery worker (in a new terminal):
   ```bash
   celery -A webmonitor_project worker --loglevel=info
   ```

3. Start Celery beat for periodic tasks (in a new terminal):
   ```bash
   celery -A webmonitor_project beat --loglevel=info
   ```

4. Start Django server:
   ```bash
   python manage.py runserver
   ```

5. Open your browser and go to: http://127.0.0.1:8000

### Option 2: Using the Startup Script

Run the startup script:
```bash
./start_monitoring.sh
```

## Usage

1. **Load Websites**: Click "Load URLs" to import websites from urls-o.json
2. **Start Monitoring**: Click "Start Monitoring" to begin real-time monitoring
3. **View Dashboard**: The dashboard shows:
   - Total websites count
   - Online/Offline status
   - Average uptime percentage
   - Individual website cards with:
     - Response time
     - Load time
     - Uptime percentage
     - Last check timestamp

## API Endpoints

- `GET /api/websites/` - Get all websites with stats
- `POST /api/monitoring/` - Start monitoring all websites
- `POST /api/load-websites/` - Load websites from JSON file
- `GET /api/monitoring/?website_id=X` - Get monitoring results

## Configuration

The monitoring service is configured in `webmonitor/services/monitoring_service.py`:
- Page load timeout: 30 seconds
- Screenshot capture for successful loads
- Headless browser mode for performance
- Image and CSS loading disabled for faster monitoring

## Monitoring Features

- **Response Time**: HTTP request response time
- **Load Time**: Full page load time using Selenium
- **Status Codes**: HTTP status codes (200, 404, 500, etc.)
- **Error Tracking**: Connection errors, timeouts, and page load errors
- **Uptime Calculation**: Percentage of successful checks
- **Screenshot Capture**: Automatic screenshots for failed pages

## File Structure

```
django/
 webmonitor_project/          # Django project settings
 webmonitor/                  # Main monitoring app
    models.py               # Database models
    views.py                # API views
    services/               # Monitoring service
    tasks.py                # Celery tasks
    consumers.py            # WebSocket consumers
 templates/webmonitor/       # HTML templates
 static/                     # Static files
 urls-o.json                # Website URLs to monitor
 msedgedriver.exe           # Edge WebDriver
 requirements.txt           # Python dependencies
```

## Troubleshooting

1. **Redis Connection Error**: Make sure Redis server is running
2. **WebDriver Error**: Ensure msedgedriver.exe is in the project root
3. **Permission Errors**: Run as administrator if needed
4. **Port Conflicts**: Change ports in settings.py if needed

## Admin Interface

Access the Django admin at: http://127.0.0.1:8000/admin/
- Create superuser: `python manage.py createsuperuser`
- Manage websites, monitoring results, and statistics

## Performance Notes

- Monitoring runs in headless mode for better performance
- Images and CSS are disabled during monitoring
- Results are cached and updated every 30 seconds
- WebSocket provides real-time updates without page refresh
