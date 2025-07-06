
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: AdminContext.js  
 * Description: This file is responsible to save admin netlist, tech file data to context 
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

import { createContext, useContext } from "react"

export const AdminContext = createContext({
  adminNetlistFileData: null, // stores list of admin netlist file
  setAdminNetlistFileData: () => null,
  userNetlistFileContent: null, // stores user netlist file content
  setUserNetlistFileContent: () => null,
  adminTechFileData: null,// stores list of admin tech file
  setAdminTechFileData: () => null,
  userTechFileContent: null, // stores user tech file content 
  setUserTechFileContent: () => null,
  defultNetlistContent: {},
  setDefaultNetlistContent: () => null

})
export const useAdminContext = () => {
  return useContext(AdminContext);
}