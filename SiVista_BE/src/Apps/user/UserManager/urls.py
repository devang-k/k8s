"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: urls.py  
 * Description: Each of these routes is associated with a class-based view that provides functionality for user management, such as viewing details, listing users, creating new users, updating user information, and updating passwords.
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
from src.Apps.user.UserManager.views import CreateUser, UpdateUser, UserDetails, UserList,PasswordUpdate


urlpatterns = [
    path('details/',UserDetails.as_view(), name='UserDetails'),
    path('list/',UserList.as_view(), name='UserList'),
    path('create/',CreateUser.as_view(), name='CreateUser'),
    path('modify/<int:uid>/', UpdateUser.as_view(), name='UpdateUser'), 
    path('password/update/',PasswordUpdate.as_view(),name='PasswordUpdate')
    ]