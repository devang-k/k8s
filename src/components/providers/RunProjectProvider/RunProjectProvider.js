 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: RunProjectProvider.js  
 * Description: This file is responsible to share run project data to other components within the application. 
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

import React, { useMemo, useState } from "react"
import { RunProjectContext } from "./RunProjectContext"

export const RunProjectProvider = ({ children }) => {

    const [runLayoutJobId, setRunLayoutJobId] = useState();
    const [runLayoutRunningJobLogs, setRunLayoutRunningJobLogs] = useState([]);
    const [isRunningJobCompleted, setIsRunningJobCompleted] = useState(false);
    const [isRunJobErrored, setIsRunningJobErrored] = useState(false);
    const [listOfRunningJobsData, setListOfRunningJobsData] = useState();
    const [runningJobStatus, setRunningJobStatus] = useState(false);
    const [webSocketObj, setWebSocketObj] = useState(null);
    const [isProjectStillRunning,setIsProjectStillRunning] = useState(false);

    const value = useMemo(() => {
        return {
            runLayoutJobId,
            setRunLayoutJobId,
            runLayoutRunningJobLogs,
            setRunLayoutRunningJobLogs,
            isRunningJobCompleted,
            setIsRunningJobCompleted,
            isRunJobErrored,
            setIsRunningJobErrored,
            listOfRunningJobsData,
            setListOfRunningJobsData,
            runningJobStatus,
            setRunningJobStatus,
            webSocketObj,
            setWebSocketObj,
            isProjectStillRunning,
            setIsProjectStillRunning
        }
    }, [
        isProjectStillRunning,
        setIsProjectStillRunning,
        runLayoutJobId,
        setRunLayoutJobId,
        runLayoutRunningJobLogs,
        setRunLayoutRunningJobLogs,
        isRunningJobCompleted,
        setIsRunningJobCompleted,
        isRunJobErrored,
        setIsRunningJobErrored,
        listOfRunningJobsData,
        setListOfRunningJobsData,
        runningJobStatus,
        setRunningJobStatus,
        webSocketObj,
        setWebSocketObj
    ]);
    return (
        <RunProjectContext.Provider value={value}>{children}</RunProjectContext.Provider>
    )
}