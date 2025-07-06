
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: NetListFileContext.js  
 * Description: This file is responsible to save netlist file data 
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

import { createContext, useContext } from 'react';

export const NetListContext = createContext({
    netListFileData:{},
    setNetListFileData:()=>null,
    selectedNetlistFileName:"",
    setSelectedNetlistFileName:()=>null,
    selectedNetlistFileType:"",
    setSelectedNetlistFileType:()=>null,
    netlistFileContent:"", 
    setNetlistFileContent:()=> null,
    netlistCellInfo:[], 
    setNetlistCellInfo:()=> null,
    isNetListFileSelected: false,
    setIsNetListFileSelected: () => null,
    actionSelected : 1,
    setActionSelected : () => null, 
    isSelectAllChecked: false,
    setIsSelectAllChecked:()=> null,
    isNetlistDataChanged: false,
    setIsNetlistDataChanged: () => null,
    defaultNetlistFileData: {}, // stores the default netlistfile data 
    setDefaultNetlistFileData: () => null,
    isNetlistFileContentDataChanged :false ,
    setIsNetlistFileContentDataChanged : () => null 
});

export const useNetListFileContext = () => {
    return useContext(NetListContext);
};