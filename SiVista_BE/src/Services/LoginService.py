# /***************************************************************************  
#  * Copyright © 2024 SiClarity, Inc.  
#  * All rights reserved.  
#  *  
#  * File Name: LoginService.py  
#  * Description: Service to maintain functions for validating Login module apis
#  *  
#  * Author: Mansi Mahadik 
#  * Created On: 17-12-2024
#  *  
#  * This source code and associated materials are the property of SiClarity, Inc.  
#  * Unauthorized copying, modification, distribution, or use of this software,  
#  * in whole or in part, is strictly prohibited without prior written permission  
#  * from SiClarity, Inc.  
#  *  
#  * Disclaimer:  
#  * This software is provided "as is," without any express or implied warranties,  
#  * including but not limited to warranties of merchantability, fitness for a  
#  * particular purpose, or non-infringement. In no event shall SiClarity, Inc.  
#  * be held liable for any damages arising from the use of this software.  
#  *  
#  * SiClarity and its logo are trademarks of SiClarity, Inc.  
#  *  
#  * For inquiries, contact: support@siclarity.com  
#  ***************************************************************************/
import hashlib
from src.Apps.user.Login.models import User
from django.contrib.auth import authenticate

def PassCheck(User, password):
    result = hashlib.md5(password.encode())
    if User.password==result.hexdigest().upper():
        return True
    else:
        return False
          
def CheckUser(user):
    return User.objects.filter(username=user).first()
    
def IsActive(user):
    return user.is_active

def IsDeleted(user):
    return user.is_deleted

def getPassword(Password):
    result = hashlib.md5(Password.encode())
    password=result.hexdigest().upper()
    return password
