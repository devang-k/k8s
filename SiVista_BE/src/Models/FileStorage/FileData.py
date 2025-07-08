"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: FileData.py  
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
class FileData:  
    def __init__(self, fileObj, fileName):
        self.fileObj = fileObj
        self.fileName = fileName
        self.fileBytes = fileObj.read()
        self.fileValidationConfigs = {
            'max_size_bytes': 10485760, #10MB
            'illegal_characters': {'/'}
        }
    
    def validate(self):
        passed = True
        errors = []
        # check for file size
        if self.fileObj.size > self.fileValidationConfigs['max_size_bytes']:
            passed = False
            errors.append('File is too large')
        # check for illegal characters in name
        if set(self.fileName) & self.fileValidationConfigs['illegal_characters']:
            passed = False
            errors.append('File name contains illegal characters')
        return {
            'passed': passed,
            'errors': ', '.join(errors)
        }