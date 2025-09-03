import time
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webmonitor_project.settings')
django.setup()

from webmonitor.services.monitoring_service import WebMonitoringService

def run_monitoring_cycle():
    print('Starting monitoring cycle...')
    service = WebMonitoringService()
    results = service.monitor_all_websites()
    print(f'Monitoring completed! Processed {len(results)} websites')
    service.cleanup()
    return len(results)

if __name__ == '__main__':
    print('Web Monitoring Service - Direct Mode')
    print('Press Ctrl+C to stop')
    
    try:
        while True:
            run_monitoring_cycle()
            print('Waiting 60 seconds before next cycle...')
            time.sleep(60)  # Wait 60 seconds between cycles
    except KeyboardInterrupt:
        print('\nMonitoring stopped by user')
