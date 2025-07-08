"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: consumers.py  
 * Description: The JobConsumer class handles WebSocket connections for job-related communication, enabling clients to send and receive messages, join/leave specific channels, and close the connection when a special message is received. 
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
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class JobConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.job_id = self.scope['url_route']['kwargs']['job_id']
        self.room_group_name = f'job_{self.job_id}'
        # Join room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        
    async def disconnect(self, close_code):
        # Leave room
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # This is to handle data sent from the client to the web socket group
        print('received from client:', text_data)
        await self.send(text_data=json.dumps({
            'message': text_data
        }))

    # Receive message from the group
    async def job_message(self, event):
        message = event['message']
        status = event['status']
        if message == "__close__":
            # If we receive a special close message, close the WebSocket connection
            await self.close()
        else:
            # Send message to WebSocket
            await self.send(text_data=json.dumps({
                'message': message,
                'status': status
            })
        )