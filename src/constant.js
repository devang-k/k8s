 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: constant.js  
 * Description: This file contains all the constant values used throughout the application 
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

export const hostName = process.env.REACT_APP_API_URL;
export const pageSize = 20;
export const pageNumber = 0;
export const adminPageSize = 25;
export const userPageSize = 100;
export const webSocketHostName = process.env.REACT_APP_WEBSOCKET_API_URL;
export const isDebugModeOn = process.env.REACT_APP_DEBUG === "true"? true : false; // here converting string value to boolean
export const version = process.env.REACT_APP_VERSION;
export const netlistDirType = "netlist"
export const techFileDirType = "tech"
export const globalFile = "GLOBAL"
export const userFile = "USER"
export const normalProjectType = 0;
export const RLBasedPOCProject = 1;
export const TwoHunderedPlusTransistorProject = 2;
export const projectTypeLookup = {
    [normalProjectType]: " ",
    [RLBasedPOCProject]: "RL",
    [TwoHunderedPlusTransistorProject]: "200+"
};
export const applicationTitle = "SiVista R.2025.06.0000";
export const filterOperators = [">", "<", "=", "<=", ">=", "!=","between"];
export const productName ="SiVista"
export const currentAppVersion = process.env.REACT_APP_CURRENT_APP_VERSION || 2;