import time
import os
import json
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from django.conf import settings
from django.utils import timezone
from webmonitor.models import Website, MonitoringResult, MonitoringStats
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class WebMonitoringService:
    def __init__(self):
        self.driver = None
    
    def _create_private_driver(self):
        """Create a private/incognito WebDriver instance"""
        try:
            edge_options = Options()
            
            # Private/Incognito mode - no cookies, cache, or data storage
            edge_options.add_argument("--incognito")
            edge_options.add_argument("--headless")
            edge_options.add_argument("--no-sandbox")
            edge_options.add_argument("--disable-dev-shm-usage")
            edge_options.add_argument("--disable-gpu")
            edge_options.add_argument("--window-size=1920,1080")
            
            # Disable all data storage and tracking
            edge_options.add_argument("--disable-web-security")
            edge_options.add_argument("--disable-features=VizDisplayCompositor")
            edge_options.add_argument("--disable-extensions")
            edge_options.add_argument("--disable-plugins")
            edge_options.add_argument("--disable-images")
            edge_options.add_argument("--disable-javascript")
            edge_options.add_argument("--disable-css")
            edge_options.add_argument("--disable-background-timer-throttling")
            edge_options.add_argument("--disable-renderer-backgrounding")
            edge_options.add_argument("--disable-backgrounding-occluded-windows")
            edge_options.add_argument("--disable-ipc-flooding-protection")
            
            # Clear all data and prevent storage
            prefs = {
                "profile.default_content_setting_values": {
                    "cookies": 2,
                    "images": 2,
                    "javascript": 2,
                    "plugins": 2,
                    "popups": 2,
                    "geolocation": 2,
                    "notifications": 2,
                    "media_stream": 2,
                },
                "profile.managed_default_content_settings": {
                    "images": 2,
                    "cookies": 2,
                    "javascript": 2,
                },
                "profile.default_content_settings": {
                    "popups": 0,
                    "cookies": 2,
                }
            }
            edge_options.add_experimental_option("prefs", prefs)
            
            # Additional privacy settings
            edge_options.add_argument("--disable-blink-features=AutomationControlled")
            edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            edge_options.add_experimental_option("useAutomationExtension", False)
            
            service = Service(settings.SELENIUM_DRIVER_PATH)
            driver = webdriver.Edge(service=service, options=edge_options)
            driver.set_page_load_timeout(30)
            
            # Execute script to remove webdriver property
            driver.execute_script("Object.defineProperty(navigator, \"webdriver\", {get: () => undefined})")
            
            return driver
            
        except Exception as e:
            logger.error(f"Failed to create private WebDriver: {e}")
            return None
    
    def monitor_website_threaded(self, website):
        """Monitor a single website in a thread with private mode"""
        driver = None
        try:
            # Create a new private driver instance for each thread
            driver = self._create_private_driver()
            if not driver:
                return self._create_error_result(website, "WebDriver not available")
            
            start_time = time.time()
            response_time = 0
            load_time = 0
            status_code = None
            status = "error"
            error_message = None
            
            try:
                # HTTP request
                try:
                    response = requests.get(website.url, timeout=10, allow_redirects=True)
                    status_code = response.status_code
                    response_time = time.time() - start_time
                except requests.RequestException as e:
                    logger.warning(f"HTTP request failed for {website.url}: {e}")
                
                # Selenium monitoring
                selenium_start = time.time()
                driver.get(website.url)
                time.sleep(2)
                load_time = time.time() - selenium_start
                
                if "error" not in driver.title.lower() and driver.current_url:
                    status = "success"
                else:
                    status = "error"
                    error_message = f"Page load error: {driver.title}"
                
            except TimeoutException:
                status = "timeout"
                error_message = "Page load timeout (30 seconds)"
                load_time = 30.0
            except Exception as e:
                status = "error"
                error_message = f"Error: {str(e)}"
            
            # Create result
            result = MonitoringResult.objects.create(
                website=website,
                status_code=status_code,
                response_time=response_time,
                load_time=load_time,
                status=status,
                error_message=error_message,
                timestamp=timezone.now()
            )
            
            self._update_website_stats(website)
            return result
            
        except Exception as e:
            logger.error(f"Thread error for {website.url}: {e}")
            return self._create_error_result(website, f"Thread error: {str(e)}")
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    logger.error(f"Error closing driver: {e}")
    
    def monitor_all_websites(self):
        """Monitor all active websites using threading for faster execution"""
        websites = Website.objects.filter(is_active=True)
        results = []
        
        # Use ThreadPoolExecutor for parallel monitoring
        max_workers = min(len(websites), 5)  # Limit to 5 concurrent threads
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all monitoring tasks
            future_to_website = {
                executor.submit(self.monitor_website_threaded, website): website 
                for website in websites
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_website):
                website = future_to_website[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"Monitored {website.url}: {result.status}")
                except Exception as e:
                    logger.error(f"Failed to monitor {website.url}: {e}")
                    error_result = self._create_error_result(website, f"Thread execution error: {str(e)}")
                    results.append(error_result)
        
        return results
    
    def _create_error_result(self, website, error_message):
        result = MonitoringResult.objects.create(
            website=website,
            status="connection_error",
            error_message=error_message,
            timestamp=timezone.now()
        )
        self._update_website_stats(website)
        return result
    
    def _update_website_stats(self, website):
        try:
            stats, created = MonitoringStats.objects.get_or_create(website=website)
            stats.update_stats()
        except Exception as e:
            logger.error(f"Failed to update stats for {website.url}: {e}")
    
    def load_websites_from_json(self, json_file_path):
        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            urls = data.get("urls", [])
            created_count = 0
            
            for url in urls:
                website, created = Website.objects.get_or_create(
                    url=url,
                    defaults={"name": url.split("/")[-1] or url.split("/")[-2]}
                )
                if created:
                    created_count += 1
                    MonitoringStats.objects.create(website=website)
            
            logger.info(f"Loaded {len(urls)} URLs, created {created_count} new websites")
            return created_count
            
        except Exception as e:
            logger.error(f"Failed to load websites from {json_file_path}: {e}")
            return 0
    
    def cleanup(self):
        pass  # No cleanup needed for threaded approach
