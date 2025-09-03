from celery import shared_task
from django.utils import timezone
from webmonitor.services.monitoring_service import WebMonitoringService
from webmonitor.models import Website
import logging

logger = logging.getLogger(__name__)

@shared_task
def monitor_all_websites_task():
    try:
        service = WebMonitoringService()
        results = service.monitor_all_websites()
        service.cleanup()
        logger.info(f'Completed monitoring {len(results)} websites')
        return f'Monitored {len(results)} websites successfully'
    except Exception as e:
        logger.error(f'Error in monitor_all_websites_task: {e}')
        return f'Error: {str(e)}'

@shared_task
def monitor_single_website_task(website_id):
    try:
        website = Website.objects.get(id=website_id)
        service = WebMonitoringService()
        result = service.monitor_website(website)
        service.cleanup()
        logger.info(f'Monitored {website.url}: {result.status}')
        return f'Monitored {website.url} - Status: {result.status}'
    except Website.DoesNotExist:
        logger.error(f'Website with id {website_id} not found')
        return f'Website with id {website_id} not found'
    except Exception as e:
        logger.error(f'Error in monitor_single_website_task: {e}')
        return f'Error: {str(e)}'

@shared_task
def load_websites_from_json_task(json_file_path):
    try:
        service = WebMonitoringService()
        created_count = service.load_websites_from_json(json_file_path)
        service.cleanup()
        logger.info(f'Loaded websites from {json_file_path}')
        return f'Created {created_count} new websites from {json_file_path}'
    except Exception as e:
        logger.error(f'Error in load_websites_from_json_task: {e}')
        return f'Error: {str(e)}'
