"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: LoginResponse.py  
 * Description: Model for response
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
class LoginResponse:
    #Message>>str, Status>>str, Token>>str    
    def __init__(self,message,status,token=None) -> None:
        self.message=message
        self.status=status
        self.token=token

class LoginResponseAbout:
    #Message>>str, Status>>str, Token>>str    
    def __init__(self,message,status_code,status,data=None) -> None:
        self.message=message
        self.status_code=status_code
        self.status=status
        self.data=data