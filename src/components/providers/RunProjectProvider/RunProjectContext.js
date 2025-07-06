 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: RunProjectContext.js  
 * Description: This file is responsible to save run project data 
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

export const RunProjectContext =  createContext({
    runLayoutJobId : null,// it holds jobID of current running stage1 or stage2 project
    setRunLayoutJobId: () => null,
    runLayoutRunningJobLogs : [] ,
    setRunLayoutRunningJobLogs : () => null,
    isRunningJobCompleted: false,
    setIsRunningJobCompleted: () => null,
    isRunJobErrored: false,
    setIsRunningJobErrored: () => null,
    listOfRunningJobsData : null, // it stores user list of running jobs.
    setListOfRunningJobsData : () => null, 
    runningJobStatus : false, // it holds runnings job status.
    setRunningJobStatus : () => null,
    webSocketObj: null,//it stores websocket obj as soon as it is created
    setWebSocketObj : () => null,
    isProjectStillRunning: false, // it sets state to true once run is completed with error or success
    setIsProjectStillRunning : () => null,
})

export const useRunProjectContext = () =>{
    return useContext(RunProjectContext);
};