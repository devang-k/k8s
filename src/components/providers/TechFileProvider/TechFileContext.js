 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: TechFileContext.js  
 * Description: This file is responsible to save Tech file content in context 
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

export const TechFileContext = createContext({
    techFileData:{},
    setTechFileData:()=>null,
    isTechFileSelected:false,
    setIsTechFileSelected:()=>null,
    selectedTechFileName:"",
    setSelectedTechFileName:()=>null,
    selectedTechFileType:"",
    setSelectedTechFileType:()=> null,
    isTechDataChanged: false,
    setIsTechDataChanged: () => null,
    defaultTechFileData: {}, // stores the default techfile data 
    setDefaultTechFileData : () => null,
    techParameterValueError : [], // stores error in techfile page while user is updating parameter values
    setTechParameterValueError : () => {},
    projectTechFileListData: [], // stores the list of project tech file
    setProjectTechFileListData : () => null,
    viewProjectTechFile: false,  // handle project tech file button
    setViewProjectTechFile : () => null,
    isTechFileProjectSaved: false, // handle the rename tech file project
    setIsTechFileProjectSaved: () => null,
});

export const useTechFileContext = () =>{
    return useContext(TechFileContext);
};