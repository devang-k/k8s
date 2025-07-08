"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: celery.py  
 * Description: 1. **Django Settings Module**: This line sets the environment variable for the Django settings module. It's necessary for Celery to use the correct configuration and integrate with Django.
                2. **Celery Application Creation**: This creates the Celery application instance, which is the main object used to configure and manage task execution.
                3. **Loading Configuration from Django Settings**: Celery reads its configuration settings (like broker URL, task serialization, etc.) from the Django `settings.py` file, specifically those prefixed with `CELERY_`.
                4. **Autodiscover Tasks**: This enables Celery to automatically find and register tasks in any of the installed Django apps, making it scalable for complex applications.
                5. **Debug Task**: The `debug_task` is a simple test task, useful for verifying Celery is working correctly.
                This file configures Celery to work seamlessly within the Django application, handling background tasks asynchronously.
 *  
 * Author: Mansi Mahadik 
 * Created On: 17-12-2024
 *  
 * This source code and associated materials are the property of SiClarity, Inc.  
 * Unauthorized copying, modification, distribution, or use of this software,  
 * in whole or in part, is strictly prohibited without prior written permission  
 * from SiClarity, Inc.  
 *  
 * Disclaimer:  
 * This software is provided "as is," without any express or implied warranties,  
 * including but not limited to warranties of merchantability, fitness for a  
 * particular purpose, or non-infringement. In no event shall SiClarity, Inc.  
 * be held liable for any damages arising from the use of this software.  
 *  
 * SiClarity and its logo are trademarks of SiClarity, Inc.  
 *  
 * For inquiries, contact: support@siclarity.com  
 ***************************************************************************/"""
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SiVista_BE.settings')

# Create the Celery application.
app = Celery('SiVista_BE')

# Load task modules from all registered Django app configs.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks from all installed apps.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')