from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from webmonitor.models import Website, MonitoringResult, MonitoringStats
from webmonitor.services.monitoring_service import WebMonitoringService
import json
import logging

logger = logging.getLogger(__name__)

def dashboard(request):
    websites = Website.objects.filter(is_active=True).prefetch_related('stats')
    return render(request, 'webmonitor/dashboard.html', {'websites': websites})

@method_decorator(csrf_exempt, name='dispatch')
class WebsiteAPIView(View):
    def get(self, request):
        websites = Website.objects.filter(is_active=True).prefetch_related('stats')
        data = []
        
        for website in websites:
            stats = website.stats
            latest_result = website.monitoring_results.first()
            
            website_data = {
                'id': website.id,
                'url': website.url,
                'name': website.name,
                'is_active': website.is_active,
                'stats': {
                    'total_checks': stats.total_checks,
                    'successful_checks': stats.successful_checks,
                    'failed_checks': stats.failed_checks,
                    'average_response_time': round(stats.average_response_time, 2),
                    'average_load_time': round(stats.average_load_time, 2),
                    'uptime_percentage': round(stats.uptime_percentage, 2),
                    'last_check': stats.last_check.isoformat() if stats.last_check else None,
                },
                'latest_result': {
                    'status': latest_result.status if latest_result else None,
                    'status_code': latest_result.status_code if latest_result else None,
                    'response_time': latest_result.response_time if latest_result else None,
                    'load_time': latest_result.load_time if latest_result else None,
                    'timestamp': latest_result.timestamp.isoformat() if latest_result else None,
                } if latest_result else None
            }
            data.append(website_data)
        
        return JsonResponse({'websites': data})
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            website = Website.objects.create(
                url=data['url'],
                name=data.get('name', ''),
                is_active=data.get('is_active', True)
            )
            MonitoringStats.objects.create(website=website)
            
            return JsonResponse({
                'success': True,
                'message': 'Website added successfully',
                'website_id': website.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class MonitoringAPIView(View):
    def post(self, request):
        try:
            # Run monitoring directly without Celery
            service = WebMonitoringService()
            results = service.monitor_all_websites()
            service.cleanup()
            
            return JsonResponse({
                'success': True,
                'message': f'Monitoring completed! Processed {len(results)} websites',
                'results_count': len(results)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def get(self, request):
        website_id = request.GET.get('website_id')
        limit = int(request.GET.get('limit', 50))
        
        if website_id:
            results = MonitoringResult.objects.filter(website_id=website_id)[:limit]
        else:
            results = MonitoringResult.objects.all()[:limit]
        
        data = []
        for result in results:
            data.append({
                'id': result.id,
                'website_url': result.website.url,
                'website_name': result.website.name,
                'status': result.status,
                'status_code': result.status_code,
                'response_time': result.response_time,
                'load_time': result.load_time,
                'error_message': result.error_message,
                'timestamp': result.timestamp.isoformat(),
                'screenshot_path': result.screenshot_path
            })
        
        return JsonResponse({'results': data})

@method_decorator(csrf_exempt, name='dispatch')
class LoadWebsitesAPIView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            json_file = data.get('json_file', 'urls-o.json')
            
            # Run directly without Celery
            service = WebMonitoringService()
            created_count = service.load_websites_from_json(json_file)
            service.cleanup()
            
            return JsonResponse({
                'success': True,
                'message': f'Loaded {created_count} websites from {json_file}',
                'created_count': created_count
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

def website_detail(request, website_id):
    try:
        website = Website.objects.get(id=website_id)
        results = website.monitoring_results.all()[:100]
        
        paginator = Paginator(results, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        return render(request, 'webmonitor/website_detail.html', {
            'website': website,
            'page_obj': page_obj,
            'stats': website.stats
        })
    except Website.DoesNotExist:
        return JsonResponse({'error': 'Website not found'}, status=404)
