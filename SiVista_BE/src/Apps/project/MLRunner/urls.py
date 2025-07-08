"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: urls.py  
 * Description:This code defines the URL patterns for the MLRunner app, mapping HTTP requests to specific views that handle job-related operations, such as running projects, listing running jobs, viewing job details, and clearing results.
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
from django.urls import path
from src.Apps.project.MLRunner.views import *

urlpatterns = [
    path('project/', RunProject.as_view(), name='RunProject'),
    path('list/', JobList.as_view(), name='RunningJobList'),
    path('job/<int:jid>/', JobDetails.as_view(), name='JobDetails'),
    path('clear/result/', ClearResult.as_view(), name='ClearResult'),
]