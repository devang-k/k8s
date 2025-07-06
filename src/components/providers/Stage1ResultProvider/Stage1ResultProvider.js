
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: Stage1ResultProvider.js  
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

import React, { useMemo, useState } from "react";
import { Stage1ResultContext } from "./Stage1ResultContext";

// Provider component for managing stage 1 results
export const Stage1ResultProvider = ({ children }) => {
    const [stage1Result, setStage1Result] = useState({}); // Initialize as an empty object
    const [selectedGdsItems, setSelectedGdsItems] = useState([]);
    const [stage1CellInfo , setStage1CellInfo ] = useState();
    const [isGdsSelectAllChecked, setIsGdsSelectAllChecked] = useState(false)
    const [stage1RunResultSummaryData, setStage1RunResultSummaryData] = useState();
    const [stage1GdsLayoutImageData, setStage1GdsLayoutImageData] = useState([]);
    const [stage1TotalGDSNumber, setStage1TotalGDSNumber] = useState(null)

    const value = useMemo(() => ({
        stage1Result,
        setStage1Result,
        selectedGdsItems,
        setSelectedGdsItems,
        stage1CellInfo,
        setStage1CellInfo,
        isGdsSelectAllChecked,
        setIsGdsSelectAllChecked,
        stage1RunResultSummaryData,
        setStage1RunResultSummaryData,
        stage1GdsLayoutImageData,
        setStage1GdsLayoutImageData,
        stage1TotalGDSNumber,
        setStage1TotalGDSNumber,
    }), [stage1Result, setStage1Result, selectedGdsItems, setSelectedGdsItems, stage1CellInfo, setStage1CellInfo, isGdsSelectAllChecked, setIsGdsSelectAllChecked, stage1RunResultSummaryData, setStage1RunResultSummaryData, stage1GdsLayoutImageData, setStage1GdsLayoutImageData, stage1TotalGDSNumber, setStage1TotalGDSNumber]);

    return (
        <Stage1ResultContext.Provider value={value}>
            {children}
        </Stage1ResultContext.Provider>
    );
};
