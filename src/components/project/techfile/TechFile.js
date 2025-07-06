
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: TechFile.js  
 * Description: This file is responsible show tech file data and select variations 
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

import React, { useCallback, useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "./TechFile.css";
import { useTechFileContext } from "../../providers/TechFileProvider/TechFileContext";
import { useRunProjectContext } from "../../providers/RunProjectProvider/RunProjectContext";
import {
  getTechFileData,
  saveProjectInS3,
  getTechFileList,
  runProject,
  deleteRunProjectResult,
  editProjectData,
  getRunResultsStatus,
  fetchStageData,
  uploadProjectTechFile,
  getProjectTechFileList,
  getProjectTechFileData,
  downloadProjectTechFile,
  renameTechFile,
  saveTechFile
} from "../../../server/server";
import { useNetListFileContext } from "../../providers/NetListFileProvider/NetListFileContext";
import { useCreateProjectContext } from "../../providers/CreateProjectProvider/CreateProjectContext";
import { useEditProjectContext } from "../../providers/EditProjectProvider/EditProjectContext";
import { ToastContainer, toast } from "react-toastify";
import { isDebugModeOn } from "../../../constant";
import Modal from "react-bootstrap/Modal";
import Button from "react-bootstrap/Button";
import { Empty } from "antd";
import Parameters from "./parameters/Parameters";
import Variations from "./variations/Variations";
import { useOutletContext } from "react-router-dom";
import ModalComponent from "../../utils/Modal/ModalComponent";
import { useStage1ResultContext } from "../../providers/Stage1ResultProvider/Stage1ResultContext";
import { useStage2ResultContext } from "../../providers/Stage2ResultProvider/Stage2ResultContext";
import { useLayoutGraphContext } from "../../providers/LayoutGraphProvider/LayoutGraphContext";
import { Tooltip as ReactTooltip } from 'react-tooltip'
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faRotate, faTrash, faFileLines } from "@fortawesome/free-solid-svg-icons";
import { useFilterResultsContext } from "../../providers/FilterResultsProvider/FilterResultsContext";
import { userFile } from "../../../constant"
import ProjectTechFileListModalBody from "./ProjectTechFileListModalBody";
import UploadProjectTechFileModalBody from "./UploadProjectTechFileModalBody";
import SaveTechFieModalBody from "./SaveTechFieModalBody";

const TechFile = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { projectName, selectedFeatures, action } = location.state || {};
  const { filterRequestParameter, clearFilterResultsContext, setIsFilterApplied, isFilterApplied, setFilterRequestParameter, stage1GraphSelectedGdsCells, stage2GraphSelectedGdsCells } = useFilterResultsContext();
  const { setSidebarContent } = useOutletContext();
  const { stage1Result, setStage1Result, setSelectedGdsItems, setIsGdsSelectAllChecked, setStage1RunResultSummaryData, setStage1GdsLayoutImageData, setStage1TotalGDSNumber } = useStage1ResultContext();
  const { setIsUserOnStage2Page, setStage2Result, setStage2RunResultSummaryData, setStage2GdsLayoutImageData, setStage2TotalGDSNumber } = useStage2ResultContext();
  const { setIsProjectStillRunning, webSocketObj, setRunLayoutJobId, setRunLayoutRunningJobLogs, setIsRunningJobCompleted, setIsRunningJobErrored } = useRunProjectContext();
  const {
    techFileData,
    setTechFileData,
    isTechFileSelected,
    setIsTechFileSelected,
    selectedTechFileName,
    setSelectedTechFileName,
    selectedTechFileType,
    setSelectedTechFileType,
    isTechDataChanged,
    setIsTechDataChanged,
    defaultTechFileData,
    setDefaultTechFileData,
    techParameterValueError,
    setTechParameterValueError,
    projectTechFileListData,
    setProjectTechFileListData,
    viewProjectTechFile,
    setViewProjectTechFile,
    isTechFileProjectSaved,
    setIsTechFileProjectSaved
  } = useTechFileContext();
  const {
    selectedNetlistFileName,
    selectedNetlistFileType,
    netlistCellInfo,
    netlistFileContent,
    actionSelected,
    setNetlistFileContent,
    setIsNetListFileSelected,
    setNetListFileData,
    setNetlistCellInfo,
    setSelectedNetlistFileName,
    setSelectedNetlistFileType,
    setIsSelectAllChecked,
    isNetlistDataChanged,
    isNetlistFileContentDataChanged,
    setIsNetlistFileContentDataChanged,
    setIsNetlistDataChanged
  } = useNetListFileContext();
  const {
    currentProjectId,
    setCurrentProjectId,
    setIsProjectSaved,
    isProjectSaved,
    isUserInAction1EditFromViewProject,
    isUserInAction3EditFromViewProject,
    setIsUserInAction3EditFromViewProject,
    setIsUserInAction2EditFromViewProject,
    setIsUserInAction1EditFromViewProject,
    typeOfSelectedProject,
    setTypeOfSelectedProject,
    isStage1RunResultPresent,
    isStage2RunResultPresent,
    setIsStage1RunResultPresent,
    setIsStage2RunResultPresent,

  } = useCreateProjectContext();
  const { setStage1GraphData, setStage2GraphData } = useLayoutGraphContext();
  const { isUserInEditMode, setIsUserInEditMode, isButtonDisabledInEditMode, setIsButtonDisabledInEditMode, showResultButtonInTechFileInEditMode, showResultButtonInStage1ResultInEditMode, setShowResultButtonInTechFileInEditMode, setShowResultButtonInStage1ResultInEditMode } = useEditProjectContext();
  const [techFile, setTechFile] = useState(false);
  const [selectedName, setSelectedName] = useState(null);
  const [selectedType, setSelectedType] = useState(null);
  const [techlistData, setTechlistData] = useState([]);
  const [isSuccess, setIsSuccess] = useState(false);
  const [selectedCellInfo, setSelectedCellInfo] = useState();
  const [userConfirmationModal, setUserConfirmationModal] = useState(false);
  const [selectedCellInfoConfirmation, setSelectedCellInfoConfirmation] = useState();
  const [selectedPermutationConfirmation, setSelectedPermutationConfirmation] = useState();
  const [deleteRunProjectModal, setDeleteRunProjectModal] = useState(false);
  const [runModalMessage, setRunModalMessage] = useState();
  const [doesStage1ResultExisit, setDoesStage1ResultExisit] = useState(false);
  const [isProjectRunningModal, setIsProjectRunningModal] = useState(false);
  const [projectRunningMessage, setProjectRunningMessage] = useState("");
  const [doesVariationsExisit, setDoesVariationsExisit] = useState(false);
  const [uploadProjectTechFileModal, setUploadProjectTechFileModal] = useState(false); 
  const [selectedTechFileFromLocal, setSelectedTechFileFromLocal] = useState();
  const [viewProjectTechFileModal, setViewProjectTechFileModal] = useState(false);
  const [projectTechFileList, setProjectTechFileList] = useState({
    title: "",
    body: "",
    footer: ""
  });
  const [selectedProjectTechFileIdFromList, setSelectedProjectTechFileIdFromList] = useState(); 
  const [selectedProjectTechFileNameFromList, setSelectedProjectTechFileNameFromList] = useState();
  const [selectedProjectTechFileProjectIdFromTheList, setSelectedProjectTechFileProjectIdFromList] = useState();
  const [saveTechFileModal, setSaveTechFileModal] = useState(false);
  const [confirmTechFileRenameModal, setConfirmTechFileRenameModal] = useState(false);
  const [newTechFileName, setNewTechFileName] = useState(); // stores new name of tech file
  const [techFileAction, setTechFileAction] = useState(''); //stores the techfile file action 
  const [renameTechFileErrorMessage, setRenameTechFileErrorMessage] = useState(); // stores error message if file name is same
  const [confirmTechFileRenameMessage, setConfirmTechFileRenameMessage] = useState(); // stores the message to confirm rename tech fie
  const [saveTechFileName, setSaveTechFileName] = useState(false); 
  const [loading , setLoading]= useState(false);
  const [isTechFileSaved, setIsTechFileSaved] = useState(false); 

  //getting array of Selected netlist cell info
  useEffect(() => {
    setSelectedCellInfo(
      netlistCellInfo
        ?.filter((obj) => obj?.is_selected)
        ?.map((obj) => obj?.cell_name)
    );
  }, [netlistCellInfo]);

  useEffect(() => {
    setSelectedCellInfoConfirmation(selectedCellInfo?.length);
  }, [selectedCellInfo]);

  useEffect(() => {
    setSelectedPermutationConfirmation(
      techFileData?.data?.FileContent?.find(
        (items) => items.name === "permutation"
      )?.data?.map((subItems) => subItems.name).length
    );
  }, [techFileData]);

  const handleExistingResult = useCallback(async () => {
    try {
      navigate("/dashboard/stage1result", { state: { projectName, selectedFeatures, action } });
    } catch (err) {
      console.error("Fetching Error", err);
    }
  }, [action, navigate, projectName, selectedFeatures]);

  const handleClick = async () => {
    const getTechFileListRes = await getTechFileList();
    try {
      if (getTechFileListRes?.status === false) {
        toast.error(getTechFileListRes?.message);
      } else {
        setTechFile(true);
        setTechlistData(getTechFileListRes.data);
      }
    } catch (err) {
      console.error("Fetching Error", err);
    }
  };

  // when user select on yes it hits the run end point
  const userConfirmationYesButton = async () => {
    setUserConfirmationModal(false);
    const runProjectReq = {
      cells: selectedCellInfo,
      projectId: currentProjectId,
      action: (actionSelected === 1 || actionSelected === 3) ? 1 : actionSelected,
      netlistData: btoa(netlistFileContent),
      techData: techFileData.data,
      selectedLayout: [],
    };
    const runLayoutProjectRes = await runProject(runProjectReq);
    // if there  is already run project data available , user will be asked to confirm for overriding & then deletion activity happens & then project runs
    try {
      if (runLayoutProjectRes?.status_code === 200) {
        setRunLayoutJobId(runLayoutProjectRes?.data?.jobId);
        setRunLayoutRunningJobLogs(["################################################################################################"]);

        navigate("/dashboard/loader", { state: { projectName, selectedFeatures, action: actionSelected } });
      } else if (runLayoutProjectRes?.status_code === 208) {
        // Project is already running - show running project modal
        setProjectRunningMessage(runLayoutProjectRes?.message || "The project is currently in a running state.Please try again later.");
        setIsProjectRunningModal(true);
      }
      else if (runLayoutProjectRes?.data?.status_code === 409) {
        // if filter applied addtional adding further message in run
        const filterMessage = "All the applied filters will be removed."
        setRunModalMessage(`${isFilterApplied ? filterMessage : ''} ${runLayoutProjectRes?.data?.message}` )
        setUserConfirmationModal(false)
        setDeleteRunProjectModal(true)
      }
    } catch (error) {
      toast.error("Error while running layout project ");
      console.error("Error while running project ", error);
    }
  }

  const userConfirmationNoButton = () => {
    setUserConfirmationModal(false);
  };

  const handleRunResultYesButton = async () => {
    const runLayoutProjectReq = {
      cells: selectedCellInfo,
      projectId: currentProjectId,
      action: (actionSelected === 1 || actionSelected === 3) ? 1 : actionSelected,
      netlistData: btoa(netlistFileContent),
      techData: techFileData.data,
      selectedLayout: []
    };
    const deleteRunProjectReq = {
      projectId: currentProjectId,
      stage: (actionSelected === 1 || actionSelected === 3) ? 1 : actionSelected,
    }

    const getUserProjectDeleteRes = await deleteRunProjectResult(deleteRunProjectReq);
    
    try {
      if (getUserProjectDeleteRes?.status_code === 200) {
        setIsFilterApplied(false);//setting filter back to null since rerunning project
        setFilterRequestParameter(null);//setting filter back to null since rerunning project
        setDeleteRunProjectModal(false);
        setStage2Result();//making stage2 results empty on rerun since it is deletion of results
        setDoesStage1ResultExisit(false);
        setShowResultButtonInTechFileInEditMode(false);
        setStage1Result();//make stage1result as empty on deletion of results from s3 , so that no data on local is also there to keep in sync
        setRunLayoutRunningJobLogs(["################################################################################################"]);
        setIsRunningJobCompleted(false);
        setStage1RunResultSummaryData();
        setStage2RunResultSummaryData();
        const runLayoutProjectRes = await runProject(runLayoutProjectReq);
        //once project is deleted successfully , running project 
        try {
          if (runLayoutProjectRes?.status_code === 200) {
            setRunLayoutJobId(runLayoutProjectRes?.data?.jobId);//setting the current running project jobid in context 
            navigate("/dashboard/loader", { state: { projectName, selectedFeatures, action: actionSelected } })
          } else {
            toast.error("Error While running project");
          }
        } catch (error) {
          console.error("Error while running project from layout", error)
        }
      } else {
        toast.error("Error while deleting project in layout");
      }
    } catch (deleteProjectErr) {
      console.error("Error while deleting project details after user confirms overwriting of run results", deleteProjectErr)
    }
  }

  const handleRunResultNoButton = () => {
    setDeleteRunProjectModal(false)
  }

  const closeModal = useCallback(() => {
    setTechFile(false);
    setNetListFileData();
  }, [setNetListFileData, setTechFile]);

  const handleCancel = useCallback(() => {
    if (webSocketObj) {
      webSocketObj.close();
    }
    setRunLayoutJobId(null);
    setIsUserInAction1EditFromViewProject(false);
    setIsUserInAction2EditFromViewProject(false);
    setIsUserInAction3EditFromViewProject(false);
    setIsRunningJobErrored(false);
    setIsRunningJobCompleted(false);
    setRunLayoutRunningJobLogs([]);
    navigate("/home");
    setIsTechFileSelected(false);
    setSelectedTechFileName("");
    setStage1Result();
    setStage2Result();
    setNetlistCellInfo();
    setIsNetListFileSelected(false);
    setNetlistFileContent();
    setSelectedNetlistFileName();
    setSelectedNetlistFileType();
    setIsProjectSaved(false);
    setIsSelectAllChecked(false);
    setIsUserInEditMode(false);
    setIsButtonDisabledInEditMode(false);
    setSelectedGdsItems([]);
    setIsUserOnStage2Page(false);
    setIsNetlistDataChanged(false);
    setIsTechDataChanged(false);
    setShowResultButtonInTechFileInEditMode(false);
    setShowResultButtonInStage1ResultInEditMode(false);
    setStage1GraphData(null);
    setStage2GraphData(null);
    setTypeOfSelectedProject(0);
    setIsProjectStillRunning(false);
    setDefaultTechFileData();
    setIsGdsSelectAllChecked(false);
    setTechParameterValueError([]);
    setStage1RunResultSummaryData()
    setStage2RunResultSummaryData()
    setTechFileData();
    setStage1GdsLayoutImageData([]);
    setStage2GdsLayoutImageData([]);
    clearFilterResultsContext();
    setIsStage1RunResultPresent(false);
    setIsStage2RunResultPresent(false);
    setStage1TotalGDSNumber(0);
    setStage2TotalGDSNumber(0);
    setProjectTechFileListData();
    setViewProjectTechFile(false);
    setIsTechFileProjectSaved(false);
  }, [
    setIsStage1RunResultPresent,
    setIsStage2RunResultPresent,
    clearFilterResultsContext,
    setTechParameterValueError,
    setIsProjectStillRunning,
    setTypeOfSelectedProject,
    setRunLayoutJobId,
    webSocketObj,
    setIsUserInAction1EditFromViewProject,
    setIsUserInAction2EditFromViewProject,
    setIsUserInAction3EditFromViewProject,
    setStage2Result,
    setIsRunningJobErrored,
    setIsRunningJobCompleted,
    setRunLayoutRunningJobLogs,
    setIsTechFileSelected,
    setSelectedTechFileName,
    setNetlistCellInfo,
    setIsNetListFileSelected,
    setNetlistFileContent,
    setSelectedNetlistFileName,
    setSelectedNetlistFileType,
    setIsProjectSaved,
    setIsSelectAllChecked,
    setIsUserInEditMode,
    setIsButtonDisabledInEditMode,
    navigate,
    setStage1Result,
    setSelectedGdsItems,
    setIsUserOnStage2Page,
    setIsNetlistDataChanged,
    setIsTechDataChanged,
    setShowResultButtonInTechFileInEditMode,
    setShowResultButtonInStage1ResultInEditMode,
    setStage1GraphData,
    setStage2GraphData,
    setDefaultTechFileData,
    setIsGdsSelectAllChecked,
    setStage1RunResultSummaryData,
    setStage2RunResultSummaryData,
    setStage1GdsLayoutImageData,
    setStage2GdsLayoutImageData,
    setTechFileData,
    setStage2TotalGDSNumber,
    setStage1TotalGDSNumber,
    setProjectTechFileListData,
    setViewProjectTechFile,
    setIsTechFileProjectSaved
  ]);

  const previousButton = useCallback(() => {
    navigate("/dashboard/netlist-file", {
      state: { projectName, selectedFeatures ,action},
    });
  }, [projectName, navigate, selectedFeatures,action]);

  const navigateTo = useCallback(
    (path, buttonName) => {
      navigate(path, { state: { projectName, selectedFeatures } });
    },
    [navigate, projectName, selectedFeatures]
  );

  const handleTechFileSelection = useCallback(async () => {
    setTechFile(false);
    setIsTechFileSelected(true);
    const techFileDataReqBody = {
      FileName: selectedName,
      FileType: selectedType,
      projectType: typeOfSelectedProject
    };
    const techFileDataRes = await getTechFileData(techFileDataReqBody);
    if (techFileDataRes?.status === false) {
      toast.error(techFileDataRes?.message, { autoClose: 30000 });
      setIsTechFileSelected(false);
    } else {
      setTechFileData(techFileDataRes);
      setDefaultTechFileData(JSON.parse(JSON.stringify(techFileDataRes)));
      setSelectedTechFileName(`${selectedName}`);
      setSelectedTechFileType(selectedType);
      navigateTo("parameters", "parameters");
    }
  }, [
    setTechFile,
    setIsTechFileSelected,
    selectedName,
    selectedType,
    setTechFileData,
    setDefaultTechFileData,
    setSelectedTechFileName,
    setSelectedTechFileType,
    navigateTo,
    typeOfSelectedProject
  ]);

  const handleRowClick = (name, type) => {
    setSelectedName(name);
    setSelectedType(type);
  };

  // below function handles api call and data creation for saving the project in S3
  const handleSaveProject = useCallback(async () => {
    /*{
      action = 1 means only layout selected ,
      action = 2 means only hyperexpressivity selected ,
      action = 3 means both layout & hyperexpressivity selected
      }
    */
    //  request Body for save project
    if (isUserInEditMode) {
      const editProjectReqJSON = {
        ...((isNetlistDataChanged || isNetlistFileContentDataChanged) && {
          netlistMetadata: {
            fileName: selectedNetlistFileName,
            netlistType: selectedNetlistFileType?.toUpperCase(),
            cellSelections: netlistCellInfo,
          },
          netlistFileContents: btoa(netlistFileContent),
        }),
        ...(isTechDataChanged && {
          techMetadata: {
            fileName: selectedTechFileName,
            techType: selectedTechFileType?.toUpperCase(),
          },
          techFileContents: techFileData?.data?.FileContent,
        })
      };

      if (Object.keys(editProjectReqJSON)?.length) {
        try {
          const { status, message } = await editProjectData(currentProjectId, editProjectReqJSON) || {};

          if (status) {
            setIsSuccess(true);
            setIsNetlistDataChanged(false);
            setIsTechDataChanged(false);
            toast.success(`${message} ${isDebugModeOn ? currentProjectId : ""}` || "Project saved successfully.", { autoClose: 10000 });
          } else {
            console.error(message);
            toast.error(message || "Failed to save the project.", { autoClose: false });
          }
        } catch (error) {
          // Handle any errors that occur during the API call or elsewhere
          console.error("Error during project update:", error);
          toast.error("An error occurred while saving the project. Please try again.", { autoClose: 10000 });
        }
      } else {
        setIsSuccess(true);
        toast.success(`Project already up-to-date. ${isDebugModeOn ? currentProjectId : ""} `, { autoClose: 10000 });
      }
    }
    else {
      const saveProjectReqJSON = {
        projectName: projectName,
        action: actionSelected,
        netlistMetadata: {
          fileName: selectedNetlistFileName,
          netlistType: selectedNetlistFileType?.toUpperCase(),
          cellSelections: netlistCellInfo,
        },
        techMetadata: {
          fileName: selectedTechFileName,
          techType: selectedTechFileType?.toUpperCase(),
        },
        netlistFileContents: btoa(netlistFileContent),
        techFileContents: techFileData?.data?.FileContent,
        projectType: typeOfSelectedProject
      };
      const saveProjectRes = await saveProjectInS3(saveProjectReqJSON);
      if (saveProjectRes.status === false) {
        // using react-tostify for handling toaster messages in application
        console.error(saveProjectRes?.message)
        toast.error(saveProjectRes?.message, { autoClose: 30000 });
      } else {
        setIsNetlistFileContentDataChanged(false)
        setIsProjectSaved(true);
        setIsSuccess(true);
        setCurrentProjectId(saveProjectRes?.data?.projectId);
        toast.success(`${saveProjectRes?.message} ${isDebugModeOn ? saveProjectRes?.data?.projectId : ""}`, { autoClose: 10000 });
        setIsNetlistDataChanged(false);
        setIsTechDataChanged(false);
        setIsUserInEditMode(true); // setting user in edit mode only when the project is saved successfully.
        setIsButtonDisabledInEditMode(true);
        setViewProjectTechFile(true);
        setIsTechFileProjectSaved(true)
      }
    }
  }, [
    typeOfSelectedProject,
    isNetlistFileContentDataChanged,
    projectName,
    actionSelected,
    selectedNetlistFileName,
    selectedNetlistFileType,
    netlistCellInfo,
    selectedTechFileName,
    selectedTechFileType,
    netlistFileContent,
    techFileData,
    setIsProjectSaved,
    setIsSuccess,
    currentProjectId,
    isUserInEditMode,
    setCurrentProjectId,
    setIsUserInEditMode,
    setIsButtonDisabledInEditMode,
    isNetlistDataChanged,
    isTechDataChanged,
    setIsNetlistDataChanged,
    setIsTechDataChanged,
    setIsNetlistFileContentDataChanged,
    setViewProjectTechFile,
    setIsTechFileProjectSaved
  ]);

  //run project button click handle
  const handleRunProject = useCallback(async () => {
    setUserConfirmationModal(true);
  }, [setUserConfirmationModal]);

  //below fuction handle the selection of tech file from the local
  const handleLoadTechFileChange = (event) => {
    const file = event?.target?.files[0];
    setSelectedTechFileFromLocal(file)
  }

  // below function open the upload project modal
  const handleUploadProjectTechfile = async () => {
    setUploadProjectTechFileModal(true);
  }

  //below function handle the cancel on the upload tech file modal
  const handleCancelUploadTechFile = () => {
    setUploadProjectTechFileModal(false)
    setSelectedTechFileFromLocal(false);
  }

  // below function upload the project techfile
  const handleUploadOnProjectTechfile = async (event) => {
    event.preventDefault();
    const formData = new FormData();
    formData.append("upload", selectedTechFileFromLocal);
    try {
      const uploadProjectTechFileRes = await uploadProjectTechFile(formData);
      if (uploadProjectTechFileRes?.status_code === 200) {
        setTechFileData(uploadProjectTechFileRes)
        setDefaultTechFileData(JSON.parse(JSON.stringify(uploadProjectTechFileRes)));
        setUploadProjectTechFileModal(false);
        setTechFile(false);
        setIsTechFileSelected(true);
        setSelectedTechFileType(userFile)
        setSelectedTechFileName(selectedTechFileFromLocal?.name)
        toast.success(uploadProjectTechFileRes?.message, { autoClose: 10000 });
      }
      else {
        toast.error(uploadProjectTechFileRes?.message);
        setSelectedTechFileFromLocal();
        setIsTechFileSelected(false);
        if(techFileData?.data?.FileContent){
          setIsTechFileSelected(true);
        }
      }
    }
    catch (error) {
      console.error("Error while uploading the project tech file", error)
    }
  }

  const uploadTechFileModalContent = {
    title: "Choose a File",
    body: (
      <UploadProjectTechFileModalBody handleLoadTechFileChange={handleLoadTechFileChange} handleUploadOnProjectTechfile={handleUploadOnProjectTechfile} />
    ),
    footer: (
      <>
        <div className="d-flex justify-content-center gap-2">
          <div className="w-25">
            <Button
              disabled={!selectedTechFileFromLocal}
              id="admin-upload-Tech-file-button"
              data-tooltip-id="upload-Tech-file-button-tooltip"
              data-tooltip-content={!selectedTechFileFromLocal && "Choose Tech File to upload"}
              type="submit"
              form="upload-tech-file-form"
              className={`w-100 ${!selectedTechFileFromLocal ? "app-secondary-button-color border-0 cursor_not_allowed" : "app-primary-button-color border-0"}`}
            >
              OK
            </Button>
            {!selectedTechFileFromLocal && <ReactTooltip id="upload-tech-file-button-tooltip" place="top" style={{ width: "200px", zIndex: 9999 }} />}
          </div>
          <div className="w-25">
            <Button
              id="admin-upload-cancel-tech-file-button"
              className="w-100 app-secondary-button-color border-0"
              onClick={handleCancelUploadTechFile}
            >
              Cancel
            </Button>
          </div>
        </div>
      </>
    )
  }


  // passing the data to the modal as props
  const confirmationModalContent = {
    title: "Please Confirm:",
    body: (
      <h6>
        You have selected {selectedCellInfoConfirmation} cell and{" "}
        {selectedPermutationConfirmation} variations for layout generation.
      </h6>
    ),
    footer: (
      <>
        <Button
          id="user-confirmation-yes-button"
          className="w-25 app-primary-button-color border-0"
          onClick={userConfirmationYesButton}
        >
          Yes
        </Button>
        <Button
          id="user-confirmation-no-button"
          className="w-25 app-secondary-button-color border-0"
          onClick={userConfirmationNoButton}
        >
          No
        </Button>
      </>
    ),
  };

  const runResultConfirmationModalContent = {
    title: "Message",
    body: runModalMessage,
    footer: (<>
      <Button id="user-run-result-confirmation-yes-button" onClick={handleRunResultYesButton} className="w-25 app-primary-button-color border-0">Yes</Button>
      <Button id="user-run-result-confirmation-no-button" onClick={handleRunResultNoButton} className="w-25 app-secondary-button-color border-0">No</Button>
    </>)
  };

  // const fetchStage1ResultsData = useCallback(async () => {
  //   const stage1Res = await fetchStageData(currentProjectId, 1, 0,filterRequestParameter?filterRequestParameter:null);
  //   if (stage1Res?.status === true) {
  //     setStage1Result(stage1Res)
  //     setShowResultButtonInTechFileInEditMode(true);
  //   }
  //   else {
  //     setShowResultButtonInTechFileInEditMode(false);
  //   }
  // }, [currentProjectId, setStage1Result, setShowResultButtonInTechFileInEditMode,filterRequestParameter]);

  //commenting out since logic for showing exisiting result button is changed
  // // handling showing of showexisiting result  button for action3 in edit mode
  // useEffect(() => {
  //   // scenario that it comes only for action3 from view edit mode
  //   if ((isUserInAction3EditFromViewProject || isUserInAction1EditFromViewProject)) {
  //     // after this check we make sure to chaeck if user is in edit mode
  //     if (isUserInEditMode) {
  //       setDoesStage1ResultExisit(true);
  //       fetchStage1ResultsData()
  //     }
  //   }
  // }, [actionSelected, fetchStage1ResultsData, isUserInAction3EditFromViewProject, isUserInAction1EditFromViewProject, isUserInEditMode]);

  
    useEffect(() => {
      if(isUserInEditMode){
      // useeffect checks if exisiting reuslts are there or not there if there then it will set which will show exisiting results button
      const runResultReqBodyStage1 = {
        "projectId": currentProjectId,
        "stage": 1
      };
      const runResultReqBodyStage2 = {
        "projectId": currentProjectId,
        "stage": 2
      }
      if (action === 1) {
        (async () => {
          const resultResStage1 = await getRunResultsStatus(runResultReqBodyStage1);
          setIsStage1RunResultPresent(resultResStage1);
         
        })();
      } else if (action === 2) {
        (async () => {
          const resultResStage2 = await getRunResultsStatus(runResultReqBodyStage2);
          setIsStage2RunResultPresent(resultResStage2);
          
        })();
      } else if (action === 3) {
        (async () => {
          const resultResStage1 = await getRunResultsStatus(runResultReqBodyStage1);
          const resultResStage2 = await getRunResultsStatus(runResultReqBodyStage2);
          setIsStage1RunResultPresent(resultResStage1);
          setIsStage2RunResultPresent(resultResStage2);
        })();
      }
    }
    },[isUserInEditMode, action, currentProjectId,setIsStage1RunResultPresent,setIsStage2RunResultPresent]);

     useEffect(()=>{
        //below useEffect handles fetching of stageResult based on if stage result present button on of off 
        if(isStage1RunResultPresent){
        const fetchStage1ResultsData = async () => {
            const stage1Res = await fetchStageData(currentProjectId, 1, 0,filterRequestParameter?filterRequestParameter:null);
            if (stage1Res?.status === true) {
              if(!stage1GraphSelectedGdsCells || stage1GraphSelectedGdsCells === null){
              setStage1Result(stage1Res);
              }
              setShowResultButtonInTechFileInEditMode(true);// setting this to show this button only in case of edit mode
            }else{
              setShowResultButtonInTechFileInEditMode(true);// setting this to show this button only in case of edit mode
            }
          };
          fetchStage1ResultsData();
        } 
        if(isStage2RunResultPresent){
          const fetchStage2ResultsData = async () => {
            const stage2Res = await fetchStageData(currentProjectId, 2, 0,filterRequestParameter?filterRequestParameter:null);
            if (stage2Res?.status === true) {
              if(!stage2GraphSelectedGdsCells || stage2GraphSelectedGdsCells === null){
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
      },[isStage1RunResultPresent,isStage2RunResultPresent,currentProjectId,setStage1Result])

  // the below function is called when the stage1Result are present
  useEffect(() => {
    if (stage1Result && stage1Result?.data) {
      setShowResultButtonInTechFileInEditMode(true);
      setDoesStage1ResultExisit(true);
    }
  }, [stage1Result, setShowResultButtonInTechFileInEditMode, setDoesStage1ResultExisit])

  // the below function reset the updated tech file data to default tech file data. 
  const handleResetTechFileData = useCallback(() => {
    if (defaultTechFileData) {
      setTechFileData(JSON.parse(JSON.stringify(defaultTechFileData)));
    }

    toast.success("Reset TechFile Data Successful", { autoClose: 10000 })
    setTechParameterValueError([]);
  }, [setTechFileData, defaultTechFileData, setTechParameterValueError]);

  //below functions removes all variations selected 
  const handleResetVariation = useCallback(() => {
    const updatedTechDataWithNoVariations = { ...techFileData }; // Copying the current techData from context
    updatedTechDataWithNoVariations?.data?.FileContent?.forEach((parameter) => {
      if (parameter?.name === 'permutation') {
        //removing it from variations permutations object to not include it under variations
        parameter.data = [];
        return;
      }else{
        //also updating selected check to unselected to uncheck checkbox from parameter tab
        parameter.data = parameter?.data?.map((parameterItem)=>{
          if(parameterItem?.isSelected){
            //if selected flag is true turning it to off
            return {...parameterItem,isSelected: false}
          }
            //if it is unchecked returning as it is 
            return parameterItem;
          
        })
      }

    });
    setTechFileData(updatedTechDataWithNoVariations);
    setTechParameterValueError([]);// removing errors as well as variations is getting deleted
    toast.success("Variations removed successfully.", { autoClose: 10000 })// adding toaster to indicate user data removed successfully
  }, [techFileData, setTechFileData,setTechParameterValueError])

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

  // below function get the list of project techfiles
  const handleViewProjectTechFile = useCallback(async () => {
    try {
      const getProjectTechFileListRes = await getProjectTechFileList(currentProjectId);
      if (getProjectTechFileListRes?.status_code === 200) {
        setProjectTechFileListData(getProjectTechFileListRes?.data);
        setViewProjectTechFileModal(true);
      }
      else {
        setProjectTechFileListData(getProjectTechFileListRes);
        setViewProjectTechFileModal(true);
      }
    } catch (error) {
      console.error("Failed to fetch project tech file list:", error);
    }
  }, [currentProjectId, setProjectTechFileListData])

  // below function handles save tech file
  const handleSaveTechFile = useCallback(() => {
    setSaveTechFileModal(true);
    setTechFileAction("save");
    const fileName = selectedTechFileName.split('.').slice(0, -1).join('.');
    setNewTechFileName(fileName)
    setIsTechFileSaved(true);
  },[selectedTechFileName])

  //handling the sidebar content 
  useEffect(() => {
    setSidebarContent({
      upper: (
        <div>
          <div className="mb-2">
            <h6>Project Name:</h6>
            <span
              id="sidebar-project-name"
              className="text-muted text-break text-dark py-2"
            > {projectName} </span>
          </div>
          <div className="mb-2">
            <h6 className="mb-2">Select PDK/Tech File:</h6>
            {selectedTechFileName ? (
              <span
                id="techfile-selected-filename"
                className="text-dark py-2 text-break"
              >
                {selectedTechFileName}
              </span>
            ) : (
              <span className="text-muted" id="techfile-selected-filename">No file selected</span>
            )}
          </div>
        </div>
      ),
      lower: (
        <div className="col-12">
          <div className="row">
            <div className="btn-group" role="group" aria-label="First group">
                {/* {(((doesStage1ResultExisit) || (stage1Result && stage1Result.data && Array.isArray(stage1Result.data.Items))) && showResultButtonInTechFileInEditMode) && ( */}
                {((action === 1 || action === 3) && showResultButtonInTechFileInEditMode && isStage1RunResultPresent) && (
                <Button
                  id="show-layout-existing-result"
                  onClick={handleExistingResult}
                  className="app-primary-button-color border-0 my-1 w-100"                >
                  Show LayoutGeneration Result
                </Button>
              )}
            </div>
            <div className="btn-group" role="group" aria-label="First group">
                {/* {(((doesStage1ResultExisit) || (stage1Result && stage1Result.data && Array.isArray(stage1Result.data.Items))) && showResultButtonInTechFileInEditMode) && ( */}
                {( action === 3 && showResultButtonInStage1ResultInEditMode &&  isStage2RunResultPresent) && (
                <Button
                  id="show-hyperExpressivity-existing-result"
                  onClick={handleShowExisitingHyperResult}
                  className="app-primary-button-color border-0 my-1 w-100"                >
                   Show HyperExpressivity Result
                </Button>
              )}
            </div>
            <div className="btn-group" role="group" aria-label="First group">
              {isTechFileProjectSaved && (
                <Button
                  id="save-project-techfile"
                  disabled={techParameterValueError?.length > 0}
                  onClick={handleSaveTechFile}
                  className={techParameterValueError?.length > 0 ?"app-secondary-button-color border-0 cursor_not_allowed":"app-primary-button-color border-0 my-1 w-100"}                
                  data-tooltip-id="toolTip-savetechfile-button"
                  data-tooltip-content={techParameterValueError?.length > 0 && "Handle error/s on parameter value/s under variation tab to save project"}
                  data-tooltip-place="top"
                >
                  Save TechFile
                </Button>  
              )}
              {techParameterValueError?.length > 0 && (<ReactTooltip id="toolTip-savetechfile-button" style={{ width: "170px", zIndex: 9999 }} />)}
            </div>
            <div className="btn-group" role="group" aria-label="First group">
              {(isUserInEditMode && isButtonDisabledInEditMode) ||
                (!isUserInEditMode && !isButtonDisabledInEditMode) ? (
                <div className="w-100">
                  <Button
                    data-tooltip-id="select-techfile-button-tooltip"
                    data-tooltip-content={isButtonDisabledInEditMode && "You cannot change techfile after saving project once."}
                    id="netlist-select-button"
                    onClick={handleClick}
                    disabled={isButtonDisabledInEditMode}
                    className={`my-1 w-100 ${isButtonDisabledInEditMode ? "app-secondary-button-color border-0 cursor_not_allowed" : "app-primary-button-color border-0"}`}
                  >
                    Select Techfile
                  </Button>
                  {isButtonDisabledInEditMode && <ReactTooltip id="select-techfile-button-tooltip" place="top" style={{ width: "260px", zIndex: 9999 }} />}
                </div>
              ) : null}
            </div>
            <div className="btn-group" role="group" aria-label="First group">

             
              <Button
                id="run-button"
                onClick={handleRunProject}
                className={`my-1 w-50 ${techParameterValueError?.length > 0 ?"app-secondary-button-color border-0 cursor_not_allowed":isProjectSaved || isUserInEditMode ? "app-primary-button-color border-0" : "app-secondary-button-color border-0 cursor_not_allowed"
                }`}
                disabled={techParameterValueError?.length > 0 || (!isProjectSaved && !isUserInEditMode)}
                data-tooltip-id="toolTip-techFile-runButton"
                data-tooltip-content={techParameterValueError?.length > 0 ? "Handle error/s on parameter value/s to save project" : "Please save project first before running"}
                data-tooltip-place="top"
              >
                Run LayoutGeneration
              </Button>
              {(techParameterValueError?.length > 0 || (!isProjectSaved && !isUserInEditMode)) && (<ReactTooltip id="toolTip-techFile-runButton" style={{ width: "200px", zIndex: 9999 }} />)}
            
            </div>
            <div className="btn-group" role="group" aria-label="First group">

              <Button
                id="previous-button"
                onClick={previousButton}
                className="ms-0 mx-2 my-1 w-50 app-primary-button-color border-0"              >
                Previous
              </Button>
              <Button
                id="save-button"
                onClick={handleSaveProject}
                className={`ms-0 my-1 w-50 ${ techParameterValueError?.length > 0 ?"app-secondary-button-color border-0 cursor_not_allowed":isTechFileSelected || isUserInEditMode ? "app-primary-button-color border-0" :"app-secondary-button-color border-0 cursor_not_allowed"} }`}                
                disabled={!isTechFileSelected && !isUserInEditMode ? true : techParameterValueError?.length > 0 ? true: false}
                data-tooltip-id="toolTip-techFile-saveButton"
                data-tooltip-content={techParameterValueError?.length > 0 ? "Handle error/s on parameter value/s on variation tab to save project" : "Select techfile to save project"}
                data-tooltip-place="top"
              >
                Save
              </Button>
                {(techParameterValueError?.length > 0 || (!isTechFileSelected && !isUserInEditMode)) && (<ReactTooltip id="toolTip-techFile-saveButton" style={{ width: "170px", zIndex: 9999 }} />)}
            </div>
            <div className="btn-group" role="group" aria-label="First group">
              <Button
                id="cancel-button"
                onClick={handleCancel}
                className="my-1 w-50 app-secondary-button-color border-0"
              >
                Close
              </Button>
            </div>
          </div>
        </div>
      ),
    });
  }, [
    showResultButtonInStage1ResultInEditMode,
    action,
    handleShowExisitingHyperResult,
    isStage2RunResultPresent,
    isStage1RunResultPresent,
    techParameterValueError,
    isUserInAction3EditFromViewProject,
    isUserInAction1EditFromViewProject,
    doesStage1ResultExisit,
    setSidebarContent,
    selectedTechFileName,
    isProjectSaved,
    techFile,
    isTechFileSelected,
    handleCancel,
    previousButton,
    handleSaveProject,
    handleRunProject,
    isUserInEditMode,
    handleExistingResult,
    stage1Result,
    isButtonDisabledInEditMode,
    showResultButtonInTechFileInEditMode,
    projectName,
    viewProjectTechFile,
    handleViewProjectTechFile,
    isTechFileProjectSaved,
    handleSaveTechFile
  ]);

  //below function download the project tech file from the list
  const handleDownloadProjectTechFile = useCallback(async (techFileId, projectId, fileName) => {
    const downloadProjectTechFileReq = {
      id: techFileId ? techFileId : selectedProjectTechFileIdFromList,
      file_name:fileName ? fileName  : selectedProjectTechFileNameFromList,
      project_id: projectId ? projectId : selectedProjectTechFileProjectIdFromTheList
    };
    setLoading(true);
    try {
      const downloadProjectTechFileRes = await downloadProjectTechFile(downloadProjectTechFileReq);
      if (downloadProjectTechFileRes?.status === 200) {
        const blob = new Blob([downloadProjectTechFileRes.data]);
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
  
          // Extract filename from headers or set a default
          const contentDisposition = downloadProjectTechFileRes?.headers["x-filename"];
          let fileName = 'download.tech'; // Default filename

          if (contentDisposition) {
            const fileNameMatch = contentDisposition.match(/filename="(.+)"/);
            if (fileNameMatch && fileNameMatch[1]) {
              fileName = fileNameMatch[1];
            } else {
              fileName = contentDisposition;
            }
          }
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
  
        setViewProjectTechFileModal(false);
        setSelectedProjectTechFileIdFromList();
        toast.success("Tech File downloaded successfully", { autoClose: 10000 });
      } 
    } catch (error) {
      console.error("Error while downloading the project tech file", error);
    } finally{
      setLoading(false);
    }
  }, [
    selectedProjectTechFileIdFromList,
    selectedProjectTechFileNameFromList,
    selectedProjectTechFileProjectIdFromTheList
  ]);
  
  const handleProjectTechFileCancel= () =>{
    setViewProjectTechFileModal(false);
    setSelectedProjectTechFileIdFromList();
  }

  //below function loads the project tech fie from the list 
  const handleLoadProjectTechFile = useCallback(async () => {
    const projectTechFileReq = {
      "techId": selectedProjectTechFileIdFromList
    }
    try {
      const getProjectTechFileDataRes = await getProjectTechFileData(projectTechFileReq);
      if (getProjectTechFileDataRes?.status_code === 200) {
        setIsTechDataChanged(true);//setting this to true to make sure newly selected techfile is reflected when saved is hit
        setTechFileData(getProjectTechFileDataRes)
        setDefaultTechFileData(JSON.parse(JSON.stringify(getProjectTechFileDataRes)));
        setIsTechFileSelected(true);
        setViewProjectTechFileModal(false);
        setSelectedProjectTechFileIdFromList();
        setSelectedTechFileName(selectedProjectTechFileNameFromList);
      }
    }
    catch (error) {
      console.error("Error while loading tech file data")
    }
  }, [setIsTechDataChanged,setDefaultTechFileData, setTechFileData, setIsTechFileSelected, selectedProjectTechFileIdFromList, setSelectedTechFileName, selectedProjectTechFileNameFromList])

  // below function handles rename tech file.
  const handleRenameTechFile = useCallback((file_name) => {
    if(file_name === selectedTechFileName){
      setSaveTechFileName(true);
    }
    setSaveTechFileModal(true);
    setTechFileAction("rename")
    const fileName = file_name.split('.').slice(0, -1).join('.');
    setNewTechFileName(fileName);
  },[selectedTechFileName])

  // the below function is used to rename the tech file
  const handleSaveRenameTechFile = async () => {
    const renameTechFileReq = {
      techId: selectedProjectTechFileIdFromList,
      projectId: currentProjectId,
      newName: newTechFileName,
    };

    const saveTechFileInCatalogTechFile = {
      projectId: currentProjectId,
      techData: {
        FileContent: techFileData?.data?.FileContent ,
      },
      file_name: newTechFileName,
    };

    try {
      if (techFileAction === "rename") {
        const renameTechFileRes = await renameTechFile(renameTechFileReq);
        if (renameTechFileRes?.status_code === 200) {
         
          setIsTechDataChanged(true);// setting this as true to make sure saving endpt is called to updated renamed techfile name
          setSaveTechFileModal(false);
          setViewProjectTechFileModal(false);
          if(saveTechFileName) {
          const techFileName = newTechFileName.concat(".tech");
          setSelectedTechFileName(techFileName);
          }
          setNewTechFileName();
          setSelectedProjectTechFileIdFromList();
          setConfirmTechFileRenameModal(false);
          setSaveTechFileName(false);
          setRenameTechFileErrorMessage();
          setIsTechFileSaved(false);
          toast.success(renameTechFileRes?.message, { autoClose: 10000 })
        }
        else if(renameTechFileRes?.status_code === 400){
          setRenameTechFileErrorMessage(renameTechFileRes);
          setConfirmTechFileRenameModal(false);
          if(isTechFileSaved){
           setTechFileAction("save")
          }
        }
      } else if (techFileAction === "save") {
        const saveTechFileRes = await saveTechFile(saveTechFileInCatalogTechFile);
        if (saveTechFileRes?.status_code === 200) {
          setSaveTechFileModal(false);
          setNewTechFileName();
          setSelectedProjectTechFileIdFromList();
          const techFileName = newTechFileName.concat(".tech");
          setSelectedTechFileName(techFileName);
          setRenameTechFileErrorMessage();
          toast.success(saveTechFileRes?.message, { autoClose: 10000 })          
        }
        if (saveTechFileRes?.status_code === 208) {
          setConfirmTechFileRenameModal(true)
          setTechFileAction("rename")
          setSaveTechFileName(true);
          setConfirmTechFileRenameMessage(saveTechFileRes?.message);
          setSelectedProjectTechFileIdFromList(saveTechFileRes?.data?.techId)
        }
        else{
          setRenameTechFileErrorMessage(saveTechFileRes)
        }
      }
    } catch (error) {
      console.error(`Error while handling tech file (${techFileAction})`, error);
    }
  };

  // handle save tech file modal Cancel 
  const handleCancelSaveTechFile = () => {
    setSaveTechFileModal(false);
    setRenameTechFileErrorMessage();
    }

  // below function cancel the techfile
  const handleCancelRenameTechFile = () =>{
    setConfirmTechFileRenameModal(false);
    setSaveTechFileName(false);
    setTechFileAction("save");
  }

  // Modal content for already running project
  const projectRunningModalContent = {
    title: "Project Status",
    body: <h6>{projectRunningMessage}</h6>,
    footer: (
      <Button
        id="project-running-ok-button"
        className="w-25 app-primary-button-color border-0"
        onClick={() => setIsProjectRunningModal(false)}
      >
        OK
      </Button>
    ),
  };

  // below use effect handle the project techfile modal
  useEffect(() => {
    if (viewProjectTechFileModal && projectTechFileListData) {
      setProjectTechFileList({
        title: "Select Project Techfile",
        body: <ProjectTechFileListModalBody projectTechFileListData={projectTechFileListData} setSelectedProjectTechFileId={setSelectedProjectTechFileIdFromList} setSelectedProjectTechFileNameFromList={setSelectedProjectTechFileNameFromList} setSelectedProjectTechFileProjectIdFromList={setSelectedProjectTechFileProjectIdFromList} handleRenameTechFile={handleRenameTechFile} handleDownloadProjectTechFile={handleDownloadProjectTechFile} loading={loading} />,
        footer: (<>
          {/* To do: Commenting as per the duscussion will enable when multiple download is supported from backend */}
          {/* <Button className={`w-25 ${selectedProjectTechFileIdFromList ? "app-primary-button-color" : "app-secondary-button-color"} border-0`} disabled={!selectedProjectTechFileIdFromList} id="project-techfile-download" onClick={() => handleDownloadProjectTechFile()}>Download</Button> */}
          <Button className={`w-25 ${selectedProjectTechFileIdFromList ? "app-primary-button-color" : "app-secondary-button-color"} border-0`} disabled={!selectedProjectTechFileIdFromList} id="load-project-techfile" onClick={handleLoadProjectTechFile}>Load TechFile</Button>
          <Button className="w-25 app-secondary-button-color border-0" id="project-techfile-cancel" onClick={handleProjectTechFileCancel}>Cancel</Button>
        </>
        )
      })
    }
  }, [viewProjectTechFileModal, projectTechFileListData, selectedProjectTechFileIdFromList, handleLoadProjectTechFile, handleDownloadProjectTechFile, loading, handleRenameTechFile])

  // modal content for save tech file
  const saveTechFileModalContent = {
    title: "Enter New Tech File Name:",
    body: (
      <>
        <SaveTechFieModalBody setNewTechFileName={setNewTechFileName} newTechFileName={newTechFileName} renameTechFileErrorMessage={renameTechFileErrorMessage} />
      </>
    ),
    footer: (
      <>
        <Button className={`w-25 ${newTechFileName ? "app-primary-button-color" : "app-secondary-button-color cursor_not_allowed"}  border-0`} disabled={!newTechFileName} id="save-techfile" onClick={handleSaveRenameTechFile}>Save</Button>
        <Button className="w-25 app-secondary-button-color border-0" id="cancel-techfile" onClick={handleCancelSaveTechFile}>Cancel</Button>
      </>
    )
  }

  // modal content to confirm rename techfile.
  const confirmRenameTechFileModalContent = {
    title: "Please Confirm:",
    body: (
      <h6
        className="w-100 text-break" style={{ wordBreak: 'break-word', maxHeight: '200px' }}>
          {confirmTechFileRenameMessage}
      </h6>
    ),
    footer: (
      <>
        <Button className="w-25 app-primary-button-color border-0" id="confirm-rename-techfile" onClick={handleSaveRenameTechFile}>Yes</Button>
        <Button className="w-25 app-secondary-button-color border-0" id="confirm-cancel-rename-techfile" onClick={handleCancelRenameTechFile} >No</Button>
      </>
    )
  }

  //useeffect for handling clear variations button
  useEffect(()=>{
   const variationsExisit =  techFileData?.data?.FileContent?.some((techParam)=> techParam?.name === 'permutation' && techParam?.data && techParam?.data?.length >0)
   setDoesVariationsExisit(variationsExisit);
  },[techFileData]);

  return (
    <>
      <ToastContainer
        closeButton={true}
        position="top-center"
        autoClose={isSuccess ? true : false}
        theme="colored"
      />
      <div
        className="container-fluid d-flex flex-column h-100 p-0 m-0"
        style={{ maxHeight: "100%", overflow: "hidden" }}
      >
        <div className="row flex-grow-1 m-0 p-0" style={{ overflow: "hidden" }}>
          {techFile && (
            <Modal
              id="select-techfile-modal"
              show={techFile}
              onHide={closeModal}
              centered
              size="lg"
              animation={false}
              className="modal-style modal-fade-in-bottom"
            >
              <Modal.Header closeButton>
                <Modal.Title>Select Techfile</Modal.Title>
              </Modal.Header>
              <Modal.Body className="p-3 pt-0 overflow-y-auto overflow-x-hidden">
                <div className="row">
                  <ul className="list-group">
                    <li
                      className="list-group-item border rounded mb-2 bg-light sticky-top me-0 pe-3"
                      style={{ zIndex: 1 }}
                      id={selectedTechFileName}
                    >
                      <div className="d-flex justify-content-between ">
                        <div className="">
                          <label className="form-check-label fw-bold">
                            File Name
                          </label>
                        </div>
                        <div className="">
                          <label className="form-check-label fw-bold ">
                            File Type
                          </label>
                        </div>
                      </div>
                    </li>
                    {techlistData && techlistData.length > 0 ? (
                      techlistData.map((data) => (
                        <li
                          key={data.FileName}
                          className={`list-group-item d-flex justify-content-between align-items-center py-2 border rounded mb-2 ${selectedName === data.FileName && selectedType === data?.FileType
                            ? "app-primary-button-color border-0 text-white"
                            : "bg-light"
                            }`}
                          onClick={() =>
                            handleRowClick(data.FileName, data.FileType)
                          }
                          style={{ cursor: "pointer" }}
                        >
                          <div className="w-75 text-start text-truncate">
                            {data.FileName}
                          </div>
                          <div>{data.FileType}</div>
                        </li>
                      ))
                    ) : (
                      <li className="list-group-item text-center text-muted">
                        No Techfiles available
                      </li>
                    )}
                  </ul>
                </div>
              </Modal.Body>
              <Modal.Footer className="d-flex justify-content-center gap-2">
                <Button
                  id="upload-tech-file"
                  className=" col-3 m-2 app-primary-button-color border-0"
                  onClick={handleUploadProjectTechfile}
                >
                  Upload Tech File
                </Button>
                <Button
                  id="ok-button"
                  onClick={handleTechFileSelection}
                  className={`col-3 m-2 border-0 ${selectedName || selectedType ? "app-primary-button-color border-0" : "app-secondary-button-color border-0 cursor_not_allowed"}`}
                  disabled={!selectedName || !selectedType}
                  data-tooltip-id="toolTip-techFile-OkButton"
                  data-tooltip-content="Select atleast one techfile to proceed ahead."
                  data-tooltip-place="top"

                >
                  Ok
                </Button>
                {(!selectedName || !selectedType) && (<ReactTooltip id="toolTip-techFile-OkButton" style={{ zIndex: 9999 }} />)}
                <Button
                  id="cancel-button"
                  onClick={closeModal}
                  className="col-3 m-2 app-secondary-button-color border-0"
                >
                  Cancel
                </Button>
              </Modal.Footer>
            </Modal>
          )}
          <div className={`col-12 m-0 p-0 h-100 ${!techFileData && "d-flex justify-content-center align-items-center"} `}>
            <div className={`d-flex ${(!techFileData) && "justify-content-center"} flex-column app-secondary-color h-100 `}>
              <div
                className={`col-12 row m-0 ${!techFileData ? "overflow-hidden" : "overflow-y-auto"}`}
                style={{ maxHeight: "100%" }}
              >
                {isTechFileSelected || isUserInEditMode ? (
                  <>
                    {selectedTechFileName && selectedTechFileName.length > 0 ? (
                      <>
                        <div className="col-12 pb-4 pt-1">
                          <ul
                            className="nav nav-tabs justify-content-center border-0 gap-1"
                            id="myTab"
                            role="tablist"
                          >
                            <li className="nav-item ms-auto tabs-border">
                              <a
                                className="nav-link tabs-btn active fw-bold text-uppercase border px-4 py-2"
                                id="active-tab"
                                data-bs-toggle="tab"
                                href="#active"
                                role="tab"
                                aria-controls="active"
                                aria-selected="true"
                              >
                                Parameters
                              </a>
                            </li>
                            <li className="nav-item tabs-border">
                              <a
                                className="nav-link tabs-btn fw-bold text-uppercase border px-4 py-2 "
                                id="link1-tab"
                                data-bs-toggle="tab"
                                href="#link1"
                                role="tab"
                                aria-controls="link1"
                                aria-selected="false"
                              >
                                Variations
                              </a>
                            </li>
                            <div className="nav-item ms-auto d-flex align-items-center">
                            {viewProjectTechFile && (
                                <>
                                  <button
                                    className="border-0 bg-transparent active tabs-btn"
                                    onClick={handleViewProjectTechFile}
                                    id="view-project-techfile-button"
                                    data-tooltip-id="techfile-project-button-tooltip"
                                    data-tooltip-content="Select Project TechFile"
                                    data-tooltip-place="top"
                                  >
                                    <FontAwesomeIcon icon={faFileLines} style={{ fontSize: '20px', cursor: "pointer" }} />
                                  </button>
                                  <ReactTooltip id="techfile-project-button-tooltip" style={{ width: "180px", zIndex: 9999 }} />
                                </>
                              )}
                              {doesVariationsExisit && (
                                <>
                                  <button
                                    className="border-0 bg-transparent active tabs-btn"
                                    onClick={handleResetVariation}
                                    id="clear-variations-techfile-button"
                                    data-tooltip-id="toolTip-techFile-clear-variation-button"
                                    data-tooltip-content="Clear all variations selected for layout generation."
                                    data-tooltip-place="top"
                                  >
                                    <FontAwesomeIcon icon={faTrash} style={{ fontSize: '20ypx', cursor: "pointer" }} />
                                  </button>
                                  <ReactTooltip id="toolTip-techFile-clear-variation-button" style={{ width: "170px", zIndex: 9999 }} />
                                </>
                              )}
                              <button
                                className="border-0 bg-transparent active tabs-btn"
                                onClick={handleResetTechFileData}
                                id="reset-techfile-button"
                                data-tooltip-id="toolTip-techFile-reset-button"
                                data-tooltip-content="Reset Techfile Data"
                                data-tooltip-place="top"
                              >
                                <FontAwesomeIcon icon={faRotate} style={{ fontSize: '20ypx', cursor: "pointer"}} />
                              </button>
                              <ReactTooltip id="toolTip-techFile-reset-button" style={{ width: "170px", zIndex: 9999 }} />
                            </div>
                          </ul>
                          <div className="tab-content" id="myTabContent">
                            <div
                              className="tab-pane fade show active"
                              id="active"
                              role="tabpanel"
                              aria-labelledby="active-tab"
                            >
                              <div className="p-4 bg-white border rounded shadow-sm">
                                <Parameters />
                              </div>
                            </div>
                            <div
                              className="tab-pane fade"
                              id="link1"
                              role="tabpanel"
                              aria-labelledby="link1-tab"
                            >
                              <div className="p-4 bg-white border rounded shadow-sm">
                                <Variations />
                              </div>
                            </div>
                          </div>
                        </div>
                      </>
                    ) : (
                      <div className="spinner-border overflow-hidden" role="status">
                        <span className="sr-only overflow-hidden">Loading...</span>
                      </div>
                    )}
                    {loading && (
                    <div className="position-fixed top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center " style={{ zIndex: 99999 }}>                    
                      <div className="spinner-border overflow-hidden" role="status">
                        <span className="sr-only overflow-hidden">Loading...</span>
                      </div>
                    </div>
                    )}
                  </>
                ) : (
                  <div className="col-12 bg-light-brown-v1 d-flex flex-column justify-content-center align-items-center p-4">
                    <Empty />
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* Modal for getting confirmation before user hits run project */}
      <ModalComponent
        id="user-confirmation-modal-run"
        size="md"
        show={userConfirmationModal}
        handleClose={() => setUserConfirmationModal(false)}
        modalContent={confirmationModalContent}
        modalCSSClass={"overflow-hidden;"}
      />
      {/* Modal for getting user's confirmation to overwrite the existing result or not */}
      <ModalComponent
        id="delete-run-project-modal"
        size="md"
        show={deleteRunProjectModal}
        handleClose={() => setDeleteRunProjectModal(false)}
        modalContent={runResultConfirmationModalContent}
        modalCSSClass={"overflow-hidden;"}
      />
      <ModalComponent
        id="project-running-modal"
        size="md"
        show={isProjectRunningModal}
        handleClose={() => setIsProjectRunningModal(false)}
        modalContent={projectRunningModalContent}
        modalCSSClass={"overflow-hidden"}
      />
      {/* Modal for selecting the user project tech file */}
      <ModalComponent
        id="list-project-techfile-modal"
        size="lg"
        show={viewProjectTechFileModal}
        handleClose={handleProjectTechFileCancel}
        modalContent={projectTechFileList}
        bodyClassName={"p-3 pt-0 overflow-auto"}
      />
      {/* Modal for uploading project tech file */}
      <ModalComponent
        id="upload-project-techfile-modal"
        size="md"
        show={uploadProjectTechFileModal}
        handleClose={() => setUploadProjectTechFileModal(false)}
        modalContent={uploadTechFileModalContent}
        modalCSSClass={"overflow-hidden"}
      />
      {/* modal for renaming the tech file */}
      <ModalComponent
        id="save-techfile-modal"
        size="md"
        show={saveTechFileModal}
        handleClose={handleCancelSaveTechFile}
        modalContent={saveTechFileModalContent}
        modalCSSClass={"overflow-hidden"}
      />
      {/* modal to confirm rename tech file */}
      <ModalComponent
        id="confirm-rename-techfile-modal"
        show={confirmTechFileRenameModal}
        size="md"
        handleClose={handleCancelRenameTechFile}
        modalContent={confirmRenameTechFileModalContent}
        modalCSSClass={"overflow-hidden"}
      />
    </>
  );
};

export default TechFile;
