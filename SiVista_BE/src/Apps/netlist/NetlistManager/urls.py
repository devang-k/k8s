"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: urls.py  
 * Description:The urlpatterns list defines the URL routing for two API views:

        /getlist/: This URL is mapped to the GetList view, which retrieves a list of netlist files. It is named getList.
        /getdata/: This URL is mapped to the GetData view, which handles POST requests to retrieve data for a specific netlist file. It is named getNetlistData.
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
from src.Apps.netlist.NetlistManager.views import GetList, GetData,ValidateNetlist


urlpatterns = [
    path('getlist/',GetList.as_view(),name='getList'),
    path('getdata/',GetData.as_view(),name='getNetlistData'),
    path('validate/',ValidateNetlist.as_view(),name='validateNetlist'),
    ]