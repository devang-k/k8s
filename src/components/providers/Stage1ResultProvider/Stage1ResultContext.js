
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: Stage1ResultContext.js  
 * Description: This file is responsible to save stage 1 result (Layout Generation) data 
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

import { createContext, useContext } from "react";

// Create a context for stage 2 results
export const Stage1ResultContext = createContext({
    stage1Result: {}, // Use a more generic name
    setStage1Result: () => {}, // Function to update the result
    selectedGdsItems: [], // Holds selected items
    setSelectedGdsItems: () => {}, // Function to update selected items
    stage1CellInfo : null,
    setStage1CellInfo : () => null,
    isGdsSelectAllChecked: false,
    setIsGdsSelectAllChecked: () => null,
    stage1RunResultSummaryData: {}, // stores stage1 run result summary data
    setStage1RunResultSummaryData: () => null,
    stage1GdsLayoutImageData: [], // stores stage1 gds image data
    setStage1GdsLayoutImageData: () => null,
    stage1TotalGDSNumber: 0, // store the generatedGDS number
    setStage1TotalGDSNumber: () => null,
});

// Custom hook to use the Stage2ResultContext
export const useStage1ResultContext = () => {
    return useContext(Stage1ResultContext);
};
