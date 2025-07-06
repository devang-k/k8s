 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: LayoutGraphProvider.js  
 * Description: This file is responsible to share stage 1 & stage 2 (Layout generation & Hyper expressivity) graph data to other components within the application. 
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
import { LayoutGraphContext } from "./LayoutGraphContext";

export const LayoutGraphProvider = ({ children }) => {
    const [stage1GraphData, setStage1GraphData] = useState(null);
    const [stage2GraphData, setStage2GraphData] = useState(null);

    const value = useMemo(() => ({
        stage1GraphData,
        setStage1GraphData,
        stage2GraphData,
        setStage2GraphData
    }), [stage1GraphData, setStage1GraphData, stage2GraphData, setStage2GraphData]);

    return (
        <LayoutGraphContext.Provider value={value}>
            {children}
        </LayoutGraphContext.Provider>
    );
};
