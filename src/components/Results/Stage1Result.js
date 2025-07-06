
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: Stage1Result.js  
 * Description: This file is responsible to show Layout Generation results 
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

import React, { useEffect, useState, useCallback, useRef } from "react";
import { useOutletContext, useNavigate, useLocation } from "react-router-dom";
import { Button } from "react-bootstrap";
import { getRunResultsStatus,fetchStageData, fetchImageData, saveProjectInS3, runProject, editProjectData, deleteRunProjectResult, downloadStageResults, RunResultSummaryData } from "../../server/server";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faImages,
  faTable,
  faChartColumn,
  faDownload, faChartLine, faFileLines, faFilter, faCartShopping, faRotate, faTrash
} from "@fortawesome/free-solid-svg-icons";

import { useCreateProjectContext } from "../providers/CreateProjectProvider/CreateProjectContext";
import { useNetListFileContext } from "../providers/NetListFileProvider/NetListFileContext";
import { useTechFileContext } from "../providers/TechFileProvider/TechFileContext";
import { useEditProjectContext } from "../providers/EditProjectProvider/EditProjectContext";
import { ToastContainer, toast } from "react-toastify";
import { Tooltip as ReactTooltip } from 'react-tooltip'
import LayoutMetricsData from "./LayoutMetricsData";
import LayoutPexData from "./LayoutPexData";
import LayoutImageData from "./LayoutImageData";
import LayoutPexDataConsolidated from "./LayoutPexDataConsolidated";
import LayoutGraphDataStage1 from "./LayoutGraphDataStage1";
import ModalComponent from "../utils/Modal/ModalComponent";
import { ProjectWithStage1ResultListModalBody } from "../home/ProjectWithStage1ResultListModalBody";
import { useStage1ResultContext } from "../providers/Stage1ResultProvider/Stage1ResultContext";
import { useRunProjectContext } from "../providers/RunProjectProvider/RunProjectContext";
import { useRunHyperExpressivityProjectContext } from "../providers/RunHyperExpressivityProjectProvider/RunHyperExpressivityProjectContext";
import { useStage2ResultContext } from "../providers/Stage2ResultProvider/Stage2ResultContext";
import { useLayoutGraphContext } from '../providers/LayoutGraphProvider/LayoutGraphContext';
import { isDebugModeOn } from "../../constant";
import LayoutTotalData from "./LayoutTotalData";

import { useFilterResultsContext } from "../providers/FilterResultsProvider/FilterResultsContext";
import { DownloadResultsModalBody } from "./DownloadResultsModalBody"
import RunResultSummary from "./RunResultSummary";
import FilterRunResults from "../utils/FilterRunResults/FilterRunResults";
import ViewCart from "../utils/ViewCart/ViewCart";

import useApplyFilterHook from "../../Hooks/applyFilterHook/useApplyFilterHook";
import useClearAllLevelFilter from "../../Hooks/clearAllLevelFiltersHook/useClearAllLevelFilter";

const Stage1Result = () => {

  const hasLoaded = useRef(false);
  const { isStage1Level2FilterApplied, setIsStage1Level2FilterApplied, stage1Level2Filter, selectedDownloadOption, setSelectedDownloadOption, stage1GdsCartData, setFilterRequestParameter, setIsFilterApplied, isFilterApplied, isStage1FilterApplied, setIsStage1FilterApplied, filterRequestParameter, clearFilterResultsContext, stage1GraphSelectedGdsCells, stage2GraphSelectedGdsCells } = useFilterResultsContext();
  const { setSidebarContent, toggleSidebar, isSidebarCollapsed, terminalHeight } = useOutletContext();
  const { setRunHyperExpressivityProjectJobId } = useRunHyperExpressivityProjectContext();
  const { stage1Result, setStage1Result, selectedGdsItems, setSelectedGdsItems, stage1CellInfo, setStage1CellInfo, isGdsSelectAllChecked, setIsGdsSelectAllChecked, stage1RunResultSummaryData, setStage1RunResultSummaryData, setStage1GdsLayoutImageData, stage1TotalGDSNumber, setStage1TotalGDSNumber, } = useStage1ResultContext();
  const { isUserInEditMode, setIsUserInEditMode, isButtonDisabledInEditMode, setIsButtonDisabledInEditMode, showResultButtonInStage1ResultInEditMode, setShowResultButtonInStage1ResultInEditMode, setShowResultButtonInTechFileInEditMode } = useEditProjectContext();
  const { isUserOnStage2Page, stage2Result, setStage2Result, setIsUserOnStage2Page, setStage2RunResultSummaryData, setStage2GdsLayoutImageData, setStage2TotalGDSNumber } = useStage2ResultContext();
  const {
    currentProjectId,
    setCurrentProjectId,
    setIsProjectSaved,
    projectListWithStage1Result,
    selectedProjectIdFromList,
    setSelectedProjectIdFromList,
    selectedProjectNameWithStage1Result,
    setSelectedProjectNameWithStage1Result,
    setProjectListWithStage1Result,
    isHyperExpressivityProjectSaved,
    setIsHyperExpressivityProjectSaved,
    projectDetailsSelectedForHyperExpressivityFlow,
    setProjectDetailsSelectedForHyperExpressivityFlow,
    isProjectWithStage1ResultSelectedFromList,
    setIsProjectWithStage1ResultSelectedFromList,
    setInPreviousThroughHyperExpressivityProjectCreation,
    setIsUserInAction3EditFromViewProject,
    setIsUserInAction2EditFromViewProject,
    setIsUserInAction1EditFromViewProject,
    isUserInAction2EditFromViewProject,
    typeOfSelectedProject,
    setTypeOfSelectedProject,
    isStage2RunResultPresent,
    setIsStage1RunResultPresent,
    setIsStage2RunResultPresent,

  } = useCreateProjectContext();
  const {
    selectedNetlistFileName,
    actionSelected,
    setNetlistFileContent,
    setIsNetListFileSelected,
    netlistCellInfo,
    setNetlistCellInfo,
    setSelectedNetlistFileName,
    setSelectedNetlistFileType,
    setIsSelectAllChecked,
    setIsNetlistDataChanged
  } = useNetListFileContext();
  const {
    setIsTechFileSelected,
    selectedTechFileName,
    setSelectedTechFileName,
    setIsTechDataChanged,
    setDefaultTechFileData,
    setViewProjectTechFile, 
    setProjectTechFileListData,
    setIsTechFileProjectSaved
  } = useTechFileContext();

  const { setIsProjectStillRunning, setRunLayoutJobId, setIsRunningJobCompleted, setRunLayoutRunningJobLogs, webSocketObj } = useRunProjectContext();
  const {stage1GraphData, setStage1GraphData, setStage2GraphData } = useLayoutGraphContext();

  // custom hooks
  const { handleApplyFilterStage1 } = useApplyFilterHook();
  const { handleClearAllLevelFilter } = useClearAllLevelFilter(1);

  const [gdsData, setGdsData] = useState([]);
  const [page, setPage] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMoreImages, setHasMoreImages] = useState(true);
  const [totalImages, setTotalImages] = useState(0);
  const location = useLocation();
  const { projectName, selectedFeatures, action, nextButtonClicked } = location.state || {};
  const loadingRef = useRef(false);
  const scrollRefGdsImage = useRef(null);
  const scrollRefGdsMetrics = useRef(null);
  const scrollRefGdsPex = useRef(null);
  const navigate = useNavigate();
  const [isProjectWithStage1ResultModalOpen, setIsProjectWithStage1ResultModalOpen] = useState(false);
  const [isProjectSelected, setIsProjectSelected] = useState(false);
  const [isNextButtonClicked, setNextButtonClicked] = useState(nextButtonClicked || true); // when user navigate to previous and click next button on home page. we are sending "nextButtonClicked" as true. On load layout data on "ok" click we are setting this to false. so use effect gets trigeer to load new data.
  const [projectListStage1ModalBody, setProjectListStage1ModalBody] = useState({
    title: "",
    body: "",
    footer: "",
  });

  const [selectedNetlistFileNameFromList, setSelectedNetlistFileNameFromList] =
    useState();
  const [selectedTechFileNameFromList, setSelectedTechFileNameFromList] =
    useState();
  const [
    selectedProjectIdFromStage1ListRow,
    setSelectedProjectIdFromStage1ListRow,
  ] = useState();
  const [
    selectedProjectNameFromStage1ListRow,
    setSelectedProjectNameFromStage1ListRow,
  ] = useState();
  const [
    projectDetailsSelectedForHyperExpressivityFlowLocal,
    setProjectDetailsSelectedForHyperExpressivityFlowLocal,
  ] = useState();
  const [userRunConfirmationModal, setRunUserConfirmationModal] = useState(false);
  const [showImageColumn, setShowImageColumn] = useState(false);
  const [isDeleteRunProjectResultModalOpen, setIsDeleteRunProjectResultModalOpen] = useState(false);
  const [deleteRunResultsModalMessage, setDeleteRunResultsModalMessage] = useState();
  const [doesStage2ResultExisit, setDoesStage2ResultExisit] = useState(false); // it sets if stage2 results exisit for action 3
  const [currentPexView, setCurrentPexView] = useState("totaldata");
  const [isProjectRunningModal, setIsProjectRunningModal] = useState(false);
  const [projectRunningMessage, setProjectRunningMessage] = useState("")
  const [isDownloading, setIsDownloading] = useState(false); // to track if the download is in progress
  const [downloadResultModal, setDownloadResultModal] = useState(false);
  const [checkedValues, setCheckedValues] = useState({
    gds: false,    // GDS data checkbox
    metrics: false, // Metrics data checkbox
    pex: false,     // Pex data checkbox
  });
  const [filterResultSlider, setFilterResultSlider] = useState(false);
  const [viewCartOption, setViewCartOption] = useState(false); // sets the state of view cart option
  const [selectedCellFromList, setSelectedCellFromList] = useState(); // set the selected cell name
  const [isTableImageLoading, setIsTableImageLoading] = useState(false);
  const [showGDSLayoutImageData, setShowGDSLayoutImageData] = useState(); // This state stores the Layout Images Data
  const [gdsLayoutToggle, setGdsLayoutToggle] = useState(false); //This state handle the Layout toggle sync between Total Pex data and Graph Data
  const [isStage1DataLoaded , setIsStage1DataLoaded] = useState(false);

  const handleGdsSelectAllChange = () => {
    const newCheckedState = !isGdsSelectAllChecked;
    setIsGdsSelectAllChecked(newCheckedState);
    if (newCheckedState) {
      setSelectedGdsItems(stage1Result?.data?.Items?.map((metricData) => metricData?.MetricsData[0]?.File));
    }
    else {
      setSelectedGdsItems([]);
    }
  };

  // below useEffect check if all gds are selected or not. 
  useEffect(()=>{
    if(stage1Result && selectedGdsItems){
    const totalGdsItems = stage1Result?.data?.Items?.length;
    const totalSelectedGdsItems =  selectedGdsItems?.length
    if(totalGdsItems === totalSelectedGdsItems){
      setIsGdsSelectAllChecked(true);
    }
    else{
      setIsGdsSelectAllChecked(false);
    }
  }
  },[selectedGdsItems,stage1Result, setIsGdsSelectAllChecked])

  useEffect(() => {
    if (isGdsSelectAllChecked) {
      setSelectedGdsItems(stage1Result?.data?.Items?.map((metricData) => metricData?.MetricsData[0]?.File));
    }
  }, [stage1Result, isGdsSelectAllChecked, setSelectedGdsItems])

  useEffect(() => {
    // when user is in Edit mode and SelectedGdsItems is empty then it will add all Layout name data to SelectedGdsItems
    if (isUserInEditMode && selectedGdsItems?.length === 0 && isGdsSelectAllChecked) {
      const initialSelectedLayout = stage1Result?.data?.Items?.map(
        (metricData) => metricData?.MetricsData[0]?.File
      ) || []; // Fallback to an empty array if stage1Result is undefined
      setSelectedGdsItems(initialSelectedLayout);
    }

  }, [stage1Result, setSelectedGdsItems, isUserInEditMode, selectedGdsItems?.length, isGdsSelectAllChecked]);

  useEffect(() => {
    // Check if all items are selected or not
    if (gdsData?.items && selectedGdsItems && gdsData?.items?.length === selectedGdsItems?.length) {
      setIsGdsSelectAllChecked(true);
    }
  }, [selectedGdsItems, totalImages, setIsGdsSelectAllChecked, gdsData?.items]);


  // when user select on yes it hits the run end point
  const userConfirmationYesButton = async () => {
    setRunUserConfirmationModal(false);
    const runHyperExpressivityRequest = {
      cells: stage1CellInfo, // value will be an array of cell names selected
      projectId: currentProjectId,
      action: 2, // action is 2 here as project is to be run for hyperexpressivity
      selectedLayouts: isGdsSelectAllChecked ? [] : selectedGdsItems, // value will be an empty array is Select All is checked else array of selected GDS Items
      selectAll: isGdsSelectAllChecked,
      stage1Project: selectedProjectIdFromList,
    };
    try {
      const runHyperExpressivityRunRes = await runProject(runHyperExpressivityRequest);//calling endpoint for running hyperexpressivity project
      //setting running job id in context
      if (runHyperExpressivityRunRes?.status && runHyperExpressivityRunRes?.status_code === 200) {
        setRunLayoutJobId(runHyperExpressivityRunRes?.data?.jobId)// setting jobid to start displaying run project logs
        setRunHyperExpressivityProjectJobId(runHyperExpressivityRunRes?.data?.jobId);
        if (action === 1 || action === 2) {
          setRunLayoutRunningJobLogs(["################################################################################################"]); // will clear the logs only when user runs project individually

        } else if (action === 3) {
          setRunLayoutRunningJobLogs((prevState) => [...prevState, "################################################################################################"])
          setIsUserOnStage2Page(true) // this will set and perform action 2 
        }

        //navigating user to loader page 
        navigate("/dashboard/loader", { state: { projectName, selectedFeatures, action: actionSelected } });
      } else if (runHyperExpressivityRunRes?.status_code === 208) {
        // Project is already running - show running project modal
        setProjectRunningMessage(runHyperExpressivityRunRes?.message || "The project is currently in a running state.Please try again later.");
        setIsProjectRunningModal(true);
      } else if (runHyperExpressivityRunRes?.data && runHyperExpressivityRunRes?.data?.status_code === 409) {
        // here need to handle 409 if already results exisit asking user for confirmation if it needs to be overrided

        if (action === 2) {
          const filterMessage = "All the applied filters will be removed."
          setDeleteRunResultsModalMessage(`${isFilterApplied ? filterMessage : ''}${runHyperExpressivityRunRes?.data?.message}`);// setting the message to be shown in delete modal body
        } else {
          setDeleteRunResultsModalMessage(runHyperExpressivityRunRes?.data?.message);// setting the message to be shown in delete modal body 
        }
        setRunUserConfirmationModal(false);
        setIsDeleteRunProjectResultModalOpen(true); // this will show user delete run results confirmation modal
      }
    } catch (error) {
      toast.error(error?.message);
      console.error("Error while running hyperexpressivity project", error);
    }
  }

  // below function will help in closing filter pop up modal
  const closeFilterResultSlider = () => {
    document.getElementById("mySidenav").style.width = "0";
    setFilterResultSlider(false);
  }

  //when user selects option no to run hyper expressivity project 
  const userConfirmationNoButton = () => {
    setRunUserConfirmationModal(false);
  };

  //below function handles overriding of exisiting run result & then running hyper project again
  const handleOverRideRunResultAndReRunHyper = async () => {
    const deleteRunProjectReq = {
      projectId: currentProjectId,
      stage: 2 // here always action 2 goes since for action3 also action
    }

    const deleteRunResultResponse = await deleteRunProjectResult(deleteRunProjectReq);
    setIsDeleteRunProjectResultModalOpen(false);
    try {
      if (deleteRunResultResponse && deleteRunResultResponse?.status_code === 200) {

        if (action === 2) {
          //only for hyper project this is expected
          setIsFilterApplied(false);//setting filter back to null since rerunning project
          setFilterRequestParameter(null);//setting filter back to null since rerunning project
        }

        setStage2Result();//emptying stage results data on local as well to keep it in sync since deleting it from s3
        if (action === 1 || action === 2) {
          setRunLayoutRunningJobLogs([]);
        } else if (action === 3) {
          setRunLayoutRunningJobLogs((prevState) => [...prevState, "################################################################################################"])
        }
        setIsRunningJobCompleted(false);
        //creating run hyperexpressivity requestjson
        const runHyperExpressivityRequest = {
          cells: stage1CellInfo, // value will be an array of cell names selected, this value is geting set in useeffect
          projectId: currentProjectId,
          action: 2, // action is 2 here as project is to be run for hyperexpressivity
          selectedLayouts: isGdsSelectAllChecked ? [] : selectedGdsItems, // value will be an empty array is Select All is checked else array of selected GDS Items
          selectAll: isGdsSelectAllChecked,
          stage1Project: selectedProjectIdFromList,
        };
        const runHyperExpressivityRunProjRes = await runProject(runHyperExpressivityRequest);
        //once project is deleted successfully , running project 
        try {
          if (runHyperExpressivityRunProjRes?.status_code === 200) {
            if (action === 3) {
              setIsUserOnStage2Page(true) // this will set and perform action 2 
            }
            setRunLayoutJobId(runHyperExpressivityRunProjRes?.data?.jobId)// setting jobid to start displaying run project logs
            setRunHyperExpressivityProjectJobId(runHyperExpressivityRunProjRes?.data?.jobId);//setting the current running project jobid in context 
            navigate("/dashboard/loader", { state: { projectName, selectedFeatures, action: actionSelected } })
          } else {
            toast.error("Error While running project");
          }
        } catch (error) {
          toast.error("Error while running project from layout", error)
          console.error("Error while running project from layout", error)
        }
      } else {
        toast.error("Error while deleting project in layout");
      }
    } catch (deleteProjectErr) {
      toast.error("Error while deleting project details after user confirms overwriting of run results", deleteProjectErr)
      console.error("Error while deleting project details after user confirms overwriting of run results", deleteProjectErr)
    }
  }
  // user confirmation modal before run , content body
  const confirmationModalContent = {
    title: "Please Confirm:",
    body: (
      <h6>
        {`You have selected ${isGdsSelectAllChecked
          ? totalImages
          : selectedGdsItems?.length || "0"
          } layouts for hyperexpressivity run.`}
      </h6>

    ),
    footer: (
      <>
        <Button
          id="user-confirmation-yes-button"
          className="app-primary-button-color border-0 w-25"
          onClick={userConfirmationYesButton}
        >
          Yes
        </Button>
        <Button
          id="user-confirmation-no-button"
          className="app-secondary-button-color border-0 w-25"
          onClick={userConfirmationNoButton}
        >
          No
        </Button>
      </>
    ),
  };

  //below generates the content of modal body for override run result (delete) modal
  const overrideRunResultConfirmationModalContent = {
    title: "Message",
    body: deleteRunResultsModalMessage,
    footer: (
      <>
        <Button id="override-run-result-hyper-confirmation-yes-button" onClick={handleOverRideRunResultAndReRunHyper} className="app-primary-button-color border-0 w-25">Yes</Button>
        <Button id="override-run-result-hyper-confirmation-no-button" onClick={() => { setIsDeleteRunProjectResultModalOpen(false) }} className="app-secondary-button-color border-0 w-25">No</Button>
      </>)
  };

  const handleDownloadModalClose = () => {
    setCheckedValues({ gds: false, metrics: false, pex: false });  // Reset checkboxes
    setSelectedDownloadOption(3)
    setDownloadResultModal(false);  // Close the modal
  };

  const handleCheckboxChange = (e) => {
    const { id, checked } = e?.target; // id corresponds to the checkbox id (gds, metrics, pex)
    setCheckedValues(prevState => ({
      ...prevState,
      [id]: checked, // Update the checked value for the specific checkbox
    }));
  };

  const gdsResultDownloadButton = async (selectedData) => {
    setIsDownloading(true); // Start download

    let projectId;
    if (actionSelected === 2) {
      if (isUserInEditMode) {
        projectId = currentProjectId; // if user is in hyperexpressivity flow & editing exisiting project then stage1 results will be fetched from stage2 project itself
      } else {
        projectId = selectedProjectIdFromList;// else it will be fetched from stage1 project
      }
    } else {
      projectId = currentProjectId;
    }

    let downloadTypeReqVal;
    if (selectedDownloadOption === 3) {
      // if download all will check here if filterall or download all
      if(( stage1GraphSelectedGdsCells?.length > 0 || !filterRequestParameter?.cellSelectAll ||  filterRequestParameter?.filterParametersName?.filterLevel1 !== null || filterRequestParameter?.filterParametersName?.filterLevel2?.length >0) ){
        downloadTypeReqVal = 2;
        setSelectedDownloadOption(2)
      }else{
        downloadTypeReqVal = 3;
        setSelectedDownloadOption(3)
      }
    } else {
      downloadTypeReqVal = selectedDownloadOption;
    };
    const downloadPayload = {
      project_id: projectId,
      stage: 1,
      file_types: Object?.keys(selectedData)?.filter(key => selectedData[key]), // Send only checked values
      filter: stage1GraphSelectedGdsCells?.length > 0 ? null : filterRequestParameter ? filterRequestParameter :null,
      filterByLayout:(stage1GraphSelectedGdsCells?.length > 0) ? stage1GraphSelectedGdsCells : null,
      downloadType: downloadTypeReqVal || 3,//making default as download all
      fileList: selectedDownloadOption === 1 ? stage1GdsCartData : null // if cart download then send list otherwise null
    };

    try {
      // Make the API call to download the data
      const response = await downloadStageResults(downloadPayload);

      if (response?.data && response?.data instanceof Blob) {
        const downloadUrl = URL.createObjectURL(response?.data);
        const contentDisposition = response?.headers['x-filename'];

        // Create a temporary <a> element to trigger the download
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.target = '_self';  // This will ensure that the file is downloaded in the same window
        link.download = contentDisposition ? contentDisposition : 'downloaded-file'; // Set a default filename
        link.click(); // Simulate a click on the link to start the download

        // Clean up the object URL after the download starts
        URL.revokeObjectURL(downloadUrl);

        setIsDownloading(false); // End download
        setCheckedValues({ gds: false, metrics: false, pex: false });  // Reset checkboxes
        setSelectedDownloadOption(3);
        setViewCartOption(false);//closing cart slider
        setDownloadResultModal(false);  // Close the modal

        //Removed to save cart added data after cart download 

        setDownloadResultModal(false);  // Close the modal

      } else {
        console.error('Received response is not a valid file or does not contain a Blob:', response);
        toast.error("No data found for the provided filter" || response?.message);
        setIsDownloading(false);
      }
    } catch (error) {
      console.error('Error while downloading the file:', error);
      setIsDownloading(false); // End download if an error occurs

    }
  };

  const downloadButton = () => {
    setDownloadResultModal(true);
  };

  const clearFilterButton = () => {
    handleClearAllLevelFilter(action); 
    setGdsLayoutToggle(false);
    setShowGDSLayoutImageData();
    setStage1GraphData({
      PEX_Consolidated: stage1GraphData?.PEX_Consolidated,
  });
  setStage1GdsLayoutImageData([]);
  };

  const isAnyCheckboxSelected = Object?.values(checkedValues)?.includes(true);
  const DownloadResultsModalContent = {
    title: "Download Layout Generation Results",
    body: (<DownloadResultsModalBody isAnyCheckboxSelected={isAnyCheckboxSelected} checkedValues={checkedValues} handleCheckboxChange={handleCheckboxChange} isDownloading={isDownloading} userStage={1} />),
    footer: (
      <>
        <Button
          id="layout-generation-result-cancel-button"
          onClick={() => handleDownloadModalClose()}
          className="app-secondary-button-color border-0 w-25"
          disabled={isDownloading} // Disable cancel button during download
        >
          Cancel
        </Button>
        <Button
          id="layout-generation-result-download-button"
          onClick={() => gdsResultDownloadButton(checkedValues)} // Pass the current state (checkedValues) to the function
          className={selectedDownloadOption === 4 ? "app-primary-button-color border-0 w-25" : !isAnyCheckboxSelected ? "w-25 app-secondary-button-color border-0 cursor_not_allowed" : "app-primary-button-color border-0 w-25"}
          disabled={selectedDownloadOption === 4 ? false : !isAnyCheckboxSelected || isDownloading} // Disable button if no checkboxes are selected or if downloading
        >
          {isDownloading ? "Downloading..." : "Download"}
        </Button>
      </>
    ),
  };

  // below function handles closing of view project list having stage1 result modal
  const handleCloseViewStage1ProjectListModal = useCallback(() => {
    setIsProjectWithStage1ResultModalOpen(false);
  }, []);


  //below function will update the state for whether project is selected from list or not
  const handleStateSetForProjectSelection = useCallback(
    (
      isProjectSelected,
      currentSelectedProjectId,
      projectNameSelected,
      currentSelectedNetListFileName,
      currentSelectedTechFileName,
      data
    ) => {
      setIsProjectWithStage1ResultModalOpen(isProjectSelected);
      setSelectedProjectIdFromStage1ListRow(currentSelectedProjectId);
      // setCurrentProjectId(currentSelectedProjectId);
      setSelectedProjectNameFromStage1ListRow(projectNameSelected);
      setSelectedNetlistFileNameFromList(currentSelectedNetListFileName);
      setSelectedTechFileNameFromList(currentSelectedTechFileName);
      setProjectDetailsSelectedForHyperExpressivityFlowLocal(data);
      setIsProjectSelected(true);
    },
    [
      setIsProjectWithStage1ResultModalOpen,
      setSelectedProjectIdFromStage1ListRow,
      setSelectedProjectNameFromStage1ListRow,
      setSelectedNetlistFileNameFromList,
      setSelectedTechFileNameFromList,
      setProjectDetailsSelectedForHyperExpressivityFlowLocal,
      // setCurrentProjectId,
    ]
  );

  //below project handles project selections row functionality handleOkButtonRowSelectionInStage1ProjectListModal
  const handleOkButtonRowSelectionInStage1ProjectListModal = useCallback(async () => {
    setPage(0);
    setSelectedGdsItems([]);
    setIsGdsSelectAllChecked(false);
    // setStage1Result({}); // keeping this commented to backtrack changes.
    setIsHyperExpressivityProjectSaved(false);
    setSelectedProjectNameWithStage1Result(selectedProjectNameFromStage1ListRow);// setting selected project name with stage1 result in context
    setSelectedProjectIdFromList(selectedProjectIdFromStage1ListRow);
    setSelectedNetlistFileName(selectedNetlistFileNameFromList);
    setSelectedTechFileName(selectedTechFileNameFromList);
    setIsProjectWithStage1ResultModalOpen(false);
    setProjectDetailsSelectedForHyperExpressivityFlow(projectDetailsSelectedForHyperExpressivityFlowLocal);
    setIsProjectWithStage1ResultSelectedFromList(true);
    setNextButtonClicked(false);
    setStage1GraphData(null);
    setStage2GraphData(null);
    setCurrentProjectId(selectedProjectIdFromStage1ListRow);
    setIsStage1DataLoaded(true);
  }, [setIsProjectWithStage1ResultSelectedFromList, projectDetailsSelectedForHyperExpressivityFlowLocal, setProjectDetailsSelectedForHyperExpressivityFlow, selectedProjectIdFromStage1ListRow, selectedProjectNameFromStage1ListRow, setSelectedProjectIdFromList, setSelectedProjectNameWithStage1Result, setSelectedNetlistFileName, setSelectedTechFileName, selectedNetlistFileNameFromList, setIsHyperExpressivityProjectSaved, selectedTechFileNameFromList, setSelectedGdsItems, /** setStage1Result, **/ setNextButtonClicked, setStage1GraphData, setStage2GraphData, setIsGdsSelectAllChecked, setCurrentProjectId]);

  const handlePreviousButton = useCallback(() => {
    if (actionSelected === 2) {
      setInPreviousThroughHyperExpressivityProjectCreation(true);
      navigate("/home", {
        state: {
          projectName,
          selectedFeatures,
          createProjectModal: true,
          action,
        },
      });
    } else {
      navigate("../techfiles", {
        state: { projectName, selectedFeatures, action },
      });
    }
  }, [navigate, projectName, selectedFeatures, action, actionSelected, setInPreviousThroughHyperExpressivityProjectCreation]);

  const handleCancelButton = useCallback(() => {
    if (webSocketObj) {
      webSocketObj.close();
    }
    setRunLayoutJobId(null);
    setIsUserInAction1EditFromViewProject(false);
    setIsUserInAction2EditFromViewProject(false);
    setIsUserInAction3EditFromViewProject(false);
    setStage2Result();
    setInPreviousThroughHyperExpressivityProjectCreation(false);
    setIsButtonDisabledInEditMode(false);
    setIsUserInEditMode(false);
    setGdsData([]);
    setStage1Result();
    setPage(0);
    setLoadingMore(false);
    setHasMoreImages(true);
    setTotalImages(0);
    setIsTechFileSelected(false);
    setSelectedTechFileName("");
    setNetlistCellInfo();
    setIsNetListFileSelected(false);
    setNetlistFileContent();
    setSelectedNetlistFileName();
    setSelectedNetlistFileType();
    setIsProjectSaved(false);
    setIsSelectAllChecked(false);
    setCurrentProjectId(null);
    setSelectedNetlistFileNameFromList();
    setSelectedProjectIdFromList();
    setSelectedProjectNameWithStage1Result();
    setProjectListWithStage1Result();
    setIsProjectWithStage1ResultSelectedFromList(false);
    setIsHyperExpressivityProjectSaved(false);
    setCurrentProjectId();
    setSelectedProjectNameFromStage1ListRow();
    setRunLayoutRunningJobLogs([]);
    setIsRunningJobCompleted(false);
    setSelectedGdsItems([]);
    setIsUserOnStage2Page(false);
    setStage1CellInfo();
    setIsNetlistDataChanged(false);
    setIsTechDataChanged(false);
    setShowResultButtonInStage1ResultInEditMode(false);
    setShowResultButtonInTechFileInEditMode(false);
    setStage1GraphData(null);
    setStage2GraphData(null);
    setTypeOfSelectedProject(0);
    setIsProjectStillRunning(false);
    setDefaultTechFileData();
    setIsGdsSelectAllChecked(false);
    setStage1RunResultSummaryData()
    setStage2RunResultSummaryData()
    clearFilterResultsContext();
    setStage1GdsLayoutImageData([]);
    setStage2GdsLayoutImageData([]);
    setIsStage1RunResultPresent(false);
    setIsStage2RunResultPresent(false);
    navigate("/home");
    setStage1TotalGDSNumber(0);
    setStage2TotalGDSNumber(0);
    setViewProjectTechFile(false);
    setProjectTechFileListData();
    setIsTechFileProjectSaved(false);
  }, [
    setIsStage1RunResultPresent,
    setIsStage2RunResultPresent,
    clearFilterResultsContext,
    setIsProjectStillRunning,
    setTypeOfSelectedProject,
    setRunLayoutJobId,
    webSocketObj,
    setIsUserInAction1EditFromViewProject,
    setIsUserInAction2EditFromViewProject,
    setIsUserInAction3EditFromViewProject,
    setStage2Result,
    setIsUserOnStage2Page,
    setInPreviousThroughHyperExpressivityProjectCreation,
    setIsButtonDisabledInEditMode,
    setIsUserInEditMode,
    setIsRunningJobCompleted,
    setRunLayoutRunningJobLogs,
    setStage1Result,
    setIsHyperExpressivityProjectSaved,
    navigate,
    setGdsData,
    setPage,
    setLoadingMore,
    setHasMoreImages,
    setTotalImages,
    setIsTechFileSelected,
    setSelectedTechFileName,
    setNetlistCellInfo,
    setIsNetListFileSelected,
    setNetlistFileContent,
    setSelectedNetlistFileName,
    setSelectedNetlistFileType,
    setIsProjectSaved,
    setIsSelectAllChecked,
    setCurrentProjectId,
    setProjectListWithStage1Result,
    setSelectedProjectIdFromList,
    setSelectedProjectNameWithStage1Result,
    setIsProjectWithStage1ResultSelectedFromList,
    setStage1CellInfo,
    setSelectedGdsItems,
    setIsNetlistDataChanged,
    setIsTechDataChanged,
    setShowResultButtonInStage1ResultInEditMode,
    setShowResultButtonInTechFileInEditMode,
    setStage1GraphData,
    setStage2GraphData,
    setDefaultTechFileData,
    setIsGdsSelectAllChecked,
    setStage1RunResultSummaryData,
    setStage2RunResultSummaryData,
    setStage1GdsLayoutImageData,
    setStage2GdsLayoutImageData ,
    setStage1TotalGDSNumber ,
    setStage2TotalGDSNumber,
    setViewProjectTechFile,
    setProjectTechFileListData,
    setIsTechFileProjectSaved
  ]);

  const loadStage1Data = useCallback(async (pageNumber) => {
    if (loadingRef.current || !hasMoreImages) return;

    loadingRef.current = true;
    setLoadingMore(true);
    try {
      // Fetch new data from API based on pageNumber
      // const projectId = actionSelected === 2 ? selectedProjectIdFromList : currentProjectId;
      let projectId;
      if (actionSelected === 2) {
        if (isUserInEditMode) {
          projectId = currentProjectId; // if user is in hyperexpressivity flow & editing exisiting project then stage1 results will be fetched from stage2 project itself
        } else {
          projectId = selectedProjectIdFromList;// else it will be fetched from stage1 project
        }
      } else {
        projectId = currentProjectId;
      }
      // Fetch data from stage , here sending 1 as we are fetching stage1 responses
      const newStage1Res = await fetchStageData(projectId, 1, pageNumber, filterRequestParameter ? filterRequestParameter : null);
      if (newStage1Res.status === false) {
        toast.error(newStage1Res.message);
        return;
      }
      if (!newStage1Res || !newStage1Res?.data || !Array.isArray(newStage1Res?.data?.Items)) {
        setHasMoreImages(false);
        return;
      }

      const newItemsData = Array.isArray(newStage1Res?.data?.Items) ? newStage1Res?.data?.Items : [];
      const PEX_Consolidated = newStage1Res?.data?.PEX_Consolidated;
      const newPageNumber = newStage1Res?.data?.PageNumber;
      const newPageSize = newStage1Res?.data?.PageSize;
      const newTotalItems = newStage1Res?.data?.TotalItems;
      const newRemainingItems = newStage1Res?.data?.RemainingItems;
      const newTotalGDSGeneratedCount = newStage1Res?.data?.TotalGdsCount;

      // // Update total images count
      setTotalImages(newStage1Res?.data?.TotalItems || 0);

      // // Fetch image data
      const imagePaths = newItemsData?.map(item => item?.LayoutData);
      const imagesData = await fetchImageData(imagePaths);

      if (!imagesData || !imagesData?.images || imagesData?.images?.length !== newItemsData?.length) {
        toast.error("Mismatch in image data fetched");
        console.error("Mismatch in image data fetched", imagesData);
        return;
      }

      const newImages = newItemsData?.map((item, index) => ({
        src: `data:image/png;base64,${imagesData?.images[index]?.encodedImage}`,
        name: item?.LayoutData?.split("/")?.pop()?.replace(".png", ""),
        metricsData: item?.MetricsData,
        pexData: item?.PEXData,
      }));

      // Append the new data to the context
      setStage1Result(prevResult => ({
        ...prevResult,
        data: {
          ...prevResult?.data,
          Items: [
            ...(prevResult?.data?.Items || []), // Default to an empty array if Items is undefined
            ...newItemsData, // Append new items to existing ones
          ],
          PEX_Consolidated: !PEX_Consolidated ? prevResult?.data?.PEX_Consolidated : PEX_Consolidated,
          PageNumber: newPageNumber,  // Update PageNumber with the new value
          PageSize: newPageSize,  // Update PageSize with the new value
          TotalItems: newTotalItems,  // Update TotalItems with the new value
          RemainingItems: newRemainingItems,  // Update RemainingItems with the new value
          TotalGdsCount: newTotalGDSGeneratedCount, //Update totalgds generatedcount
        },
      }));

      setGdsData(prevState => ({
        items: [...(Array.isArray(prevState?.items) ? prevState.items : []), ...newImages],
        PEX_Consolidated: !PEX_Consolidated ? prevState?.PEX_Consolidated : PEX_Consolidated
      }));
      setIsStage1DataLoaded(false)
    } catch (error) {
      toast.error("Error while fetching stage2 data");
      console.error("Error fetching stage2 data:", error);
    } finally {
      loadingRef.current = false;
      setLoadingMore(false);
    }
  }, [filterRequestParameter, setIsStage1DataLoaded,setStage1Result, currentProjectId, actionSelected, hasMoreImages, selectedProjectIdFromList, isUserInEditMode]);


  const handleScroll = useCallback((ref, setPage) => {
    if (!ref?.current) {
      return;
    }
    const { scrollTop, scrollHeight, clientHeight } = ref?.current;
    if (scrollTop == null || scrollHeight == null || clientHeight == null) {
      return;
    }
    if (!loadingRef?.current && scrollTop + clientHeight >= scrollHeight - 50) {
      setPage((prevPage) => {
        const newPage = prevPage + 1;
        // Check if If remaining Items are more than 0 then only fetch results
        stage1Result?.data?.RemainingItems > 0 && loadStage1Data(newPage);
        return newPage;
      });
    }
  }, [stage1Result, loadStage1Data]);

  const debouncedScroll = useCallback((ref, setPage) => {
    let timer;
    return () => {
      clearTimeout(timer);
      timer = setTimeout(() => handleScroll(ref, setPage), 200);
    };
  }, [handleScroll]);

  // calling save endpoint to save hyperexpressivity project
  const handleHyperExpressivityFlowProjectSave = useCallback(async () => {
    /*
    action = 2 means only hyperexpressivity selected ,
   
  */
    if (isUserInEditMode) {
      const editProjectReqJSON = {
        netlistMetadata: {
          fileName: projectDetailsSelectedForHyperExpressivityFlow?.netlist_metadata?.fileName,
          netlistType: projectDetailsSelectedForHyperExpressivityFlow?.netlist_metadata?.netlistType,
          cellSelections: projectDetailsSelectedForHyperExpressivityFlow?.netlist_metadata?.cellSelections,
        },
        techMetadata: {
          fileName: projectDetailsSelectedForHyperExpressivityFlow?.tech_metadata?.fileName,
          techType: projectDetailsSelectedForHyperExpressivityFlow?.tech_metadata?.techType,
        },
        selectedLayouts: isGdsSelectAllChecked ? [] : selectedGdsItems, // value will be an empty array is Select All is checked else array of selected GDS Items
        selectAll: isGdsSelectAllChecked,
      }
      const editProjectRes = await editProjectData(currentProjectId, editProjectReqJSON);
      if (editProjectRes?.status === true) {
        toast.success(`${editProjectRes?.message} ${isDebugModeOn ? currentProjectId : ""}`, { autoClose: 10000 })
      } else {
        toast.error(editProjectRes?.message, { autoClose: 30000 })
        console.error("Error saving project data in edit mode", editProjectRes?.message)
      }
    } else {
      //  request Body for save project , here actionSelected is 2 always as it is saving project through hyperexpressivity flow
      const saveProjectReqJSON = {
        projectName: projectName,
        action: actionSelected,
        stageOneProjectId: projectDetailsSelectedForHyperExpressivityFlow?.id,
        netlistMetadata: {
          fileName: projectDetailsSelectedForHyperExpressivityFlow?.netlist_metadata?.fileName,
          netlistType: projectDetailsSelectedForHyperExpressivityFlow?.netlist_metadata?.netlistType,
          cellSelections: projectDetailsSelectedForHyperExpressivityFlow?.netlist_metadata?.cellSelections,
        },
        techMetadata: {
          fileName: projectDetailsSelectedForHyperExpressivityFlow?.tech_metadata?.fileName,
          techType: projectDetailsSelectedForHyperExpressivityFlow?.tech_metadata?.techType,
        },
        selectedLayouts: isGdsSelectAllChecked ? [] : selectedGdsItems, // value will be an empty array is Select All is checked else array of selected GDS Items
        selectAll: isGdsSelectAllChecked,
        projectType: typeOfSelectedProject,
      };
      const saveHyperExpressivityProjectRes = await saveProjectInS3(saveProjectReqJSON);
      if (saveHyperExpressivityProjectRes && saveHyperExpressivityProjectRes?.status === true) {
        // show success toaster
        setIsHyperExpressivityProjectSaved(true);
        setCurrentProjectId(saveHyperExpressivityProjectRes?.data?.projectId);
        setIsUserInEditMode(true); // enables the user in edit mode. 
        setIsButtonDisabledInEditMode(true); //disables the button in edit mode.
        toast.success(`${saveHyperExpressivityProjectRes?.message} ${isDebugModeOn ? saveHyperExpressivityProjectRes?.data?.projectId : ""}`, { autoClose: 10000 });
      } else {
        console.error("Failed while saving hyperexpressivity project", saveHyperExpressivityProjectRes?.message);
        toast.error(saveHyperExpressivityProjectRes?.message);
      }
    }
  }, [typeOfSelectedProject, selectedGdsItems, setCurrentProjectId, setIsHyperExpressivityProjectSaved, actionSelected, projectDetailsSelectedForHyperExpressivityFlow, isUserInEditMode, currentProjectId, setIsUserInEditMode, setIsButtonDisabledInEditMode, projectName, isGdsSelectAllChecked]);

  //handling hyperexpressivity project run 
  const handleHyperExpressivityFlowProjectRun = useCallback(async () => {
    setRunUserConfirmationModal(true);
  }, []);

  // below function handles opening of view project list having stage1 result modal
  const handleViewStage1ProjectListModal = useCallback(() => {
    setIsProjectWithStage1ResultSelectedFromList(false);
    setIsProjectSelected(false);
    setProjectListStage1ModalBody({
      title: "Choose a Project With Layouts",
      body: <ProjectWithStage1ResultListModalBody projectListWithStage1Result={projectListWithStage1Result} handleStateSetForProjectSelection={handleStateSetForProjectSelection} />,
      footer: <>
        <Button
          id="ok-button-stage1projectlist-hyperexpressivity-flow"
          className={`col-4 m-2 ${handleStateSetForProjectSelection ? "app-primary-button-color border-0" : "app-secondary-button-color border-0"}`}
          disabled={!isProjectWithStage1ResultModalOpen}
          onClick={() => { handleOkButtonRowSelectionInStage1ProjectListModal() }}
        >
          Ok
        </Button>
        <Button
          id="cancel-button-stage1projectlist-hyperexpressivity-flow"
          onClick={handleCloseViewStage1ProjectListModal}
          className="col-4 m-2 app-secondary-button-color border-0"
        >
          Cancel
        </Button>
      </>,
    });
    setIsProjectWithStage1ResultModalOpen(true);
  }, [handleCloseViewStage1ProjectListModal, setIsProjectWithStage1ResultSelectedFromList,handleOkButtonRowSelectionInStage1ProjectListModal, handleStateSetForProjectSelection, isProjectWithStage1ResultModalOpen, projectListWithStage1Result])

  // below function helps in handling case of showing exisiting hyper result
  const handleShowExisitingHyperResult = useCallback(async () => {
    try {
      //setting value that user is going back in stage2result page
      setIsUserOnStage2Page(true);
      navigate("/dashboard/stage2result", { state: { projectName, selectedFeatures, action } });
    } catch (err) {
      console.error("Fetching Error", err);
    }
  }, [action, navigate, projectName, selectedFeatures, setIsUserOnStage2Page]);

  useEffect(() => {
    if (isStage1DataLoaded && actionSelected === 2 && page === 0 && !isHyperExpressivityProjectSaved && !isNextButtonClicked) {
      setGdsData([]); // Reset GDS data before fetching new data
      setHasMoreImages(true); // Reset image loading flag
      setStage1Result();  //reset context on project change
      loadStage1Data(0); // Trigger data load for page 0
    }
  }, [
    isHyperExpressivityProjectSaved,
    isStage1DataLoaded, // dependency for project selection
    actionSelected, // ensures correct action type
    selectedProjectIdFromList, // ensure the correct project ID is available
    loadStage1Data,
    setStage1Result,
    isNextButtonClicked,
    page
  ]);


  useEffect(() => {
    const handleDebouncedScrollGdsImage = debouncedScroll(scrollRefGdsImage, setPage);
    const handleDebouncedScrollGdsMetrics = debouncedScroll(
      scrollRefGdsMetrics,
      setPage
    );
    const handleDebouncedScrollGdsPex = debouncedScroll(
      scrollRefGdsPex,
      setPage
    );

    const refGdsImage = scrollRefGdsImage?.current;
    const refGdsMetrics = scrollRefGdsMetrics?.current;
    const refGdsPex = scrollRefGdsPex?.current;

    if (refGdsImage) {
      refGdsImage?.addEventListener("scroll", handleDebouncedScrollGdsImage);
    }
    if (refGdsMetrics) {
      refGdsMetrics?.addEventListener("scroll", handleDebouncedScrollGdsMetrics);
    }

    // Attach the scroll listener to PEX Data tab only if it's selected
    if (currentPexView === "pexdata" && refGdsPex) {
      refGdsPex?.addEventListener("scroll", handleDebouncedScrollGdsPex);
    }

    // Cleanup function to remove the scroll event listeners when the component is unmounted
    return () => {
      if (refGdsImage) {
        refGdsImage?.removeEventListener("scroll", handleDebouncedScrollGdsImage);
      }
      if (refGdsMetrics) {
        refGdsMetrics?.removeEventListener("scroll", handleDebouncedScrollGdsMetrics);
      }

      // Only remove the PEX Data scroll event listener if currently on PEX Data tab
      if (currentPexView === "pexdata" && refGdsPex) {
        refGdsPex?.removeEventListener("scroll", handleDebouncedScrollGdsPex);
      }
    };

  }, [debouncedScroll, currentPexView]);


  // below use effect handles the selected cells to set based on action in running the project
  useEffect(() => {
    //filtering selected gdsitems to filter out cells name from it & send those cells name to run 
    //filtering out cell based on _ logic
    let extractingCellName = [];
    if (isGdsSelectAllChecked) {
      extractingCellName = stage1Result?.data?.PEX_Consolidated?.map((item) => item?.name) || [];
    } else {
      extractingCellName = selectedGdsItems?.map((selectedGDSItem) => selectedGDSItem?.split('_')[0]) || [];
    }

    //filtering unique cell names only
    let selectedCellsForHyperRun = [...new Set(extractingCellName)];
    setStage1CellInfo(selectedCellsForHyperRun); // cell info values will be set based on action 3
    if (action === 3) {
      setIsRunningJobCompleted(false);
    }
  }, [selectedGdsItems, handleHyperExpressivityFlowProjectSave, setIsUserOnStage2Page, netlistCellInfo, projectDetailsSelectedForHyperExpressivityFlow, setStage1CellInfo, action, setIsRunningJobCompleted, actionSelected, isGdsSelectAllChecked, stage1Result])


  //below use effect handles creating project with stage1 result modal body content
  useEffect(() => {
    if (isProjectWithStage1ResultModalOpen && projectListWithStage1Result) {
      setProjectListStage1ModalBody({
        title: "Choose a Project With Layouts",
        body: (
          <ProjectWithStage1ResultListModalBody
            projectListWithStage1Result={projectListWithStage1Result}
            handleStateSetForProjectSelection={
              handleStateSetForProjectSelection
            }
          />
        ),
        footer: (
          <>
            {" "}
            <Button
              id="ok-button-stage1projectlist-hyperexpressivity-flow"
              className={`col-4 m-2 ${!isProjectSelected ? "app-secondary-button-color border-0 cursor_not_allowed" : "app-primary-button-color border-0"
                }`}
              disabled={!isProjectSelected}
              onClick={() => {
                handleOkButtonRowSelectionInStage1ProjectListModal();
              }}
              data-tooltip-id="tooltip-loadlayoutdata-OkButton"
              data-tooltip-content="Select atleast one project to proceed ahead."
              data-tooltip-place="top"
            >
              Ok
            </Button>
            {(!isProjectSelected) && (<ReactTooltip id="tooltip-loadlayoutdata-OkButton" />)}
            <Button
              id="cancel-button-stage1projectlist-hyperexpressivity-flow"
              onClick={handleCloseViewStage1ProjectListModal}
              className="col-4 m-2 app-secondary-button-color border-0"
            >
              Cancel
            </Button>
          </>
        ),
      });
    } else {
      setProjectListStage1ModalBody({
        title: "Choose a Project With Layouts",
        body: (
          <ProjectWithStage1ResultListModalBody
            projectListWithStage1Result={null}
            handleStateSetForProjectSelection={
              handleStateSetForProjectSelection
            }
          />
        ),
        footer: (
          <>
            <Button
              id="cancel-button-stage1projectlist-hyperexpressivity-flow app-secondary-button-color border-0"
              onClick={handleCloseViewStage1ProjectListModal}
              className="col-4 m-2"
            >
              Cancel
            </Button>
          </>
        ),
      });
    }
  }, [
    handleOkButtonRowSelectionInStage1ProjectListModal,
    handleCloseViewStage1ProjectListModal,
    isProjectWithStage1ResultModalOpen,
    projectListWithStage1Result,
    handleStateSetForProjectSelection,
    isProjectSelected,
  ]);

  useEffect(() => {
    // setting gdsdata to empty when filter is applied to make sure data is refreshed
    if (isStage1FilterApplied || isStage1Level2FilterApplied) {
      hasLoaded.current = false;
      setGdsData([]);// emptying it to refresh gds data on filter
      setPage(0);

    }
  }, [isStage1FilterApplied, isStage1Level2FilterApplied]);

  // Check if the context has initial data and load it
  useEffect(() => {
    setIsStage1FilterApplied(false);// chnaging filter applied value to false , to make sure reapplying of filter works
    setIsStage1Level2FilterApplied(false);// chnaging filter applied value to false , to make sure reapplying of filter works
    if (hasLoaded?.current) return;

    if (stage1Result?.data?.Items?.length && gdsData?.length === 0) {
      const itemsData = stage1Result?.data?.Items;
      const PEX_Consolidated = stage1Result?.data?.PEX_Consolidated;
      const imagePaths = itemsData?.map(item => item?.LayoutData);
      setTotalImages(stage1Result?.data?.TotalItems || 0);

      const loadInitialStage1Data = async () => {
        loadingRef.current = true; // Set loading to true at the start of data fetching

        try {
          const imagesData = await fetchImageData(imagePaths);
          if (!imagesData || !imagesData?.images || imagesData?.images?.length !== itemsData?.length) {
            toast.error("Mismatch in image data fetched");
            console.error("Mismatch in image data fetched", imagesData);
            loadingRef.current = false; // Reset loading to false in case of error
            return;
          }
          const initialImages = itemsData?.map((item, index) => ({
            src: `data:image/png;base64,${imagesData?.images[index].encodedImage}`,
            name: item?.LayoutData?.split("/")?.pop()?.replace(".png", ""),
            metricsData: item?.MetricsData,
            pexData: item?.PEXData,
          }));

          setGdsData({
            items: initialImages,
            PEX_Consolidated: PEX_Consolidated
          });
          hasLoaded.current = true;
        } finally {
          loadingRef.current = false; // Reset loading to false once data is set or error encountered
        }
      };

      loadInitialStage1Data();
    }
  }, [gdsData?.length, stage1Result, setIsStage1FilterApplied, setIsStage1Level2FilterApplied]); // Dependencies to watch for changes

  // const fetchStage2ResultsData = useCallback(async () => {
  //   const stage1Res = await fetchStageData(currentProjectId, 2, 0, filterRequestParameter ? filterRequestParameter : null);
  //   if (stage1Res?.status === true) {
  //     setStage2Result(stage1Res);
  //     setShowResultButtonInStage1ResultInEditMode(true);
  //   }
  //   else {
  //     setShowResultButtonInStage1ResultInEditMode(false);
  //   }
  // }, [currentProjectId, setStage2Result, setShowResultButtonInStage1ResultInEditMode, filterRequestParameter]);

  // // handling showing of showexisiting result  button for action3 in edit mode
  // useEffect(() => {
  //   // scenario that it comes only for action3 from view edit mode
  //   if ((isUserInAction2EditFromViewProject || isUserInAction3EditFromViewProject)) {
  //     if (isUserInEditMode) {
  //       setDoesStage2ResultExisit(true);
  //       fetchStage2ResultsData();
  //     }
  //   }
  // }, [actionSelected, isUserInEditMode, currentProjectId, fetchStage2ResultsData, isUserInAction2EditFromViewProject, isUserInAction3EditFromViewProject]);


  // Below function gives the Run Result Summary Data for Stage1
  const stage1SummaryData = useCallback(async () => {
    try {
      const RunResultSummaryReq = {
        "projectId": currentProjectId,
        "stage": 1
      };
      const RunResultSummaryStage1Res = await RunResultSummaryData(RunResultSummaryReq);

      if (RunResultSummaryStage1Res?.status_code === 200) {
        setStage1RunResultSummaryData(RunResultSummaryStage1Res);
      }
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  }, [currentProjectId, setStage1RunResultSummaryData])

  useEffect(() => {
    if(currentProjectId && !stage1RunResultSummaryData){
    stage1SummaryData();
    }
  }, [stage1SummaryData, currentProjectId, stage1RunResultSummaryData]);

  // the below function is called when the stage1Result are present
  useEffect(() => {
    if (stage2Result && stage2Result?.data) {
      setDoesStage2ResultExisit(true);
      setShowResultButtonInStage1ResultInEditMode(true);
    }
  }, [stage2Result, setDoesStage2ResultExisit, setShowResultButtonInStage1ResultInEditMode])

  //to store total GDS value
  useEffect(() => {
    if (stage1Result?.data?.TotalGdsCount) {
      setStage1TotalGDSNumber(stage1Result?.data?.TotalGdsCount);
    }
  }, [stage1Result, setStage1TotalGDSNumber,]);


  useEffect(()=>{
      //below useEffect handles fetching of stageResult based on if stage result present button on of off 
      if(isStage2RunResultPresent){
        const fetchStage2ResultsData = async () => {
          const stage2Res = await fetchStageData(currentProjectId, 2, 0,filterRequestParameter?filterRequestParameter:null);
          if (stage2Res?.status === true) {
            if(stage2GraphSelectedGdsCells?.length === 0){
            setStage2Result(stage2Res);
            }
            setShowResultButtonInStage1ResultInEditMode(true);
          }else{
            setShowResultButtonInStage1ResultInEditMode(false);
          }
        };
        fetchStage2ResultsData();
      }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    },[isStage2RunResultPresent,currentProjectId,setStage2Result, stage2GraphSelectedGdsCells])

    useEffect(() => {
      if(isUserInEditMode){
      // useeffect checks if exisiting reuslts are there or not there if there then it will set which will show exisiting results button
      
      const runResultReqBodyStage2 = {
        "projectId": currentProjectId,
        "stage": 2
      }
       if (action === 2) {
        (async () => {
          const resultResStage2 = await getRunResultsStatus(runResultReqBodyStage2);
          setIsStage2RunResultPresent(resultResStage2);
          
        })();
      }else if (action === 3) {
            (async () => {
             
              const resultResStage2 = await getRunResultsStatus(runResultReqBodyStage2);
              
              setIsStage2RunResultPresent(resultResStage2);
            })();
    } 
    }},[isUserInEditMode,action,currentProjectId,setIsStage2RunResultPresent])
  //below useeffect sets content on sidebar
  useEffect(() => {
    setSidebarContent({
      upper: (
        <div>
          <div className="mb-0">
            <h6 className="mb-0">Project Name:</h6>
            <span
              id="sidebar-project-name"
              className="text-muted text-break text-dark"
            > {projectName} </span>
          </div>
          <h6 className="mb-0">Selected Netlist File:</h6>
          <span className="text-muted text-break text-dark" id="netlist-selected-filename">
            {selectedNetlistFileName
              ? selectedNetlistFileName
              : "No file selected"}
          </span>
          <h6 className="">Selected PDK/Tech File:</h6>
          <span className="text-muted text-break text-dark" id="techfile-selected-filename">
            {selectedTechFileName ? selectedTechFileName : "No file selected"}
          </span>
          {actionSelected === 2 && (
            <>
              <h6 className="">Selected Project Name With Layouts:</h6>
              <span className="text-muted text-break text-dark" id="selected-project-name-with-layouts">
                {selectedProjectNameWithStage1Result ? selectedProjectNameWithStage1Result : "No file selected"}
              </span>
            </>
          )}
          <div className="d-flex align-items-center gap-1 " id="side-bar-upper-no-of-GDS-images-generated">
            <h6 className="mt-1">No. of Generated GDS Images:</h6>
            {/* <span className="text-muted text-break text-dark" id="no-of-GDS-images-generated">{totalImages ? totalImages : 0}</span> */}
            {/** reading total no of generated imgaes from end pt as it send no of gds generated*/}
            <span className="text-muted text-dark mb-1" id="no-of-GDS-images-generated">{stage1TotalGDSNumber || 0}</span>
          </div>
          {/* below is displayed only if filter is applied */}
          {(isFilterApplied || stage1Level2Filter?.length > 0) && (
            <div className="d-flex align-items-center gap-1" id="side-bar-upper-filtered-no-of-GDS-images-generated-stage1">
              <h6 className="">No. of Filtered GDS Images:</h6>
              <span className="text-muted text-break text-dark mb-1" id="filtered-no-of-GDS-images-generated">{stage1Result?.status === false ? 0 : (totalImages ? totalImages : 0)}</span>
            </div>)}
          {(actionSelected === 2 || actionSelected === 3) && (
            <>
              <div className="d-flex align-items-center gap-1" id="side-bar-upper-selected-no-of-GDS-items">
                <h6 className="">Selected No of GDS Items:</h6>
                <span className="text-muted text-break text-dark mb-1" id="selected-no-of-GDS-items"> {isGdsSelectAllChecked ? totalImages : selectedGdsItems ? selectedGdsItems?.length : "0"}</span>
              </div>
            </>
          )
          }

        </div>
      ),
      lower: (
        <div className="col-12">
          <div className="row">
            {/* button below is visible on UI only when user lands on this page from previous button on stage2 page */}
            {( ( action === 2 || action === 3) && isStage2RunResultPresent  && showResultButtonInStage1ResultInEditMode)&&(
            <div className="btn-group" role="group" aria-label="First group">
              {/* {(((doesStage2ResultExisit) || (stage2Result && stage2Result?.data && Array.isArray(stage2Result?.data?.Items))) && showResultButtonInStage1ResultInEditMode) && ( */}
             
                <Button
                  id="show-layout-existing-result"
                  onClick={handleShowExisitingHyperResult}
                  className="my-1 w-100 app-primary-button-color border-0"
                >
                  Show HyperExpressivity Result
                </Button>
             
            </div>
             )}
            {actionSelected === 2 && (
              <div className="btn-group " role="group" aria-label="First group">
                {(isUserInEditMode && isButtonDisabledInEditMode) ||
                  (!isUserInEditMode && !isButtonDisabledInEditMode) ?
                  (<Button
                    id="viewprojectlist-with-layout-select-button"
                    onClick={handleViewStage1ProjectListModal}
                    disabled={isButtonDisabledInEditMode}
                    className={`my-1 w-100 ${isButtonDisabledInEditMode ? "cursor_not_allowed app-secondary-button-color border-0" : "app-primary-button-color border-0"}`}
                    data-tooltip-id="load-layout-data-in-stage1-tooltip"
                    data-tooltip-content={isButtonDisabledInEditMode && "You cannot change layout data after saving project once."}
                  >
                    Load Layout Data
                  </Button>) : null
                }
                {isButtonDisabledInEditMode && <ReactTooltip id="load-layout-data-in-stage1-tooltip" place="top" style={{ width: "260px", zIndex: 9999 }} />}
              </div>
            )}
            {/* Save & Run button are visible only when flow is through hyperexpressivity */}
            {(actionSelected === 2 || actionSelected === 3) ? (
              <>
                {/* run button */}
                <div className="btn-group" role="group" aria-label="First group">
                  {/* <div className={`${actionSelected === 3 ? "w-100" : "w-50"}`}> */}
                  <Button
                    id="run-stage2-button"
                    onClick={handleHyperExpressivityFlowProjectRun}
                    className={`my-1 w-100  ${(isHyperExpressivityProjectSaved || isUserInEditMode) && !selectedGdsItems?.length <= 0 ? "app-primary-button-color border-0" : "app-secondary-button-color border-0 cursor_not_allowed"}`}
                    disabled={(!isHyperExpressivityProjectSaved && !isUserInEditMode) || selectedGdsItems?.length <= 0 || !selectedGdsItems}
                    data-tooltip-id="run-button-action-3-tooltip"
                    data-tooltip-content={(!isHyperExpressivityProjectSaved && !isUserInEditMode) ? "Save project atleast once to run project" : (selectedGdsItems?.length <= 0 ? "You need to select at least one layout to run the project." : null)}
                    data-tooltip-place="top"
                  >
                    Run HyperExpressivity
                  </Button>
                  {((!isHyperExpressivityProjectSaved && !isUserInEditMode) || selectedGdsItems?.length <= 0) &&
                    <ReactTooltip id="run-button-action-3-tooltip" style={{ width: "170px", zIndex: 9999 }} />
                  }
                  {/* </div> */}
                </div>
                <div className="btn-group" role="group" aria-label="First group">
                  <Button
                    id="previous-hyperexpressivity-flow-button"
                    className={`ms-0 my-1 w-50 ${(actionSelected === 2) && "mx-2"}  ${isHyperExpressivityProjectSaved ? "app-secondary-button-color border-0 cursor_not_allowed" : "app-primary-button-color border-0"}`}
                    onClick={handlePreviousButton}
                    disabled={isHyperExpressivityProjectSaved}
                    data-tooltip-id="previous-button-inhyperflow-stage1-tooltip"
                    data-tooltip-content={isHyperExpressivityProjectSaved && "You cannot go further previous, since project is already saved."}
                    data-tooltip-place="top"
                  >
                    Previous
                  </Button>
                  {/* save button */}
                  {actionSelected !== 3 && (
                    <>
                      <Button
                        id="save-hyperexpressivity-button"
                        className={`ms-0 my-1 w-50 ${(isUserInEditMode ? selectedGdsItems?.length <= 0 : (selectedGdsItems?.length <= 0 || !isProjectWithStage1ResultSelectedFromList)) ? "app-secondary-button-color border-0 cursor_not_allowed" : "app-primary-button-color border-0"}`}
                        onClick={handleHyperExpressivityFlowProjectSave}
                        disabled={selectedGdsItems?.length <= 0 || (!isProjectWithStage1ResultSelectedFromList && !isUserInEditMode)}
                        data-tooltip-id="save-button-action-3-tooltip"
                        data-tooltip-content={(!isProjectWithStage1ResultSelectedFromList && !isUserInEditMode) ? "Select project with layout result using loadlayoutdata button to proceed ahead" : (selectedGdsItems?.length <= 0 ? "Select atleast one GDSitem to save or run project" : null)}
                        data-tooltip-place="top"
                      >
                        Save
                      </Button>
                      {((!isProjectWithStage1ResultSelectedFromList && !isUserInEditMode) || selectedGdsItems?.length <= 0) &&
                        <ReactTooltip id="save-button-action-3-tooltip" style={{ width: "170px", zIndex: 9999 }} />
                      }
                    </>
                  )}
                </div>
                {/* close button */}
                <div className="btn-group" role="group" aria-label="First group">
                  <Button
                    id="cancel-hyperexpressivity-flow-button"
                    className={`my-1 w-50 app-secondary-button-color border-0 ${!true ? "cursor_not_allowed" : ""}`}
                    onClick={handleCancelButton}
                  >
                    Close
                  </Button>
                </div>
              </>
            ) : (

              <div className="btn-group" role="group" aria-label="Second group">
                <Button
                  id="previous-hyperexpressivity-flow-button"
                  className={`ms-0 mx-2 my-1 w-50 ${isHyperExpressivityProjectSaved ? "app-secondary-button-color border-0 cursor_not_allowed" : "app-primary-button-color border-0"}`}
                  onClick={handlePreviousButton}
                  disabled={isHyperExpressivityProjectSaved}
                  data-tooltip-id="previous-button-inhyperflow-stage1-tooltip"
                  data-tooltip-content={isHyperExpressivityProjectSaved && "You cannot go further previous, since project is already saved."}
                  data-tooltip-place="top"
                >
                  Previous
                </Button>
                <Button
                  id="cancel-hyperexpressivity-flow-button"
                  className={`my-1 w-50 app-secondary-button-color border-0 ${!true ? "cursor_not_allowed" : ""}`}
                  onClick={handleCancelButton}
                >
                  Close
                </Button>
              </div>
            )}
          </div>
          {isHyperExpressivityProjectSaved &&
            <ReactTooltip id="previous-button-inhyperflow-stage1-tooltip" place="top" style={{ width: "160px", zIndex: 9999 }} />
          }
        </div>
      )
    });
  }, [isStage2RunResultPresent, isFilterApplied, stage1TotalGDSNumber, stage1Level2Filter, stage1Result?.data?.TotalGdsCount, doesStage2ResultExisit, isUserInAction2EditFromViewProject, stage1Result, handleShowExisitingHyperResult, stage2Result, handleHyperExpressivityFlowProjectRun, handleHyperExpressivityFlowProjectSave, handleViewStage1ProjectListModal, isProjectWithStage1ResultSelectedFromList, isHyperExpressivityProjectSaved, selectedProjectNameWithStage1Result, actionSelected, setSidebarContent, selectedNetlistFileName, selectedTechFileName, totalImages, handlePreviousButton, handleCancelButton, isButtonDisabledInEditMode, isUserInEditMode, selectedGdsItems, action, showResultButtonInStage1ResultInEditMode, isGdsSelectAllChecked, projectName]);


  // Modal content for already running project
  const projectRunningModalContent = {
    title: "Project Status",
    body: <h6>{projectRunningMessage}</h6>,
    footer: (
      <Button
        id="project-running-ok-button-stage2"
        className="w-25 app-primary-button-color border-0"
        onClick={() => setIsProjectRunningModal(false)}
      >
        OK
      </Button>
    ),
  };

  const handleGDSImageToggle = (e) => {
    const isChecked = (prevState => !prevState)
    setGdsLayoutToggle(isChecked);
  };

  return (
    <>
      {/* modal for showing list of user projects having stage1 results , shown when user is in only hyperexpressivity creation flow */}
      <ModalComponent
        id={"projectlist-with-stage1-result-modal"}
        show={isProjectWithStage1ResultModalOpen}
        handleClose={handleCloseViewStage1ProjectListModal}
        modalContent={projectListStage1ModalBody}
        bodyClassName={"p-3 pt-0 overflow-auto"}
      />
      <ToastContainer
        closeButton={true}
        position="top-center"
        autoClose={false} // autoclose is false since here we are showing for error
        theme="colored"
      />

      <div
        className="container-fluid d-flex flex-column h-100 p-0 pt-1 m-0"
        style={{ overflow: "hidden" }}
      >
        <div
          className="row flex-grow-1 m-0 p-0"
          style={{ height: "100%", overflow: "hidden" }}
        >
          <div className="col-12 d-flex flex-column h-100 pe-0">
            <ul className="nav nav-tabs justify-content-center" id="stage1-result-tabs-list" role="tablist">
              {/* Tab 1 */}

              {stage1RunResultSummaryData &&
                (<li className="nav-item ms-auto tabs-border" role="presentation">
                  <a
                    className="nav-link tabs-btn fw-bold text-uppercase border px-4 py-2"
                    id="run-result-summary-tab-stage-1"
                    role="tab"
                    data-bs-toggle="tab"
                    href="#run-result-summary-stage-1"
                    aria-controls="summary-tab"
                    aria-selected="true"
                    data-tooltip-id="Summary-tooltip"
                    data-tooltip-content="Run Summary"
                    data-tooltip-place="top"
                  >
                    <FontAwesomeIcon icon={faFileLines} style={{ fontSize: "20px" }} />
                  </a>
                  <ReactTooltip id="Summary-tooltip" style={{ zIndex: 9999 }} />
                </li>)}

              {/* Tab 2 */}
              <li className={`nav-item tabs-border ${!stage1RunResultSummaryData && "ms-auto"}`}
                role="presentation">
                <a
                  className="nav-link active tabs-btn fw-bold text-uppercase border px-4 py-2"
                  id="gds-image-tab"
                  role="tab"
                  data-bs-toggle="tab"
                  href="#gds-image"
                  aria-controls="gds-image"
                  aria-selected="true"
                  data-tooltip-id="gds-tooltip"
                  data-tooltip-content="GDS Layouts"
                  data-tooltip-place="top"
                >
                  <FontAwesomeIcon icon={faImages} style={{ fontSize: "20px" }} />
                </a>
                <ReactTooltip id="gds-tooltip" style={{ zIndex: 9999 }} />
              </li>
              {/* Tab 3 */}
              {/* metric tab is only visible in qa env for analysis it is not visible in prod it is enabled disabled based on the env flag */}
              {isDebugModeOn && (
              <li className="nav-item tabs-border " role="presentation">
                <a
                  className="nav-link tabs-btn fw-bold text-uppercase border px-4 py-2"
                  id="gds-metrics-tab"
                  role="tab"
                  data-bs-toggle="tab"
                  href="#gds-metrics"
                  aria-controls="gds-metrics"
                  aria-selected="true"
                  data-tooltip-id="Metric-tooltip"
                  data-tooltip-content="Metric Values"
                  data-tooltip-place="top"
                >
                  <FontAwesomeIcon icon={faTable} style={{ fontSize: "20px" }} />
                </a>
                <ReactTooltip id="Metric-tooltip" style={{ zIndex: 9999 }} />
              </li>
              )}
              {/* Tab 4 */}
              <li className="nav-item tabs-border" role="presentation">
                <a
                  className="nav-link tabs-btn fw-bold text-uppercase border px-4 py-2"
                  id="gds-pex-tab"
                  role="tab"
                  data-bs-toggle="tab"
                  href="#gds-pex"
                  aria-controls="gds-pex"
                  aria-selected="true"
                  data-tooltip-id="PEX-tooltip"
                  data-tooltip-content="PEX Predictions"
                  data-tooltip-place="top"
                >
                  <FontAwesomeIcon icon={faChartColumn} style={{ fontSize: "20px" }} />
                </a>
                <ReactTooltip id="PEX-tooltip" style={{ zIndex: 9999 }} />
              </li>
              <li className="nav-item tabs-border"
                role="presentation"
              >
                <a
                  className="nav-link tabs-btn fw-bold text-uppercase border px-4 py-2"
                  id="gds-graph-tab"
                  role="tab"
                  data-bs-toggle="tab"
                  href="#gds-graphs"
                  aria-controls="gds-graph"
                  aria-selected="true"
                  data-tooltip-id="GRAPH-tooltip"
                  data-tooltip-content="Graph Layout"
                  data-tooltip-place="top"
                >
                  <FontAwesomeIcon icon={faChartLine} style={{ fontSize: "20px" }} />
                </a>
                <ReactTooltip id="GRAPH-tooltip" style={{ zIndex: 9999 }} />
              </li>
              {/* Last Tab - Align this to the right */}

              <li className="nav-item ms-auto d-flex" role="presentation">
                <div className="nav-item ms-auto d-flex align-items-center me-3">
                  {/* view Cart */}
                  {stage1GdsCartData?.length > 0 && (
                    <button
                      className="border-0 bg-transparent active tabs-btn cursor_pointer"
                      id="stage-1-view-cart-tab"
                      role="tab"
                      aria-controls="stage-1-view-cart"
                      aria-selected="true"
                      data-tooltip-id="view-cart-tooltip"
                      data-tooltip-content="View Cart"
                      data-tooltip-place="top"
                      onClick={() => setViewCartOption(true)}
                    >
                      <FontAwesomeIcon
                        icon={faCartShopping}
                        style={{ fontSize: "16px" }}
                      />
                      <span
                        className="view-cart-count position-relative text-white px-1 rounded"
                      >
                        {stage1GdsCartData?.length}
                      </span>
                      <ReactTooltip id="view-cart-tooltip" style={{ zIndex: 9999 }} />
                    </button>
                  )}
                  {/* sync level2 filters button */}
                  {(isStage1Level2FilterApplied || stage1Level2Filter.length > 0 )&& (
                    <button
                      className="btn btn-link button-primary-color p-0 me-3"
                      id="stage-1-graph-filter2-sync-across-tab-btn"
                      onClick={handleApplyFilterStage1}
                      style={{ transition: 'color 0.2s ease' }}
                      //onMouseEnter={(e) => e.target.style.color = '#007bff'}  
                      //onMouseLeave={(e) => e.target.style.color = 'inherit'}
                      data-tooltip-id="overall-stage-1-graph-filter2-sync-across-tab-btn-tooltip"
                      data-tooltip-content="Sync Filtered Data Across Tabs"
                      data-tooltip-place="top"
                    >
                      <FontAwesomeIcon icon={faRotate} size="md" />
                      <ReactTooltip id="overall-stage-1-graph-filter2-sync-across-tab-btn-tooltip" style={{ zIndex: 9999 }} />
                    </button>

                  )}
                  {/* filter button */}
                  {stage1RunResultSummaryData && (
                    <button
                      className="border-0 bg-transparent active tabs-btn"
                      id="stage-1-gds-filter-tab"
                      role="tab"
                      aria-controls="stage-1-gds-filter-tab"
                      aria-selected="true"
                      data-tooltip-id="filter-results-tooltip"
                      data-tooltip-content="Filter Run Results"
                      data-tooltip-place="top"
                      onClick={() => { setFilterResultSlider(true) }}
                    >
                      <FontAwesomeIcon icon={faFilter} style={{ fontSize: "16px" }} />

                      <ReactTooltip id="filter-results-tooltip" style={{ zIndex: 9999 }} />
                    </button>
                  )}
                  {(( isFilterApplied ) || (isStage1Level2FilterApplied || stage1Level2Filter.length > 0 ) || stage1GraphSelectedGdsCells )&& (
                  <button
                      className="border-0 bg-transparent active tabs-btn"
                      id="stage-1-clear-filter-button"
                      role="tab"
                      aria-controls="clear-filter-button"
                      aria-selected="true"
                      data-tooltip-id="clear-filter-tooltip"
                      data-tooltip-content="Clear Filters"
                      data-tooltip-place="top"
                      onClick={clearFilterButton}
                  >
                      <FontAwesomeIcon
                          icon={faTrash}
                          style={{ fontSize: "16px" }}
                      />

                      <ReactTooltip id="clear-filter-tooltip" style={{ zIndex: 9999 }} />
                  </button>
                  )}
                  <button
                    className="border-0 bg-transparent active tabs-btn"
                    id="stage-1-gds-download-tab"
                    role="tab"
                    aria-controls="stage-1-gds-download"
                    aria-selected="true"
                    data-tooltip-id="download-tooltip"
                    data-tooltip-content="Download Result"
                    data-tooltip-place="top"
                    onClick={downloadButton}
                  >
                    <FontAwesomeIcon
                      icon={faDownload} style={{ fontSize: "16px" }}
                    />
                  </button>
                  <ReactTooltip id="download-tooltip" style={{ zIndex: 9999 }} />
                </div>
              </li>
            </ul>

            {/* Tab Content */}
            <div className="tab-content flex-grow-1 " id="myTabContent" style={{ overflowY: "auto" }}>
              {/* Tab 1 Content */}
              <div
                className="tab-pane fade show w-100 h-100"
                id="run-result-summary-stage-1"
                role="tabpanel"
                aria-labelledby="run-result-summary-tab-stage-1"
                ref={scrollRefGdsImage}
                style={{ overflowY: "auto", maxHeight: "calc(100vh - 0px)" }}
              >
                <div className="col-3 d-flex justify-content-start w-100 align-items-center my-2 ps-3">
                  <RunResultSummary stage1RunResultSummaryData={stage1RunResultSummaryData} />
                </div>
              </div>
              {/* Tab 2 Content */}
              <div
                className="tab-pane fade show active h-100"
                id="gds-image"
                role="tabpanel"
                aria-labelledby="gds-image-tab"
                ref={scrollRefGdsImage}
                style={{ overflowY: "auto", maxHeight: "calc(100vh - 0px)" }}
              >
                <div className="col-3 d-flex justify-content-start align-items-center my-2 ps-3">
                  {!isUserOnStage2Page && gdsData?.length !== 0 && (action === 2 || action === 3) && (

                    <div className="form-check">
                      <input
                        className="form-check-input shadow-none"
                        type="checkbox"
                        role="switch"
                        id="stage-1-select-all-layout-image-toggle-button"
                        checked={isGdsSelectAllChecked}
                        onChange={handleGdsSelectAllChange}
                        style={{ cursor: "pointer" }}
                      />
                      <label
                        className="form-check-label"
                        htmlFor="stage-1-select-all-layout-image-toggle-button"
                      >
                        Select All GDS Layout
                      </label>
                    </div>
                  )}

                </div>
                <LayoutImageData
                  gdsData={gdsData}
                  loadingRef={loadingRef}
                  actionSelected={actionSelected}
                  loadingMore={loadingMore}
                  setViewCartOption={setViewCartOption}
                  stageGdsCartData={stage1GdsCartData}
                  userCurrentStage={1}
                />
              </div>

              {/* Tab 3 Content */}
              <div
                className="tab-pane fade h-100"
                id="gds-metrics"
                role="tabpanel"
                aria-labelledby="metricsData-tab"
                ref={scrollRefGdsMetrics}
                style={{ overflowY: "auto", maxHeight: "calc(100vh - 0px)" }}
              >
                <div className="col-3 d-flex justify-content-start align-items-center my-2 ps-3">
                  {gdsData?.length !== 0 && (action === 2 || action === 3) && (
                    <div className="form-check">
                      <input
                        className="form-check-input shadow-none"
                        type="checkbox"
                        role="switch"
                        id="stage-1-select-all-layout-metrics-toggle-button"
                        checked={isGdsSelectAllChecked}
                        onChange={handleGdsSelectAllChange}
                        style={{ cursor: "pointer" }}
                      />
                      <label
                        className="form-check-label"
                        htmlFor="stage-1-select-all-layout-metrics-toggle-button"
                      >
                        Select All GDS Layout
                      </label>
                    </div>
                  )}
                </div>
                <LayoutMetricsData
                  gdsData={gdsData}
                  loadingRef={loadingRef}
                  actionSelected={actionSelected}
                  loadingMore={loadingMore}
                />
              </div>

              {/* Tab 4 Content with Toggle */}
              <div
                className="tab-pane fade h-100 pe-2"
                id="gds-pex"
                role="tabpanel"
                aria-labelledby="gds-pex-tab"
                ref={scrollRefGdsPex}
                style={{ overflowY: "auto", maxHeight: "calc(100vh - 0px)" }}
              >
                <div className="col-12 d-flex justify-content-start align-items-center my-2">
                  <div className="d-flex justify-content-start align-items-center my-2">
                    <div className="form-check ms-3">
                      <input
                        className="form-check-input shadow-none"
                        type="radio"
                        id="stage1-total-data-view"
                        checked={currentPexView === "totaldata"}
                        onChange={() => setCurrentPexView("totaldata")}
                      />
                      <label className="form-check-label" htmlFor="total-data-view">
                        Total PEX Data
                      </label>
                    </div>
                    <div className="form-check ms-3">
                      <input
                        className="form-check-input shadow-none"
                        type="radio"
                        id="stage1-pex-data-view"
                        checked={currentPexView === "pexdata"}
                        onChange={() => setCurrentPexView("pexdata")}
                      />
                      <label className="form-check-label" htmlFor="pex-data-view">
                        PEX Data
                      </label>
                    </div>
                    <div className="form-check ms-3">
                      <input
                        className="form-check-input shadow-none"
                        type="radio"
                        id="stage1-consolidated-data-view"
                        checked={currentPexView === "consolidateddata"}
                        onChange={() => setCurrentPexView("consolidateddata")}
                      />
                      <label className="form-check-label" htmlFor="consolidated-data-view">
                        Consolidated PEX View
                      </label>
                    </div>

                  </div>

                  {/* Only show Select All GDS Layout when PEX Data is selected */}
                  {(currentPexView === "pexdata" && stage1Result) && (action === 2 || action === 3) && (
                    <div className="form-check ms-3">
                      <input
                        className="form-check-input shadow-none"
                        type="checkbox"
                        role="switch"
                        id="stage-1-select-all-layout-metrics-toggle-button"
                        checked={isGdsSelectAllChecked}
                        onChange={handleGdsSelectAllChange}
                        style={{ cursor: "pointer" }}
                      />
                      <label className="form-check-label" htmlFor="stage-1-select-all-layout-metrics-toggle-button">
                        Select All GDS Layout
                      </label>
                    </div>
                  )}
                  {(currentPexView === "totaldata" && stage1Result?.data) && (
                    <div className="form-check ms-3 form-switch">
                      <input
                        className="form-check-input shadow-none"
                        type="checkbox"
                        role="switch"
                        id="stage-1-select--GDS-image-toggle-button"
                        onChange={handleGDSImageToggle}
                        checked={gdsLayoutToggle}
                        style={{ cursor: "pointer" }}
                        disabled={false}
                      />
                      <label className="form-check-label" htmlFor="stage-1-select-all-layout-metrics-toggle-button">
                        Show GDS Layouts
                      </label>
                      {isTableImageLoading && (
                        <div className="spinner-border spinner-border-sm ms-2" role="status">
                          <span className="visually-hidden">Loading...</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Conditional Rendering of Views */}
                {currentPexView === "pexdata" ? (
                  <LayoutPexData
                    gdsData={gdsData}
                    loadingRef={loadingRef}
                    actionSelected={actionSelected}
                    loadingMore={loadingMore}
                  />
                ) : currentPexView === "consolidateddata" ? (
                  <LayoutPexDataConsolidated
                    gdsData={gdsData}
                    loadingRef={loadingRef}
                    actionSelected={actionSelected}
                    loadingMore={loadingMore}
                  />
                ) : currentPexView === "totaldata" ? (
                  <LayoutTotalData
                    gdsData={gdsData}
                    showImageColumn={showImageColumn}
                    setShowImageColumn={setShowImageColumn}
                    setIsTableImageLoading={setIsTableImageLoading}
                    userCurrentStage={1}
                    stageGdsCartData={stage1GdsCartData}
                    setViewCartOption={setViewCartOption}
                    gdsLayoutToggle={gdsLayoutToggle}
                    setGdsLayoutToggle={setGdsLayoutToggle}
                    showGDSLayoutImageData={showGDSLayoutImageData}
                    setShowGDSLayoutImageData={setShowGDSLayoutImageData}
                    loadingRef={loadingRef}
                  />
                ) : null}
              </div>


              {/* Tab 4 Content with Toggle */}
              <div
                className="tab-pane fade h-100 "
                id="gds-graphs"
                role="tabpanel"
                aria-labelledby="gds-graph-tab"
                style={{ overflowY: "auto", maxHeight: "calc(100vh - 0px)" }}
              >
                <LayoutGraphDataStage1
                  totalImages={totalImages}
                  gdsData={gdsData}
                  projectName={projectName}
                  stage={1}
                  toggleSidebar={toggleSidebar}
                  isSidebarCollapsed={isSidebarCollapsed}
                  currentProjectId={currentProjectId}
                  terminalHeight={terminalHeight}
                  selectedProjectIdFromList={selectedProjectIdFromList}
                  columns={
                    gdsData && gdsData.PEX_Consolidated && gdsData.PEX_Consolidated.length > 0
                      ? [
                        ...new Set(
                          gdsData.PEX_Consolidated.flatMap(index =>
                            index.data.flatMap(item =>
                              Object.keys(item).filter(column => column !== "File" && column !== "LayoutData")
                            )
                          )
                        )
                      ]
                      : [] // If no data, pass an empty array
                  }
                  loadingRef={loadingRef}
                  actionSelected={actionSelected}
                  loadingMore={loadingMore}
                  setViewCartOption={setViewCartOption}
                  setSelectedCellFromList={setSelectedCellFromList}
                  gdsLayoutToggle={gdsLayoutToggle}
                  setGdsLayoutToggle={setGdsLayoutToggle}
                  showGDSLayoutImageData={showGDSLayoutImageData}
                  setShowGDSLayoutImageData={setShowGDSLayoutImageData} 
                />
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* Modal for getting confirmation before user hits run project */}
      <ModalComponent
        id="user-confirmation-modal-run"
        size="md"
        show={userRunConfirmationModal}
        handleClose={() => setRunUserConfirmationModal(false)}
        modalContent={confirmationModalContent}
        modalCSSClass={"overflow-hidden;"}
      />
      {/* Modal for getting user's confirmation to overwrite the existing result or not */}
      <ModalComponent
        id="delete-run-results-user-confirmation-modal"
        size="md"
        show={isDeleteRunProjectResultModalOpen}
        handleClose={() => setIsDeleteRunProjectResultModalOpen(false)}
        modalContent={overrideRunResultConfirmationModalContent}
        modalCSSClass={"overflow-hidden;"}
      />
      <ModalComponent
        id="project-running-stage-modal"
        size="md"
        show={isProjectRunningModal}
        handleClose={() => setIsProjectRunningModal(false)}
        modalContent={projectRunningModalContent}
        modalCSSClass={"overflow-hidden"}
      />
      {/* Modal to download result */}
      <ModalComponent
        id="download-gds-result-modal"
        size="lg"
        show={downloadResultModal}
        handleClose={() => setDownloadResultModal(false)} // Close the modal on close button
        modalContent={DownloadResultsModalContent}
        modalCSSClass={"overflow-hidden;"}
      />
      {/* Modal to get filter options from user */}
      {filterResultSlider && (<FilterRunResults closeFilterResultSlider={closeFilterResultSlider} runSummaryData={stage1RunResultSummaryData?.data} filterStage={1} />)}
      {viewCartOption && (<ViewCart setViewCartOption={setViewCartOption} viewCartOption={viewCartOption} setSelectedCellFromList={setSelectedCellFromList} selectedCellFromList={selectedCellFromList} setDownloadResultModal={setDownloadResultModal} userCurrentStage={1} stageGdsCartData={stage1GdsCartData} />)}
    </>
  );
};

export default Stage1Result;