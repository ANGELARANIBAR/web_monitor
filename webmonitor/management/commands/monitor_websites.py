from django.core.management.base import BaseCommand
from webmonitor.tasks import monitor_all_websites_task

class Command(BaseCommand):
    help = 'Start monitoring all websites'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting website monitoring...'))
        task = monitor_all_websites_task.delay()
        self.stdout.write(self.style.SUCCESS(f'Monitoring task started with ID: {task.id}'))
