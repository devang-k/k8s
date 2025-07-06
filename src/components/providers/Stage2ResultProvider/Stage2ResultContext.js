
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: Stage2ResultContext.js  
 * Description: This file is responsible to save stage 2 result (Hyper Expressivity) data 
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
export const Stage2ResultContext = createContext({
    stage2Result: {}, // Use a more generic name
    setStage2Result: () => { }, // Function to update the result
    isUserOnStage2Page: false, // this is true when user is on stage2results page
    setIsUserOnStage2Page: () => { },
    stage2RunResultSummaryData: {},   // stores stage2 run result summary data
    setStage2RunResultSummaryData: () => null,
    stage2GdsLayoutImageData: [], // stores stage2 gds image data
    setStage2GdsLayoutImageData: () => null,
    stage2TotalGDSNumber: 0,  //store the generated GDS
    setStage2TotalGDSNumber: () => null,
});

// Custom hook to use the Stage2ResultContext
export const useStage2ResultContext = () => {
    return useContext(Stage2ResultContext);
};
