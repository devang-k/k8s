"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: urls.py  
 * Description: StageResult: The URL /result/ will trigger the StageResult view. You would define the logic of this view (likely a class-based view) to return the stage results, likely in some specific format (JSON, HTML, etc.).
                CopyStage1Layouts: The URL /copy/ would be used for the functionality to copy Stage 1 layouts (for example, copying specific layouts from one stage to another).
                GetGDSJPG: The URL /gdsimg/ could be used to return a generated image from a GDS file in JPG format. The GetGDSJPG view would likely contain logic to convert or retrieve the image data from a GDS file.
                DownloadResult: The URL /download/result/ will handle requests to download a result (for example, project results, computations, or data files).
                DownloadGDS: The URL /download/gds/ would allow users to download a GDS file.
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
from src.Apps.project.StageManager.views import *


urlpatterns = [
    path('status/',StageStatus.as_view(),name='StageStatus'),
    path('result/', StageResult.as_view(), name='StageResult'),
    path('copy/', CopyStage1Layouts.as_view(), name='CopyStage1'),
    path('gdsimg/', GetGDSJPG.as_view(), name='GetGDSJPG'),
    path('download/result/', DownloadResult.as_view(), name='DownloadResult'),
    path('download/gds/', DownloadGDS.as_view(), name='DownloadGDS'),
    path('download/files/', DownloadFiles.as_view(), name='DownloadFiles'),
    path('summary/', Summary.as_view(), name='Summary'),
]