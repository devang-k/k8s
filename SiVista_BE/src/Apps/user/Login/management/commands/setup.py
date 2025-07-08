"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: setup.py  
 * Description: setup file for setting up admin users, project types and tech parameters
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
from sys import stdout
from django.core.management.base import BaseCommand
from src.Apps.user.Login.models import User
from src.Apps.project.ProjectManager.models import ProjectType, TechInfo, TechDetailedInfo
from SiVista_BE.setup_support import tech_detailed_info_data, tech_info_data, project_types, ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_USERNAME, NAME
from django.utils import timezone
from src.Services.LoginService import getPassword


class Command(BaseCommand):
    help = 'Create the admin user if it does not already exist'

    def handle(self, *args, **kwargs):
        # Create the admin user if it doesn't already exist
        if not User.objects.filter(username=ADMIN_USERNAME).exists():
            if not User.objects.filter(email=ADMIN_EMAIL).exists():
                User.objects.create(
                    username=ADMIN_USERNAME,
                    email=ADMIN_EMAIL,
                    password=getPassword(ADMIN_PASSWORD),
                    name=NAME,
                    is_superuser=True,
                    is_staff=True,
                    is_deleted=False,
                    is_active=True
                )
                self.stdout.write(self.style.SUCCESS("Admin user created successfully."))
            else:
                self.stdout.write(self.style.WARNING(f"User with email id {ADMIN_EMAIL} already exists."))
        else:
            self.stdout.write(self.style.WARNING("Admin user already exists. Skipping creation."))

        # Insert project types if they don't already exist
        for name, p_type, variation in project_types:
            if not ProjectType.objects.filter(name=name, type=p_type).exists():
                ProjectType.objects.create(
                    name=name,
                    type=p_type,
                    variation=variation,
                    created_date=timezone.now(),
                    modified_date=timezone.now(),
                    created_by_id=1,  # Assuming '1' is the ID of the admin user
                    modified_by_id=1  # Assuming '1' is the ID of the admin user
                )
                self.stdout.write(self.style.SUCCESS(f"Inserted project type: {name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Project type '{name}' already exists. Skipping insertion."))

        # Insert TechInfo if they don't already exist
        for id, name, support_variation, non_support_variation, support_ui_visible, non_support_ui_visible, parameter_support_variation, display_name, header in tech_info_data:
            if not TechInfo.objects.filter(name=name).exists():
                TechInfo.objects.create(
                    id=id,
                    name=name,
                    support_variation=support_variation,
                    non_support_variation=non_support_variation,
                    support_ui_visible=support_ui_visible,
                    non_support_ui_visible=non_support_ui_visible,
                    parameter_support_variation=parameter_support_variation,
                    display_name=display_name,
                    header=header
                )
                self.stdout.write(self.style.SUCCESS(f"Inserted TechInfo: {name}"))
            else:
                self.stdout.write(self.style.WARNING(f"TechInfo '{name}' already exists. Skipping insertion."))

        # Insert TechDetailedInfo if they don't already exist
        for id,name, display_name, unit, description, options, options_display_name, options_description, project_type, parameter_type_id, status, support_variation, ui_visible, negative_start_allowed, negative_end_allowed, stepper_float, stepper, minStart, maxStart, minEnd, maxEnd, defaultStartValue, defaultEndValue, startPercentage, endPercentage in tech_detailed_info_data:
            if not TechDetailedInfo.objects.filter(name=name, parameter_type_id=parameter_type_id, project_type=project_type).exists():
                TechDetailedInfo.objects.create(
                    id=id,
                    name=name,
                    diplay_name=display_name,
                    unit=unit,
                    description=description,
                    options=options,
                    options_display_name=options_display_name,
                    options_description=options_description,
                    project_type=project_type,
                    parameter_type_id=parameter_type_id,
                    status=status,
                    support_variation=support_variation,
                    ui_visible=ui_visible,
                    negative_start_allowed=negative_start_allowed,
                    negative_end_allowed=negative_end_allowed, 
                    stepper_float=stepper_float, 
                    stepper=stepper,
                    minStart=minStart,
                    maxStart=maxStart,
                    minEnd=minEnd,
                    maxEnd=maxEnd,
                    defaultStartValue=defaultStartValue,
                    defaultEndValue=defaultEndValue,
                    startPercentage=startPercentage,
                    endPercentage=endPercentage
                    
                )
                self.stdout.write(self.style.SUCCESS(f"Inserted TechDetailedInfo: {name}"))
            else:
                self.stdout.write(self.style.WARNING(f"TechDetailedInfo '{name}' already exists. Skipping insertion."))