"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: models.py  
 * Description: These models form the backbone of a project/job management system where users can create and manage projects, jobs associated with them, and store detailed technical and file information. The Project model connects with Job, FileInfo, TechInfo, and other related models, allowing for a rich and flexible system with extensive relationships between entities.
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
from django.db import models
from django.contrib.postgres.fields import ArrayField
from src.Apps.user.Login.models import User
from SiVista_BE.settings import VERSION
import uuid

class Project(models.Model):
    project_name = models.CharField(max_length=200, null=False)
    is_published = models.BooleanField(default=False, null=False)
    netlist_metadata = models.JSONField(null=True)
    tech_metadata = models.JSONField(null=True)
    action = models.IntegerField()
    selectedLayouts=ArrayField(models.CharField(max_length=100), null=True, blank=True, default=None)
    project_type=models.IntegerField()
    stage_one_project= models.IntegerField(null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_projects')
    modified_date = models.DateTimeField(auto_now=True, null=True)
    modified_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='modified_projects', null=True,blank=True)
    version = models.IntegerField(default=VERSION)

    class Meta:
        db_table = 'PROJECT'

class Job(models.Model):
    STATUS_CHOICES = [
        ('QUEUED', 'Queued'),
        ('RUNNING', 'Running'),
        ('FAILED', 'Failed'),
        ('COMPLETED', 'Completed'),
        ('DELETED','Deleted')
    ]
    ACTION_CHOICES = [
        (1, 'Stage1'),  # LAYOUT_GENERATION
        (2, 'Stage2'),  # HYPEREXPRESSIVITY
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='jobs')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='QUEUED')
    log = models.TextField(blank=True, null=True)
    command = models.TextField()
    action = models.IntegerField()
    cells = ArrayField(models.CharField(max_length=100), blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_jobs')
    created_date = models.DateTimeField(auto_now_add=True)
    process_id = models.IntegerField(blank=True, null=True)
    input = models.JSONField()
    output = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'JOB'

class FileInfo(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('DELETED','Deleted'),
    ]
    DIR_CHOICES=[
        ('GLOBAL','Global'),
        ('USER','User'),
        ('UNDIFINED','Undifined'),
    ]
    name=models.CharField(max_length=200, blank=False, null=False)
    type=models.CharField(max_length=200, blank=False, null=False)
    dir=models.CharField(max_length=10, choices=DIR_CHOICES, default='UNDIFINED',blank=False, null=False)
    status=models.CharField(max_length=10, choices=STATUS_CHOICES, default='DELETED',blank=False, null=False)
    filesize = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_fileinfo',blank=False, null=False)
    modified_date = models.DateTimeField(null=True, blank=True)
    modified_by = models.ForeignKey(User, on_delete=models.CASCADE,related_name='modified_fileinfo',null=True, blank=True)

    class Meta:
        db_table = 'FILEINFO'

class ProjectType(models.Model):
    name=models.CharField(max_length=20)
    type=models.IntegerField(unique=True)
    variation=models.BooleanField(default=False, null=False)
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_project_type',blank=False, null=False)
    modified_date = models.DateTimeField(null=True, blank=True)
    modified_by = models.ForeignKey(User, on_delete=models.CASCADE,related_name='modified_project_type',null=True, blank=True)

    class Meta:
        db_table = 'ProjectType'

class TechInfo(models.Model):
    name=models.CharField(max_length=50,unique=True,null=False)
    display_name=models.CharField(max_length=50,null=True)
    support_variation=models.BooleanField(default=False, null=False)
    non_support_variation=models.BooleanField(default=False, null=False)
    support_ui_visible=models.BooleanField(default=False, null=False)
    non_support_ui_visible=models.BooleanField(default=False, null=False)
    parameter_support_variation=models.BooleanField(default=False, null=False)
    header= ArrayField(models.CharField(max_length=100), blank=True, null=True)    

    class Meta:
        db_table = 'TechInfo'

class TechDetailedInfo(models.Model):
    name=ArrayField(models.CharField(max_length=100), blank=False, null=True)
    diplay_name=ArrayField(models.CharField(max_length=100), blank=False, null=True)
    unit=models.CharField(max_length=10, null=True, blank=True)
    description=models.CharField(max_length=500, null=True, blank=True)
    options=ArrayField(models.CharField(max_length=100), blank=False, null=True)
    options_display_name=ArrayField(models.CharField(max_length=100), blank=False, null=True)
    options_description=ArrayField(models.CharField(max_length=500), blank=False, null=True)
    project_type=models.IntegerField(null=False)
    parameter_type=models.ForeignKey(TechInfo, on_delete=models.CASCADE,null=False, blank=False)
    support_variation=models.BooleanField(default=False, null=False)
    ui_visible=models.BooleanField(default=False, null=False)
    status=models.BooleanField(default=False, null=False)
    negative_start_allowed=models.BooleanField(default=False, null=False, unique=False)
    negative_end_allowed=models.BooleanField(default=False, null=False, unique=False)
    stepper_float=models.BooleanField(default=False)
    stepper=models.FloatField(default=1, null=True, blank=False)
    minStart=models.IntegerField(default=None, null=True, blank=False)
    maxStart=models.IntegerField(default=None, null=True, blank=False)
    minEnd=models.IntegerField(default=None, null=True, blank=False)
    maxEnd=models.IntegerField(default=None, null=True, blank=False)
    defaultStartValue=models.IntegerField(default=None, null=True, blank=False)
    defaultEndValue=models.IntegerField(default=None, null=True, blank=False)
    startPercentage=models.IntegerField(default=None, null=True, blank=False)
    endPercentage=models.IntegerField(default=None, null=True, blank=False)
    class Meta:
        db_table = 'TechDetailedInfo'

class TechFileCatalog(models.Model):

    STATUS_CHOICES = [
        ('QUEUED', 'Queued'),
        ('RUNNING', 'Running'),
        ('FAILED', 'Failed'),
        ('COMPLETED', 'Completed'),
        ('DELETED','Deleted'),
        ('UNPROCESSED','Unprocessed'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tech_files')
    action = models.IntegerField(null=False)
    job_id = models.CharField(max_length=100, null=True, blank=True)
    cell_name = models.CharField(max_length=100, null=True, blank=True)
    file_name = models.CharField(max_length=255, null=False)
    tech_data = models.JSONField(null=True, blank=True)
    drc_count = models.IntegerField(null=True, blank=True)
    lvs_count = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=11, choices=STATUS_CHOICES, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tech_files')

    class Meta:
        db_table = 'TechFileCatalog'

    #     indexes = [
    #         models.Index(fields=['project_id']),
    #         models.Index(fields=['status']),
    #         models.Index(fields=['created_at']),
    #     ]
    #     unique_together = ('project_id', 'file_name')

    # def __str__(self):
    #     return f"{self.project} - {self.file_name} (Status: {self.status})"