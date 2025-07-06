 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: Stage2ResultProvider.js  
 * Description: This file is responsible to share stage 2 result (Hyper Expressivity) data to other components within the application. 
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

import React, { useMemo, useState } from "react";
import { Stage2ResultContext } from "./Stage2ResultContext";

// Provider component for managing stage 2 results
export const Stage2ResultProvider = ({ children }) => {
    const [stage2Result, setStage2Result] = useState({}); // Initialize as an empty object
    const [isUserOnStage2Page, setIsUserOnStage2Page] = useState(false); // this is true when user is on stage2results page
    const [stage2RunResultSummaryData, setStage2RunResultSummaryData] = useState();
    const [stage2GdsLayoutImageData, setStage2GdsLayoutImageData] = useState([]);
    const [stage2TotalGDSNumber, setStage2TotalGDSNumber ] = useState([])

    const value = useMemo(() => ({
        stage2Result,
        setStage2Result,
        isUserOnStage2Page,
        setIsUserOnStage2Page,
        stage2RunResultSummaryData, 
        setStage2RunResultSummaryData,
        stage2GdsLayoutImageData,
        setStage2GdsLayoutImageData ,
        stage2TotalGDSNumber, 
        setStage2TotalGDSNumber
    }), [stage2Result, setStage2Result, isUserOnStage2Page, setIsUserOnStage2Page, stage2RunResultSummaryData, setStage2RunResultSummaryData, stage2GdsLayoutImageData, setStage2GdsLayoutImageData, stage2TotalGDSNumber, setStage2TotalGDSNumber]);

    return (
        <Stage2ResultContext.Provider value={value}>
            {children}
        </Stage2ResultContext.Provider>
    );
};
