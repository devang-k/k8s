"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: apps.py  
 * Description: This configuration is used to define the settings and behavior for the MLRunner app. It is typically included in the INSTALLED_APPS list in the Django settings file to ensure the app is initialized and ready for use. The default_auto_field ensures that all models in the app use a BigAutoField for primary keys by default. 
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
from django.apps import AppConfig


class MlrunnerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.Apps.project.MLRunner"