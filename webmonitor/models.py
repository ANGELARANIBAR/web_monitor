from django.db import models
from django.utils import timezone

class Website(models.Model):
    url = models.URLField(max_length=500, unique=True)
    name = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name or self.url
    
    class Meta:
        ordering = ['name', 'url']

class MonitoringResult(models.Model):
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('error', 'Error'),
        ('timeout', 'Timeout'),
        ('connection_error', 'Connection Error'),
    ]
    
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='monitoring_results')
    status_code = models.IntegerField(null=True, blank=True)
    response_time = models.FloatField(help_text='Response time in seconds')
    load_time = models.FloatField(help_text='Page load time in seconds')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    screenshot_path = models.CharField(max_length=500, blank=True, null=True)
    
    def __str__(self):
        return f'{self.website.url} - {self.status} - {self.timestamp}'
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['website', '-timestamp']),
            models.Index(fields=['status', '-timestamp']),
        ]

class MonitoringStats(models.Model):
    website = models.OneToOneField(Website, on_delete=models.CASCADE, related_name='stats')
    total_checks = models.IntegerField(default=0)
    successful_checks = models.IntegerField(default=0)
    failed_checks = models.IntegerField(default=0)
    average_response_time = models.FloatField(default=0.0)
    average_load_time = models.FloatField(default=0.0)
    last_check = models.DateTimeField(null=True, blank=True)
    uptime_percentage = models.FloatField(default=0.0)
    
    def __str__(self):
        return f'Stats for {self.website.url}'
    
    def update_stats(self):
        # Get last 100 results without slicing first
        all_results = self.website.monitoring_results.all()
        results = list(all_results[:100])  # Convert to list to avoid queryset issues
        
        if results:
            self.total_checks = len(results)
            self.successful_checks = len([r for r in results if r.status == 'success'])
            self.failed_checks = len([r for r in results if r.status in ['error', 'timeout', 'connection_error']])
            
            successful_results = [r for r in results if r.status == 'success']
            if successful_results:
                self.average_response_time = sum(r.response_time for r in successful_results) / len(successful_results)
                self.average_load_time = sum(r.load_time for r in successful_results) / len(successful_results)
            
            self.uptime_percentage = (self.successful_checks / self.total_checks * 100) if self.total_checks > 0 else 0
            self.last_check = results[0].timestamp if results else None
            self.save()
