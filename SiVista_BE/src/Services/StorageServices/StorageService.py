"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: StorageService.py  
 * Description: Select storage prefrance local or s3 if not provided then abstact functions will be called
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
from SiVista_BE.settings import STORAGE_TYPE
from src.Services.StorageServices.BaseService import BaseService
from src.Services.StorageServices.LocalService import LocalService
from src.Services.StorageServices.S3Service import S3Service
from src.Services.StorageServices.GCSService import GCSService

storage_servicer = None
if STORAGE_TYPE.lower() == 's3':
    storage_servicer = S3Service()
elif STORAGE_TYPE.lower() == 'local':
    storage_servicer = LocalService()
elif STORAGE_TYPE.lower() == 'gcs':
    storage_servicer = GCSService()
else:
    storage_servicer = BaseService()