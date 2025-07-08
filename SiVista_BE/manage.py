#!/usr/bin/env python
# """/***************************************************************************  
#  * Copyright © 2024 SiClarity, Inc.  
#  * All rights reserved.  
#  *  
#  * File Name: manage.py  
#  * Description: Starting DJANGO application using this file.
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
#  ***************************************************************************/"""

"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SiVista_BE.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
