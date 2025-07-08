"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: tests.py  
 * Description:  Test cases
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
import json
from src.Apps.user.Login.models import User

#python .\manage.py test .\src\Apps\project\CreateProject\

class CREATEProjecTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        User.objects.create(name='MANSI MAHADIK',username='MANSI01',email='mansi@123.com',password='827CCB0EEA8A706C4C34A16891F84E7B',is_active=True)
        #self.token=''
        self.headers = {'Authorization':'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzIxMzAyMDMwLCJpYXQiOjE3MjEzMDAyMzAsImp0aSI6ImM2M2IyYjc4ODg2ZTRhZDlhZmVlYjE0Mzg5Njk5NjdkIiwidXNlcl9pZCI6NX0.neL-k7UME3Ko4wRseWHSswy_MEmaWjfuPwTre5SL0Ac'}

    def get_jwt_token(self):
         pass
    
    

    def test_create_project(self):
        url = reverse('Create')  # Assuming 'json-view' is the name of your URL pattern

        # Prepare JSON data to send in the POST request
        json_data = {
                        "project_name": "project18",
                        "action" : "Layout",
                        "netlist_metadata": {
                            "netlist_file_name": "test2.spice",
                            "netlist_type": "Global",
                            "cell_selections": 
                                [
                                {"cell_name":"INVD4", "is_selected": True },
                                {"cell_name": "MUX", "is_selected": False},
                                {"cell_name": "SUB_CELL", "is_selected": True}
                                ]
                            },
                        "tech_metadata": {
                            "file_name": "abc.tech",
                            "type": "global",
                            "file_contents": "SSDDKK__DD##DD",
                            "tech_selections": {
                            }
                        },
                        "file_contents": "b'.global vdd gnd\n\n.subckt AND2X1 Y B vdd gnd A\nM0 a_2_6# A vdd vdd pmos w=0.5u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \nM1 vdd B a_2_6# vdd pmos w=0.5u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \nM2 Y a_2_6# vdd vdd pmos w=0.5u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \nM3 a_9_6# A a_2_6# gnd nmos w=0.5u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \nM4 gnd B a_9_6# gnd nmos w=0.5u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \nM5 Y a_2_6# gnd gnd nmos w=0.25u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \n.ends AND2X1\n\n.subckt AND2X2 vdd gnd A B Y\nM0 a_2_6# A vdd vdd pmos w=0.5u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \nM1 vdd B a_2_6# vdd pmos w=0.5u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \nM2 Y a_2_6# vdd vdd pmos w=1u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \nM3 a_9_6# A a_2_6# gnd nmos w=0.5u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \nM4 gnd B a_9_6# gnd nmos w=0.5u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \nM5 Y a_2_6# gnd gnd nmos w=0.5u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \n.ends AND2X2\n'"
                    }
        json_payload = json.dumps(json_data)
        response = self.client.post(url, data=json_payload, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        jdata=response.json()
        print(jdata)
        self.assertEqual(jdata['Message'], 'Project created Successfully.')

    
class EDITProjecTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        User.objects.create(name='MANSI MAHADIK',username='MANSI01',email='mansi@123.com',password='827CCB0EEA8A706C4C34A16891F84E7B',is_active=True)
        #self.token=''
        self.headers = {'Authorization':'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzIxMzAyMDMwLCJpYXQiOjE3MjEzMDAyMzAsImp0aSI6ImM2M2IyYjc4ODg2ZTRhZDlhZmVlYjE0Mzg5Njk5NjdkIiwidXNlcl9pZCI6NX0.neL-k7UME3Ko4wRseWHSswy_MEmaWjfuPwTre5SL0Ac'}

    def test_edit_project(self):
        url = reverse('Edit')  # Assuming 'json-view' is the name of your URL pattern

        # Prepare JSON data to send in the POST request
        json_data = {
                        "project_name": "project18",
                        "action" : "Layout",
                        "netlist_metadata": {
                            "file_name": "test2.spice",
                            "type": "global",
                            "cell_selections": 
                                [
                                {"cell_name":"INVD4", "is_selected": True },
                                {"cell_name": "MUX", "is_selected": False},
                                {"cell_name": "SUB_CELL", "is_selected": True}
                                ]
                            },
                        "tech_metadata": {
                            "file_name": "abc.tech",
                            "type": "global",
                            "file_contents": "SSDDKK__DD##DD",
                            "tech_selections": {
                            }
                        },
                        "netlist_file_contents": "b'.global vdd gnd\n\n.subckt AND2X1 Y B vdd gnd A\nM0 a_2_6# A vdd vdd pmos w=0.5u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \nM1 vdd B a_2_6# vdd pmos w=0.5u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \nM2 Y a_2_6# vdd vdd pmos w=0.5u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \nM3 a_9_6# A a_2_6# gnd nmos w=0.5u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \nM4 gnd B a_9_6# gnd nmos w=0.5u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \nM5 Y a_2_6# gnd gnd nmos w=0.25u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \n.ends AND2X1\n\n.subckt AND2X2 vdd gnd A B Y\nM0 a_2_6# A vdd vdd pmos w=0.5u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \nM1 vdd B a_2_6# vdd pmos w=0.5u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \nM2 Y a_2_6# vdd vdd pmos w=1u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \nM3 a_9_6# A a_2_6# gnd nmos w=0.5u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \nM4 gnd B a_9_6# gnd nmos w=0.5u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \nM5 Y a_2_6# gnd gnd nmos w=0.5u l=0.05u\n+ ad=0p pd=0u as=0p ps=0u \n.ends AND2X2\n'",
                        "tech_file_contents": "sample content"
                    }
        json_payload = json.dumps(json_data)
        response = self.client.post(url, data=json_payload, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        jdata=response.json()
        print(jdata)