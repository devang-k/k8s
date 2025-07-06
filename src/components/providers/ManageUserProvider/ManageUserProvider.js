 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: ManageUserProvider.js  
 * Description: This file is responsible to share user data to other components within the application. 
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

import React, { useMemo, useState } from 'react';
import { ManageUserContext } from './ManageUserContext';

export const ManageUserProvider = ({ children }) => {
  const [userData, setUserData] = useState(null);
  const [loggingLevelOptions ,setLoggingLevelOptions] = useState([]);
  const [ totalUsersCount, setTotalUsersCount ] = useState(0);

  const value = useMemo(() => ({
    userData,
    setUserData,
    loggingLevelOptions,
    setLoggingLevelOptions,
    totalUsersCount,
    setTotalUsersCount
  }), [userData, setUserData, loggingLevelOptions, setLoggingLevelOptions,totalUsersCount,setTotalUsersCount]);

  return (
    <ManageUserContext.Provider value={value}>
      {children}
    </ManageUserContext.Provider>
  );
};
