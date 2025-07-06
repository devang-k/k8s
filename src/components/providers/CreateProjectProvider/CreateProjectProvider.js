 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: CreateProjectProvider.js  
 * Description: This file is responsible to share created project data to other components within the application. 
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
import { CreateProjectContext } from "./CreateProjectContext"
import { normalProjectType } from "../../../constant";

export const CreateProjectProvider = ({ children }) => {

    const [currentProjectId, setCurrentProjectId] = useState();
    const [isProjectSaved, setIsProjectSaved] = useState();
    const [projectName, setProjectName] = useState();
    const [selectedFeature, setSelectedFeature] = useState();//layout or hyperexpressivity feature selection done by user
    const [projectListWithStage1Result, setProjectListWithStage1Result] = useState();//list of projects under user which are displayed in stage1 result project list modal
    const [selectedProjectIdFromList, setSelectedProjectIdFromList] = useState();//projectid user selected while selecting project from stage1 result project list modal
    const [selectedProjectNameWithStage1Result, setSelectedProjectNameWithStage1Result] = useState();//projectName which user selected from stage1project list modal
    const [isHyperExpressivityProjectSaved, setIsHyperExpressivityProjectSaved] = useState(false);// stores boolean whether project with hyperexpressivity flow is checked or not 
    const [projectDetailsSelectedForHyperExpressivityFlow, setProjectDetailsSelectedForHyperExpressivityFlow] = useState();
    const [isProjectWithStage1ResultSelectedFromList, setIsProjectWithStage1ResultSelectedFromList] = useState(false);
    const [inPreviousThroughHyperExpressivityProjectCreation,setInPreviousThroughHyperExpressivityProjectCreation] = useState(false);
    const [isUserInAction3EditFromViewProject,setIsUserInAction3EditFromViewProject] = useState(false); // this indicates if user in edit mode from view project for action 2 or 3  projects
    const [isUserInAction2EditFromViewProject, setIsUserInAction2EditFromViewProject] = useState(false); // this indicated that user is in action 1 edit from view project
    const [isUserInAction1EditFromViewProject,setIsUserInAction1EditFromViewProject] = useState(false); // this indicates uset is in action1 edit from view project
    const [typeOfSelectedProject,setTypeOfSelectedProject] = useState(normalProjectType);// it indicates if project is normal project creation or some POC  project type 
    const [isStage1RunResultPresent,setIsStage1RunResultPresent] = useState(false); // it indicates if stage1 run result is present or not
    const [isStage2RunResultPresent,setIsStage2RunResultPresent] = useState(false); // it indicates if stage2 run result is present or not


    const value = useMemo(() => {
        return {
            currentProjectId,
            setCurrentProjectId,
            isProjectSaved,
            setIsProjectSaved,
            projectName,
            setProjectName,
            selectedFeature,
            setSelectedFeature,
            projectListWithStage1Result,
            setProjectListWithStage1Result,
            selectedProjectIdFromList,
            setSelectedProjectIdFromList,
            selectedProjectNameWithStage1Result,
            setSelectedProjectNameWithStage1Result,
            isHyperExpressivityProjectSaved,
            setIsHyperExpressivityProjectSaved,
            projectDetailsSelectedForHyperExpressivityFlow,
            setProjectDetailsSelectedForHyperExpressivityFlow,
            isProjectWithStage1ResultSelectedFromList,
            setIsProjectWithStage1ResultSelectedFromList,
            inPreviousThroughHyperExpressivityProjectCreation,
            setInPreviousThroughHyperExpressivityProjectCreation,
            isUserInAction3EditFromViewProject,
            setIsUserInAction3EditFromViewProject,
            isUserInAction2EditFromViewProject, 
            setIsUserInAction2EditFromViewProject,
            isUserInAction1EditFromViewProject,
            setIsUserInAction1EditFromViewProject,
            typeOfSelectedProject,
            setTypeOfSelectedProject,
            isStage1RunResultPresent,
            setIsStage1RunResultPresent,
            isStage2RunResultPresent,
            setIsStage2RunResultPresent,
        }
    }, [
        isStage2RunResultPresent,
        setIsStage2RunResultPresent,
        isStage1RunResultPresent,
        setIsStage1RunResultPresent,
        isUserInAction1EditFromViewProject,
        setIsUserInAction1EditFromViewProject,
        isUserInAction2EditFromViewProject, 
        setIsUserInAction2EditFromViewProject,
        isUserInAction3EditFromViewProject,
        setIsUserInAction3EditFromViewProject,
        currentProjectId,
        setCurrentProjectId,
        isProjectSaved,
        setIsProjectSaved,
        projectName,
        setProjectName,
        selectedFeature,
        setSelectedFeature,
        projectListWithStage1Result,
        setProjectListWithStage1Result,
        selectedProjectIdFromList,
        setSelectedProjectIdFromList,
        selectedProjectNameWithStage1Result,
        setSelectedProjectNameWithStage1Result,
        isHyperExpressivityProjectSaved,
        setIsHyperExpressivityProjectSaved,
        projectDetailsSelectedForHyperExpressivityFlow,
        setProjectDetailsSelectedForHyperExpressivityFlow,
        isProjectWithStage1ResultSelectedFromList,
        setIsProjectWithStage1ResultSelectedFromList,
        inPreviousThroughHyperExpressivityProjectCreation,
        setInPreviousThroughHyperExpressivityProjectCreation,
        typeOfSelectedProject,
        setTypeOfSelectedProject
    ]);

    return (
        <CreateProjectContext.Provider value={value}>{children}</CreateProjectContext.Provider>
    )
}