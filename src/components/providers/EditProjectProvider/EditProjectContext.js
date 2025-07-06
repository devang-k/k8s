 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: EditProjectContext.js  
 * Description: This file is responsible to save edited project data in context. 
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

export const EditProjectContext = createContext({
    isUserInEditMode: false,
    setIsUserInEditMode: () => null,
    userCreatedProjectList: null,
    setUserCreatedProjectList: () => null,
    isButtonDisabledInEditMode: false,
    setIsButtonDisabledInEditMode: () => null,
    showResultButtonInTechFileInEditMode: false,  // Enables the show result button in TechFile when results are generated.
    setShowResultButtonInTechFileInEditMode:() => null,
    showResultButtonInStage1ResultInEditMode : false, // Enables the show result button in Stage1Result when results are generated.
    setShowResultButtonInStage1ResultInEditMode: () => null,
})

export const useEditProjectContext = () => {
    return useContext(EditProjectContext);
};