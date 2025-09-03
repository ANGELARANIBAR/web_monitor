import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from webmonitor.models import Website, MonitoringResult

class MonitoringConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "monitoring_updates"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.send_initial_data()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get("type")
        
        if message_type == "get_websites":
            await self.send_websites_data()
    
    async def send_initial_data(self):
        websites_data = await self.get_websites_data()
        await self.send(text_data=json.dumps({
            "type": "websites_data",
            "data": websites_data
        }))
    
    async def send_websites_data(self):
        websites_data = await self.get_websites_data()
        await self.send(text_data=json.dumps({
            "type": "websites_data", 
            "data": websites_data
        }))
    
    async def monitoring_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "monitoring_update",
            "data": event["data"]
        }))
    
    @database_sync_to_async
    def get_websites_data(self):
        websites = Website.objects.filter(is_active=True).prefetch_related("stats")
        data = []
        
        for website in websites:
            stats = website.stats
            latest_result = website.monitoring_results.first()
            
            website_data = {
                "id": website.id,
                "url": website.url,
                "name": website.name,
                "is_active": website.is_active,
                "stats": {
                    "total_checks": stats.total_checks,
                    "successful_checks": stats.successful_checks,
                    "failed_checks": stats.failed_checks,
                    "average_response_time": round(stats.average_response_time, 2),
                    "average_load_time": round(stats.average_load_time, 2),
                    "uptime_percentage": round(stats.uptime_percentage, 2),
                    "last_check": stats.last_check.isoformat() if stats.last_check else None,
                },
                "latest_result": {
                    "status": latest_result.status if latest_result else None,
                    "status_code": latest_result.status_code if latest_result else None,
                    "response_time": latest_result.response_time if latest_result else None,
                    "load_time": latest_result.load_time if latest_result else None,
                    "timestamp": latest_result.timestamp.isoformat() if latest_result else None,
                } if latest_result else None
            }
            data.append(website_data)
        
        return data
