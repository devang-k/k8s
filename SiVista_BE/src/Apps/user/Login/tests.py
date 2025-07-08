"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: tests.py  
 * Description: Test cases for login api
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
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from src.Apps.user.Login.models import User
import json


#python .\manage.py test .\src\Apps\project\CreateProject\


class LoginTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        User.objects.create(name='MANSI MAHADIK',username='MANSI01',email='mansi@123.com',password='827CCB0EEA8A706C4C34A16891F84E7B',is_active=True)
        User.objects.create(name='MEGHA MAHADIK',username='MEGHA01',email='megha@123.com',password='827CCB0EEA8A706C4C34A16891F84E7B',is_active=False)

    
    def test_create_project_success(self):
        
        url = reverse('Login')  # Assuming 'json-view' is the name of your URL pattern

        
        # Prepare JSON data to send in the POST request
        json_data = {
                        'Username':'Mansi01',
                        'Password':'12345'
                    }
        json_payload = json.dumps(json_data)
        response = self.client.post(url, data=json_payload, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        jdata=response.json()
        self.assertEqual(jdata['message'], 'Success')
        print(jdata)
        return(jdata)
    
    def test_create_project_invalidcred(self):
        url = reverse('Login')  # Assuming 'json-view' is the name of your URL pattern

        # Prepare JSON data to send in the POST request
        json_data = {
                        'Username':'Mansi01',
                        'Password':'1234'
                    }
        json_payload = json.dumps(json_data)
        response = self.client.post(url, data=json_payload, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        jdata=response.json()
        self.assertEqual(jdata['message'], 'Invalid Credentials')

    def test_create_project_isactivef(self):
        url = reverse('Login')  # Assuming 'json-view' is the name of your URL pattern

        # Prepare JSON data to send in the POST request
        json_data = {
                        'Username':'MEGHA01',
                        'Password':'12345'
                    }
        json_payload = json.dumps(json_data)
        response = self.client.post(url, data=json_payload, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        jdata=response.json()
        self.assertEqual(jdata['message'], 'User MEGHA01 is inactive, kindly coordinate with Admin user.')       
        