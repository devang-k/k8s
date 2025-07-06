
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: RefreshHandler.js  
 * Description: This file is responsible to navigate user to home page on refresh 
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

import { useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";

const RefreshHandler = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (location.pathname === '/') {
        return; // No popup on login page
      }
      e.preventDefault();
      e.returnValue = ""; // This triggers the default confirmation dialog
    };

    const handlePageHide = () => {
      sessionStorage.setItem("reload", "true");
    };

    // Only add the beforeunload and pagehide events if the user is not on the home page
    if (location.pathname !== '/home' &&
      location.pathname !== '/privacy-policy' &&
      location.pathname !== '/terms-and-conditions' &&
      location.pathname !== '' &&
      !location.pathname.startsWith('/admin-settings')) {
      window.addEventListener("beforeunload", handleBeforeUnload);
      window.addEventListener("pagehide", handlePageHide);
    }

    // Check if the user has refreshed the page
    if (sessionStorage.getItem("reload") === "true") {
      sessionStorage.removeItem("reload");
      navigate("/home");
    }

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
      window.removeEventListener("pagehide", handlePageHide);
    };
  }, [navigate, location.pathname]);

  return children;
};

export default RefreshHandler;
