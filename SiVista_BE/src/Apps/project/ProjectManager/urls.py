"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: urls.py  
 * Description: Defines URL patterns for the ProjectManager app in Django. Each URL is mapped to a view class that handles the HTTP request and provides the necessary response. 
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
from src.Apps.project.ProjectManager.views import Create, ListProjects, GetProject, EditProject, CheckProject, Stage1Ready, DeleteProject, UploadProjectTech, ListTechFileCatalog, GetTechFileCatalogData, DownloadTechFile, RenameCatalogTechFile, SaveCatalogTechFile, MigrateApplication,DeleteCatalogTechFile


urlpatterns = [
    path('create/', Create.as_view(), name='Create'),
    path('list/', ListProjects.as_view(), name='GetAllProjects'),
    path('details/<int:pid>/', GetProject.as_view(), name='GetProjectDetails'),
    path('edit/<int:pid>/', EditProject.as_view(), name='Edit'),
    path('checkproject/', CheckProject.as_view(), name='CheckProject'),
    path('stage1_ready/', Stage1Ready.as_view(), name='ProjectsWithStage1Results'),
    path('delete/<int:pid>/', DeleteProject.as_view(), name='DeleteProject'),
    path('tech-upload/', UploadProjectTech.as_view(), name='TechFileUpload'),
    path('techfile/<int:pid>/', ListTechFileCatalog.as_view(), name='ListTechFileCatalog'),
    path('techfiledata/', GetTechFileCatalogData.as_view(), name='GetTechFileCatalogData'),
    path('downloadtech/', DownloadTechFile.as_view(), name='DownloadTechFile'),
    path('renametechfile/', RenameCatalogTechFile.as_view(), name='RenameCatalogTechFile'),
    path('savetecfile/', SaveCatalogTechFile.as_view(), name='SaveCatalogTechFile'),
    path('catalog/delete/<int:pid>/', DeleteCatalogTechFile.as_view(), name='DeleteCatalog'),
    path('migrate/', MigrateApplication.as_view(), name='MigrateApplication'),
]