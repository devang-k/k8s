 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: Footer.js  
 * Description: This file is responsible to show footer in all pages 
 *  
 * Author: [Author's Name]  
 * Created On: [Creation Date]  
 *  
 * Revision History:  
 * - [Date] [Modifier's Name]: [JIRA Id]:[Summary of changes made]  
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
 ***************************************************************************/

import React from 'react';
import { Link } from 'react-router-dom';

function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="footer fw-bold app-primary-color text-center text-light sticky-bottom">
      &copy; {currentYear} SiClarity. All rights reserved. |
      <Link 
        to="/privacy-policy" 
        className="text-light ms-2"
        target="_blank"
        rel="noopener noreferrer"
      >
        Privacy Policy
      </Link> |
      <Link 
        to="/terms-and-conditions" 
        className="text-light ms-2"
        target="_blank"
        rel="noopener noreferrer"
      >
        Terms and Conditions
      </Link>
    </footer>
  );
}

export default Footer;
