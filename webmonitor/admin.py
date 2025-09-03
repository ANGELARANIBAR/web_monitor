from django.contrib import admin
from .models import Website, MonitoringResult, MonitoringStats

@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'url']
    list_editable = ['is_active']

@admin.register(MonitoringResult)
class MonitoringResultAdmin(admin.ModelAdmin):
    list_display = ['website', 'status', 'status_code', 'response_time', 'load_time', 'timestamp']
    list_filter = ['status', 'status_code', 'timestamp']
    search_fields = ['website__name', 'website__url']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'

@admin.register(MonitoringStats)
class MonitoringStatsAdmin(admin.ModelAdmin):
    list_display = ['website', 'total_checks', 'successful_checks', 'uptime_percentage', 'last_check']
    list_filter = ['last_check']
    search_fields = ['website__name', 'website__url']
    readonly_fields = ['total_checks', 'successful_checks', 'failed_checks', 'average_response_time', 'average_load_time', 'uptime_percentage', 'last_check']
