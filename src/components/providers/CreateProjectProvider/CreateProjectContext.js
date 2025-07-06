 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: CreateProjectContext.js  
 * Description: This file is responsible to save project data in context. 
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

export const CreateProjectContext = createContext({
    currentProjectId: null, // project id for current project that user is working on
    setCurrentProjectId: () => null,
    isProjectSaved: false, // it tells if project is saved or not
    setIsProjectSaved: () => null,
    projectName: '', 
    setProjectName: () => null,
    selectedFeature: [],
    setSelectedFeature: () => null,
    projectListWithStage1Result: [], // list of project with stage1 results
    setProjectListWithStage1Result: () => null,
    selectedProjectIdFromList: null, // holds project id for selected project with stage1 result from list
    setSelectedProjectIdFromList: () => null,
    selectedProjectNameWithStage1Result: null,// holds project name i.e selected from list of project with stage1 results
    setSelectedProjectNameWithStage1Result: () => null,
    isHyperExpressivityProjectSaved: false, // holds value if hyperexpressivity project is saved or not
    setIsHyperExpressivityProjectSaved: () => null,
    projectDetailsSelectedForHyperExpressivityFlow: null,// holds detail of projectwith stage1 result used for hyperexpressivity flow
    setProjectDetailsSelectedForHyperExpressivityFlow: () => null,
    isProjectWithStage1ResultSelectedFromList: false,// holds value stating if project from project with stage1 result is selected or not
    setIsProjectWithStage1ResultSelectedFromList: () => null,
    inPreviousThroughHyperExpressivityProjectCreation : false,// hold value true or false indicating if user landed on create project modal from previous button of hyperexpressivity flow
    setInPreviousThroughHyperExpressivityProjectCreation : () => null,
    isUserInAction3EditFromViewProject: false, // this indicates if user in edit mode from view project for action 3 projects
    setIsUserInAction3EditFromViewProject: ()=> null,
    isUserInAction2EditFromViewProject: false, // this indicated that user is in action 2 edit from view project
    setIsUserInAction2EditFromViewProject: ()=> null,
    isUserInAction1EditFromViewProject : false, // this indicates user is in action 1 edit from view project 
    setIsUserInAction1EditFromViewProject : () => null,
    typeOfSelectedProject: 0, // it indicates if project is normal project creation or some POC  project type 
    setTypeOfSelectedProject: () => null,
    isStage1RunResultPresent: false, // it indicates if stage1 run result is present or not
    setIsStage1RunResultPresent: () => null,
    isStage2RunResultPresent: false, // it indicates if stage2 run result is present or not
    setIsStage2RunResultPresent: () => null
});

export const useCreateProjectContext = () => {
    return useContext(CreateProjectContext);
};