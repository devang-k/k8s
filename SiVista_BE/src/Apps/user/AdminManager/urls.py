"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: urls.py  
 * Description: 
The urlpatterns list defines URL routes for various views in a Django application, handling file uploads, deletions, modifications, and retrieving file and technology data. Each path is associated with a corresponding class-based view to perform specific actions like uploading, modifying, or deleting files.
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
from src.Apps.user.AdminManager.views import GetList,UploadNetlist, DeleteFile,UploadTech, ModifyFile,GetTechData, RenameFile,DeleteFile, CloneFile


urlpatterns = [
    path('netlist/upload/',UploadNetlist.as_view(), name='UploadNetlist'),
    # path('delete/file/',DeleteFile.as_view(), name='DeleteFile'),
    path('modify/file/',ModifyFile.as_view(),name='ModifyFile'),
    path('tech/upload/',UploadTech.as_view(),name='UploadTech'),
    path('getlist/', GetList.as_view(),name='GetFileList'),
    path('getdata/',GetTechData.as_view(),name='GetTechData'),
    path('rename/file/',RenameFile.as_view(),name='RenameFile'),
    path('delete/file/',DeleteFile.as_view(),name='DeleteFile'),
    path('clone/file/',CloneFile.as_view(),name='CloneFile'),
    ]