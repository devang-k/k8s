"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: urls.py  
 * Description: This file defines the URL routing configurations for the application. It maps URLs to specific views or functions that handle the HTTP requests. 

                Key sections and functionality include:
                
                1. **URL Patterns**:
                   - This section defines the list of URL patterns that the application recognizes. Each pattern corresponds to a specific view, which is responsible for processing the request and returning an appropriate response.
                   - Patterns can be simple (mapping a URL directly to a view) or more complex (including path parameters, regex patterns, and URL converters).
                
                2. **View Mappings**:
                   - Each URL pattern is associated with a view, which contains the logic to process the request. Views can be functions or class-based views that execute when a request matches a particular URL pattern.
                
                3. **Namespace and Include**:
                   - If the application has multiple modules or apps, `urls.py` can include or namespace URLs from other files. This makes it easy to organize URLs in larger applications and maintain a modular structure.
                   - The `include()` function is typically used to reference the `urls.py` of other apps, allowing each app to manage its own URLs independently.

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
from django.contrib import admin
from django.urls import path,include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from src.Apps.user.Login.views import CustomTokenRefreshView
from rest_framework import permissions
 
schema_view = get_schema_view(
    openapi.Info(
        title="My API",
        default_version='v1',
        description="My API description",
        terms_of_service="https://www.example.com/terms/",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
 
 
 
urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('src.Apps.user.Login.urls')),
    path('project/', include('src.Apps.project.ProjectManager.urls')),
    path('stage/', include('src.Apps.project.StageManager.urls')),
    path('netlist/', include('src.Apps.netlist.NetlistManager.urls')),
    path('tech/', include('src.Apps.tech.TechManager.urls')),
    path('run/', include('src.Apps.project.MLRunner.urls')),
    path('administrator/', include('src.Apps.user.AdminManager.urls')),
    path('profile/',include('src.Apps.user.UserManager.urls')),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]