 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: ResetContextHook.js  
 * Description: This file is responsible to reset context when user navigates other then project dashboard routes 
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

import { useCallback } from "react";
import { useNetListFileContext } from "../components/providers/NetListFileProvider/NetListFileContext";
import { useTechFileContext } from "../components/providers/TechFileProvider/TechFileContext";
import { useAdminContext } from "../components/providers/AdminProvider/AdminContext";
import { useManageUserContext } from "../components/providers/ManageUserProvider/ManageUserContext";
import { useStage1ResultContext } from "../components/providers/Stage1ResultProvider/Stage1ResultContext";
import { useStage2ResultContext } from "../components/providers/Stage2ResultProvider/Stage2ResultContext";
import { useCreateProjectContext } from "../components/providers/CreateProjectProvider/CreateProjectContext";
import { useEditProjectContext } from "../components/providers/EditProjectProvider/EditProjectContext";
import { useRunProjectContext } from "../components/providers/RunProjectProvider/RunProjectContext";
import { useLayoutGraphContext } from '../components/providers/LayoutGraphProvider/LayoutGraphContext';
import { useFilterResultsContext } from '../components/providers/FilterResultsProvider/FilterResultsContext';
export const useResetContextData = () => {
  const { setAdminNetlistFileData, setUserNetlistFileContent, setAdminTechFileData, setUserTechFileContent } = useAdminContext();
  const { setUserData, setLoggingLevelOptions } = useManageUserContext();
  const { setActionSelected, setNetListFileData, setIsNetListFileSelected, setSelectedNetlistFileName, setSelectedNetlistFileType, setNetlistCellInfo, setNetlistFileContent, setIsSelectAllChecked, setIsNetlistDataChanged } = useNetListFileContext();
  const { setIsTechFileSelected, setSelectedTechFileName, setTechFileData, setSelectedTechFileType, setIsTechDataChanged, setDefaultTechFileData ,setTechParameterValueError, setViewProjectTechFile, setProjectTechFileListData, setIsTechFileProjectSaved} = useTechFileContext();
  const { setStage1Result, setSelectedGdsItems, setStage1CellInfo, setIsGdsSelectAllChecked,setStage1RunResultSummaryData, setStage1GdsLayoutImageData ,setStage1TotalGDSNumber} = useStage1ResultContext();
  const { setStage2Result, setIsUserOnStage2Page, setStage2RunResultSummaryData, setStage2GdsLayoutImageData ,setStage2TotalGDSNumber} = useStage2ResultContext();
  const { setIsUserInEditMode, setUserCreatedProjectList, setIsButtonDisabledInEditMode, setShowResultButtonInStage1ResultInEditMode, setShowResultButtonInTechFileInEditMode } = useEditProjectContext();
  const { setIsProjectStillRunning,webSocketObj, setIsRunningJobCompleted, setRunLayoutRunningJobLogs, setIsRunningJobErrored, setRunLayoutJobId, setListOfRunningJobsData, setRunningJobStatus } = useRunProjectContext();
  const {
    setCurrentProjectId,
    setProjectName,
    setProjectListWithStage1Result,
    setSelectedProjectIdFromList,
    setSelectedFeature,
    setIsProjectSaved,
    setSelectedProjectNameWithStage1Result,
    setIsProjectWithStage1ResultSelectedFromList,
    setIsHyperExpressivityProjectSaved,
    setInPreviousThroughHyperExpressivityProjectCreation,
    setProjectDetailsSelectedForHyperExpressivityFlow,
    setIsUserInAction2EditFromViewProject,
    setIsUserInAction3EditFromViewProject,
    setIsUserInAction1EditFromViewProject,
    setTypeOfSelectedProject,
    setIsStage1RunResultPresent,
    setIsStage2RunResultPresent,
  } = useCreateProjectContext();
  const { setStage1GraphData, setStage2GraphData } = useLayoutGraphContext();
  const { clearFilterResultsContext } = useFilterResultsContext();

  const resetContext = useCallback(() => {
    if (webSocketObj) {
      webSocketObj.close();
    }
    setAdminNetlistFileData(null);
    setUserNetlistFileContent(null);
    setAdminTechFileData(null);
    setUserTechFileContent(null);
    setActionSelected(1);
    setNetListFileData(null);
    setIsNetListFileSelected(false);
    setSelectedNetlistFileName("");
    setSelectedNetlistFileType(null);
    setNetlistCellInfo(null);
    setNetlistFileContent(null);
    setIsSelectAllChecked(false);
    setIsNetlistDataChanged(false);
    setIsTechFileSelected(false);
    setSelectedTechFileName("");
    setTechFileData(null);
    setSelectedTechFileType(null);
    setIsTechDataChanged(false);
    setStage1Result(null);
    setSelectedGdsItems(null);
    setStage1CellInfo(null);
    setStage2Result(null);
    setIsUserOnStage2Page(false);
    setIsUserInEditMode(false);
    setUserCreatedProjectList(null);
    setIsButtonDisabledInEditMode(false);
    setIsRunningJobCompleted(false);
    setRunLayoutRunningJobLogs([]);
    setIsRunningJobErrored(false);
    setRunLayoutJobId(null);
    setListOfRunningJobsData(null);
    setRunningJobStatus(false);
    setCurrentProjectId(null);
    setProjectName("");
    setProjectListWithStage1Result([]);
    setSelectedProjectIdFromList(null);
    setSelectedFeature([]);
    setIsProjectSaved(false);
    setSelectedProjectNameWithStage1Result(null);
    setIsProjectWithStage1ResultSelectedFromList(false);
    setIsHyperExpressivityProjectSaved(false);
    setInPreviousThroughHyperExpressivityProjectCreation(false);
    setProjectDetailsSelectedForHyperExpressivityFlow(null);
    setIsUserInAction2EditFromViewProject(false);
    setIsUserInAction3EditFromViewProject(false);
    setIsUserInAction1EditFromViewProject(false);
    setShowResultButtonInStage1ResultInEditMode(false);
    setShowResultButtonInTechFileInEditMode(false);
    setTypeOfSelectedProject(0);
    setStage1GraphData(null);
    setStage2GraphData(null);
    setIsProjectStillRunning(false);
    setDefaultTechFileData()
    setIsGdsSelectAllChecked(false);
    setTechParameterValueError([]);
    setStage1RunResultSummaryData();
    setStage2RunResultSummaryData();
    setStage1GdsLayoutImageData([]);
    setStage2GdsLayoutImageData([]);
    clearFilterResultsContext();
    setIsStage1RunResultPresent(false);
    setIsStage2RunResultPresent(false);
    setStage1TotalGDSNumber(0) ;
    setStage2TotalGDSNumber(0) ;
    setViewProjectTechFile(false);
    setProjectTechFileListData();
    setIsTechFileProjectSaved(false);
    setUserData();
    setLoggingLevelOptions([]);
  }, [
    setIsStage1RunResultPresent,
    setIsStage2RunResultPresent,
    clearFilterResultsContext,
    setTechParameterValueError,
    setIsProjectStillRunning,
    webSocketObj,
    setAdminNetlistFileData,
    setUserNetlistFileContent,
    setAdminTechFileData,
    setUserTechFileContent,
    setActionSelected,
    setNetListFileData,
    setIsNetListFileSelected,
    setSelectedNetlistFileName,
    setSelectedNetlistFileType,
    setNetlistCellInfo,
    setNetlistFileContent,
    setIsSelectAllChecked,
    setIsNetlistDataChanged,
    setIsTechFileSelected,
    setSelectedTechFileName,
    setTechFileData,
    setSelectedTechFileType,
    setIsTechDataChanged,
    setStage1Result,
    setSelectedGdsItems,
    setStage1CellInfo,
    setStage2Result,
    setIsUserOnStage2Page,
    setIsUserInEditMode,
    setUserCreatedProjectList,
    setIsButtonDisabledInEditMode,
    setIsRunningJobCompleted,
    setRunLayoutRunningJobLogs,
    setIsRunningJobErrored,
    setRunLayoutJobId,
    setListOfRunningJobsData,
    setRunningJobStatus,
    setCurrentProjectId,
    setProjectName,
    setProjectListWithStage1Result,
    setSelectedProjectIdFromList,
    setSelectedFeature,
    setIsProjectSaved,
    setSelectedProjectNameWithStage1Result,
    setIsProjectWithStage1ResultSelectedFromList,
    setIsHyperExpressivityProjectSaved,
    setInPreviousThroughHyperExpressivityProjectCreation,
    setProjectDetailsSelectedForHyperExpressivityFlow,
    setIsUserInAction2EditFromViewProject,
    setIsUserInAction3EditFromViewProject,
    setIsUserInAction1EditFromViewProject,
    setShowResultButtonInStage1ResultInEditMode,
    setShowResultButtonInTechFileInEditMode,
    setTypeOfSelectedProject,
    setStage1GraphData,
    setStage2GraphData,
    setDefaultTechFileData,
    setIsGdsSelectAllChecked,
    setStage1RunResultSummaryData,
    setStage2RunResultSummaryData,
    setStage1GdsLayoutImageData,
    setStage2GdsLayoutImageData ,
    setStage1TotalGDSNumber ,
    setStage2TotalGDSNumber ,
    setViewProjectTechFile,
    setProjectTechFileListData,
    setIsTechFileProjectSaved,
    setUserData,
    setLoggingLevelOptions
  ]);

  return resetContext;
};
