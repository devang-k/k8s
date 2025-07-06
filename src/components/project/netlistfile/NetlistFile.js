
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: NetlistFile.js  
 * Description: This file is responsible to select and show Netlist file data. 
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
import "./NetlistFile.css";
import { Empty } from "antd";
import { getNetListFiles, getNetListData, editProjectData, checkValidationNetlist, getRunResultsStatus, fetchStageData } from "../../../server/server";
import { useNetListFileContext } from "../../providers/NetListFileProvider/NetListFileContext";
import { useTechFileContext } from "../../providers/TechFileProvider/TechFileContext";
import Modal from "react-bootstrap/Modal";
import Button from "react-bootstrap/Button";
import { useCreateProjectContext } from "../../providers/CreateProjectProvider/CreateProjectContext";
import { useEditProjectContext } from "../../providers/EditProjectProvider/EditProjectContext";
import { ToastContainer, toast } from "react-toastify";
import { useOutletContext } from "react-router-dom";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSearch, faTimes } from "@fortawesome/free-solid-svg-icons";
import { Tooltip as ReactTooltip } from 'react-tooltip'
import { useRunProjectContext } from "../../providers/RunProjectProvider/RunProjectContext";
import { useStage1ResultContext } from "../../providers/Stage1ResultProvider/Stage1ResultContext";
import { useStage2ResultContext } from "../../providers/Stage2ResultProvider/Stage2ResultContext";
import { useLayoutGraphContext } from "../../providers/LayoutGraphProvider/LayoutGraphContext";
import { faChevronRight, faChevronLeft, faAnglesRight, faAnglesLeft, faRotate, faCheck, faPen } from "@fortawesome/free-solid-svg-icons";
import { isDebugModeOn } from "../../../constant";
import { useFilterResultsContext } from "../../providers/FilterResultsProvider/FilterResultsContext";
import Editor from '@monaco-editor/react';


const NetlistFile = () => {
  const [errorMessage, setErrorMessage] = useState()
  const [netlistEditable, setNetlistEditable] = useState(false);
  const [loading, setLoading] = useState(false);
  const [validationError, setValidationError] = useState(false);
  const { clearFilterResultsContext ,filterRequestParameter, stage1GraphSelectedGdsCells, stage2GraphSelectedGdsCells} = useFilterResultsContext();
  const { setSidebarContent } = useOutletContext();
  const { setSelectedGdsItems, setStage1Result, setIsGdsSelectAllChecked, setStage1RunResultSummaryData, setStage1GdsLayoutImageData, setStage1TotalGDSNumber } = useStage1ResultContext();
  const { setIsUserOnStage2Page, setStage2Result, setStage2RunResultSummaryData, setStage2GdsLayoutImageData, setStage2TotalGDSNumber } = useStage2ResultContext();
  const {
    selectedNetlistFileName,
    setSelectedNetlistFileName,
    selectedNetlistFileType,
    setSelectedNetlistFileType,
    netlistFileContent,
    setNetlistFileContent,
    netlistCellInfo,
    setNetlistCellInfo,
    defaultNetlistFileData,
    setDefaultNetlistFileData,
    isNetListFileSelected,
    setIsNetListFileSelected,
    isSelectAllChecked,
    setIsSelectAllChecked,
    isNetlistDataChanged,
    setIsNetlistDataChanged,
    isNetlistFileContentDataChanged,
    setIsNetlistFileContentDataChanged,
  } = useNetListFileContext();
  const { techFileData, setIsTechFileSelected, selectedTechFileName, setSelectedTechFileName, selectedTechFileType, isTechDataChanged, setIsTechDataChanged, setDefaultTechFileData, setTechParameterValueError, setViewProjectTechFile, setProjectTechFileListData, setIsTechFileProjectSaved,techParameterValueError } = useTechFileContext();
  const { isStage1RunResultPresent, isStage2RunResultPresent, setIsStage1RunResultPresent, setIsStage2RunResultPresent, setTypeOfSelectedProject, typeOfSelectedProject, currentProjectId, setIsProjectSaved, setIsUserInAction3EditFromViewProject, setIsUserInAction2EditFromViewProject, setIsUserInAction1EditFromViewProject } = useCreateProjectContext();
  const { isUserInEditMode, setIsUserInEditMode, isButtonDisabledInEditMode, setIsButtonDisabledInEditMode, showResultButtonInStage1ResultInEditMode, setShowResultButtonInStage1ResultInEditMode, setShowResultButtonInTechFileInEditMode, showResultButtonInTechFileInEditMode } = useEditProjectContext();
  const { setIsProjectStillRunning, webSocketObj, setRunLayoutJobId, setIsRunningJobCompleted, setRunLayoutRunningJobLogs } = useRunProjectContext();
  const { setStage1GraphData, setStage2GraphData } = useLayoutGraphContext();
  const location = useLocation();
  const navigate = useNavigate();
  const { projectName, selectedFeatures, action } = location.state || {};
  const [netListFile, setNetListFile] = useState(false);
  const [netlistData, setNetlistData] = useState([]);
  const [selectedNetlistFileNameLocal, setSelectedNetlistFileNameLocal] =
    useState("");
  const [selectedNetlistFileTypeLocal, setSelectedNetlistFileTypeLocal] =
    useState("");
  const [isNetlistCellSelected, setIsNetlistCellSelected] = useState(false);
  const [searchInput, setSearchInput] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [isSuccess, setIsSuccess] = useState(false);
  const [netlistSidebarGrid, setNetlistSidebarGrid] = useState("3");
  const [isNetlistSidebarFullScreenOpen, setIsNetlistSidebarFullScreenOpen] = useState(false);
  const [isNetlistSidebarSmallScreenOpen, setIsNetlistSidebarSmallScreenOpen] = useState(true);
  const [editorContent, setEditorContent] = useState(netlistFileContent)


  const handleSelectNetlist = async () => {
    const getNetlistDataRes = await getNetListFiles();
    try {
      if (getNetlistDataRes?.status === false) {
        toast.error(getNetlistDataRes?.message);
      } else {
        setNetlistData(getNetlistDataRes?.data);
      }
    } catch (err) {
      console.error("Error while fetching netlist files data", err);
    } finally {
      setNetListFile(true);
    }
  };

  // below function handles api call and data creation for saving the project in S3
  const handleSaveProject = useCallback(async () => {
    //  request Body for save project
    if (isUserInEditMode) {
      const editProjectReqJSON = {
        ...(isNetlistDataChanged || isNetlistFileContentDataChanged) && {
          netlistMetadata: {
            fileName: selectedNetlistFileName,
            netlistType: selectedNetlistFileType?.toUpperCase(),
            cellSelections: netlistCellInfo,
          },
          netlistFileContents: btoa(editorContent || netlistFileContent),
        },
        ...(isTechDataChanged && {
          techMetadata: {
            fileName: selectedTechFileName,
            techType: selectedTechFileType?.toUpperCase(),
          },
          techFileContents: techFileData?.data?.FileContent,
        })
      }
      const editProjectRes = await editProjectData(currentProjectId, editProjectReqJSON);
      if (editProjectRes?.status === true) {
        setIsNetlistDataChanged(false);
        setIsTechDataChanged(false);
        setIsNetlistFileContentDataChanged(false)
        // Update default netlist data 
        setDefaultNetlistFileData({
          netlistFileContent: editorContent || netlistFileContent,
          netlistCellInfo: netlistCellInfo
        });
        setIsSuccess(true);
        toast.success(`${editProjectRes?.message} ${isDebugModeOn ? currentProjectId : ""}`, { autoClose: 10000 })
      } else {
        console.error(editProjectRes?.response.data?.message)
        toast.error(editProjectRes?.response.data?.message)
      }
    }
  }, [
    currentProjectId,
    netlistFileContent,
    selectedNetlistFileName,
    selectedNetlistFileType,
    selectedTechFileName,
    selectedTechFileType,
    techFileData?.data?.FileContent,
    isUserInEditMode,
    netlistCellInfo,
    isNetlistDataChanged,
    isTechDataChanged,
    setIsNetlistDataChanged,
    setIsTechDataChanged,
    setIsNetlistFileContentDataChanged,
    isNetlistFileContentDataChanged,
    setDefaultNetlistFileData,
    editorContent
  ]);

  const handleClose = () => {
    setNetListFile(false);
  };

  const handlePreviousButton = useCallback(() => {
    let selectionProjectTypeModal = typeOfSelectedProject !== 0;
    navigate("/home", {
      state: {
        projectName,
        selectedFeatures,
        projectFeatureModal: !selectionProjectTypeModal ? true : false,
        selectProjectOptionModal: selectionProjectTypeModal ? true : false,
        action
      },
    })
  }, [action, navigate, projectName, selectedFeatures, typeOfSelectedProject]);

  const handleCancelButton = useCallback(() => {
    if (webSocketObj) {
      webSocketObj.close();
    }
    setRunLayoutJobId(null);
    setIsUserInAction1EditFromViewProject(false);
    setIsUserInAction2EditFromViewProject(false);
    setIsUserInAction3EditFromViewProject(false);
    navigate("/home");
    setIsNetListFileSelected(false);
    setSelectedNetlistFileName(null);
    setIsTechFileSelected(false);
    setSelectedTechFileName("");
    setNetlistCellInfo();
    setNetlistFileContent();
    setSelectedNetlistFileType();
    setIsSelectAllChecked(false);
    setIsProjectSaved(false);
    setIsUserInEditMode(false);
    setIsButtonDisabledInEditMode(false);
    setIsRunningJobCompleted(false);
    setRunLayoutRunningJobLogs([]);
    setSelectedGdsItems([]);
    setIsUserOnStage2Page(false);
    setStage1Result();
    setStage2Result();
    setIsNetlistDataChanged(false);
    setIsTechDataChanged(false);
    setShowResultButtonInStage1ResultInEditMode(false);
    setShowResultButtonInTechFileInEditMode(false);
    setStage1GraphData(null);
    setStage2GraphData(null);
    setTypeOfSelectedProject(0);
    setIsProjectStillRunning(false);
    setDefaultTechFileData();
    setDefaultNetlistFileData();
    setIsGdsSelectAllChecked(false);
    setTechParameterValueError([]);
    setStage1RunResultSummaryData()
    setStage2RunResultSummaryData();
    setStage1GdsLayoutImageData([]);
    setStage2GdsLayoutImageData([]);
    clearFilterResultsContext();
    setIsStage1RunResultPresent(false);
    setIsStage2RunResultPresent(false);
    setIsNetlistFileContentDataChanged(false)
    setStage2TotalGDSNumber(0)
    setStage1TotalGDSNumber(0)
    setViewProjectTechFile(false);
    setProjectTechFileListData();
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
    setStage1Result,
    setStage2Result,
    setIsUserOnStage2Page,
    setIsRunningJobCompleted,
    setRunLayoutRunningJobLogs,
    navigate,
    setIsNetListFileSelected,
    setIsProjectSaved,
    setIsSelectAllChecked,
    setIsTechFileSelected,
    setNetlistCellInfo,
    setNetlistFileContent,
    setSelectedNetlistFileName,
    setSelectedNetlistFileType,
    setSelectedTechFileName,
    setIsUserInEditMode,
    setIsButtonDisabledInEditMode,
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
    setStage2GdsLayoutImageData,
    setDefaultNetlistFileData,
    setIsNetlistFileContentDataChanged,
    setStage2TotalGDSNumber,
    setStage1TotalGDSNumber,
    setViewProjectTechFile,
    setProjectTechFileListData,
    setIsTechFileProjectSaved
  ]);

  const handleNextPage = useCallback(() => {
    navigate("../techfiles/", {
      state: { projectName, selectedFeatures, action },
    });
  }, [action, projectName, selectedFeatures, navigate]);

  const handleAllCellInfoSelection = () => {
    const allSelected = !isSelectAllChecked;
    const updatedCellInfo = netlistCellInfo?.map((obj) => ({
      ...obj,
      is_selected: allSelected,
    }));
    setNetlistCellInfo(updatedCellInfo);
    setIsSelectAllChecked(allSelected);
    setIsNetlistDataChanged(true);
  };
  const handleNetlistFile = async () => {
    setSelectedNetlistFileName(selectedNetlistFileNameLocal);
    setSelectedNetlistFileType(selectedNetlistFileTypeLocal);
    setNetListFile(false);
    setIsNetListFileSelected(true);
    setIsSelectAllChecked(false);
    const netlistFileDataReq = {
      FileName: selectedNetlistFileNameLocal,
      FileType: selectedNetlistFileTypeLocal,
    };

    try {
      const getNetListDataRes = await getNetListData(netlistFileDataReq);
      if (getNetListDataRes?.status === false) {
        toast.error(getNetListDataRes?.message, { autoClose: 30000 });
        setIsNetListFileSelected(false);
        setIsNetlistCellSelected(false);
        setIsSelectAllChecked(false);
        setSelectedNetlistFileName("");
      } else {
        const netlistFileContentFromRes = getNetListDataRes?.data?.FileContent;
        const netlistCellInfoFromRes = getNetListDataRes?.data?.Cell_Info;
        const decodedData = atob(netlistFileContentFromRes);
        setNetlistFileContent(decodedData);
        setNetlistCellInfo(netlistCellInfoFromRes);
        setDefaultNetlistFileData({
          netlistFileContent: decodedData,
          netlistCellInfo: netlistCellInfoFromRes
        })
      }
    } catch (err) {
      console.error("Fetching the error", err);
    }

  };

  useEffect(() => {
    setIsNetlistCellSelected(netlistCellInfo?.some((item) => item.is_selected));
  }, [netlistCellInfo]);

  const handleNetListFileSelection = (name, type) => {
    setSelectedNetlistFileNameLocal(name);
    setSelectedNetlistFileTypeLocal(type);
  };

  const handleCheckboxChange = (cellName) => {
    const updatedNetlistCellInfo = netlistCellInfo?.map((cell) => {
      if (cell?.cell_name === cellName) {
        return { ...cell, is_selected: !cell?.is_selected }
      }
      return cell;
    });
    setNetlistCellInfo(updatedNetlistCellInfo);
    const allChecked = updatedNetlistCellInfo.every(
      (cell) => cell?.is_selected
    );
    setIsSelectAllChecked(allChecked);
    setIsNetlistDataChanged(true);
  };


  const handleSearchInputChange = (e) => {
    setSearchInput(e.target.value);
  };

  const handleSearchSubmit = (e) => {
    if (e.key === "Enter" || e.type === "click") {
      setSearchTerm(searchInput);
    }
  };
  const handleClearSearch = () => {
    setSearchInput("");
    setSearchTerm("");
  };
  useEffect(() => {
    if (searchInput === "") {
      setSearchTerm(searchInput);
    }
  }, [searchInput]);

  const filterNetlistCells = (value) => {
    const searchTerm = value?.toLowerCase();
    return netlistCellInfo?.filter((cell) => {
      const cellName = cell?.cell_name?.toLowerCase();

      // Check for normal filtering (includes)
      if (cellName?.includes(searchTerm)) {
        return true;
      }

      // Check for wildcard patterns
      if (searchTerm?.includes("*") || searchTerm?.includes("?")) {
        const pattern = searchTerm
          .replace(/\*/g, ".*")
          .replace(/\?/g, ".")
          .replace(/^/, "^")
          .replace(/$/, "$");
        const regex = new RegExp(pattern);
        return regex.test(cellName);
      }

      return false;
    });
  };

 const handleShowLayoutGenerationClick = useCallback(async () => {
    try {
      navigate("/dashboard/stage1result", { state: { projectName, selectedFeatures, action } });
    } catch (err) {
      console.error("Fetching Error", err);
    }
  }, [action, navigate, projectName, selectedFeatures]);

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
          <div>
            <h6 className="mb-2">Selected Netlist File:</h6>
            {selectedNetlistFileName ? (
              <span
                id="netlist-selected-filename"
                className="text-dark py-2 text-break text-muted"
              >
                {selectedNetlistFileName}
              </span>
            ) : (
              <span className="text-muted">No file selected</span>
            )}
          </div>
        </div>
      ),
      lower: (
        <div className="col-12">
          <div className="row">
          <div className="btn-group" role="group" aria-label="First group">
                {/* {(((doesStage1ResultExisit) || (stage1Result && stage1Result.data && Array.isArray(stage1Result.data.Items))) && showResultButtonInTechFileInEditMode) && ( */}
           
                {( (action === 3  || action === 1) && isStage1RunResultPresent && showResultButtonInTechFileInEditMode) && (
                
                <Button
                  id="show-layout-existing-result"
                  onClick={handleShowLayoutGenerationClick}
                  className="app-primary-button-color border-0 my-1 w-100"                >
                  Show LayoutGeneration Result
                </Button>
              )}
            </div>
            <div className="btn-group" role="group" aria-label="First group">
                {/* {(((doesStage1ResultExisit) || (stage1Result && stage1Result.data && Array.isArray(stage1Result.data.Items))) && showResultButtonInTechFileInEditMode) && ( */}
                {( action === 3 && isStage2RunResultPresent && showResultButtonInStage1ResultInEditMode) && (
                <Button
                  id="show-hyperExpressivity-existing-result"
                  onClick={handleShowExisitingHyperResult}
                  className="app-primary-button-color border-0 my-1 w-100"                >
                   Show HyperExpressivity Result
                </Button>
              )}
            </div>
            <div className="btn-group" role="group" aria-label="First group">
              {(isUserInEditMode && isButtonDisabledInEditMode) ||
                (!isUserInEditMode && !isButtonDisabledInEditMode) ? (
                <div className="w-100">
                  <Button
                    data-tooltip-id="select-netlist-button-tooltip"
                    data-tooltip-content={isButtonDisabledInEditMode && "You cannot change netlist file after saving project once."}
                    id="netlist-select-button"
                    onClick={handleSelectNetlist}
                    disabled={isButtonDisabledInEditMode}
                    className={`my-1 w-100 ${isButtonDisabledInEditMode ? "app-secondary-button-color cursor_not_allowed border-0" : "app-primary-button-color border-0"}`}
                  >
                    Select Netlist
                  </Button>
                  {isButtonDisabledInEditMode && <ReactTooltip id="select-netlist-button-tooltip" place="top" style={{ width: "260px", zIndex: 9999 }} />}
                </div>
              ) :
              <>
                <Button
                  data-tooltip-id="save-button-onNetlist-tooltip"
                  data-tooltip-content={techParameterValueError?.length >0 && "Handle error/s on parameter value/s on variation tab to save project"}
                  id="netlist-save-button"
                  onClick={handleSaveProject}
                  disabled={!isNetlistDataChanged && !isTechDataChanged && !isNetlistFileContentDataChanged ? true : techParameterValueError?.length >0 ? true: false}
                  className={`my-1 w-100 ${!isNetlistDataChanged && !isTechDataChanged && !isNetlistFileContentDataChanged ?"app-secondary-button-color border-0 cursor_not_allowed"  : techParameterValueError?.length >0  ? "app-secondary-button-color border-0 cursor_not_allowed" : "app-primary-button-color border-0"}`}
                >
                  Save
                </Button>
                {techParameterValueError?.length >0 && <ReactTooltip id="save-button-onNetlist-tooltip" place="top" style={{ width: "260px", zIndex: 9999 }} />}
              </>
              }
            </div>
            <div className="btn-group" role="group" aria-label="Second group">
              <Button
                data-tooltip-id="previous-button-tooltip"
                data-tooltip-content={isButtonDisabledInEditMode && "You cannot change feature after saving project once."}
                id="previous-button"
                onClick={handlePreviousButton}
                disabled={isUserInEditMode}
                className={`ms-0 mx-2 my-1 w-50 ${isUserInEditMode ? "app-secondary-button-color border-0 cursor_not_allowed" : "app-primary-button-color border-0"} rounded-end-0`}
              >
                Previous
              </Button>
              {isButtonDisabledInEditMode && <ReactTooltip id="previous-button-tooltip" place="top" style={{ width: "170px", zIndex: 9999 }} />}
              <Button
                id="next-button"

                onClick={handleNextPage}
                className={`ms-0 my-1 w-50 border-0 ${!isNetlistCellSelected || netlistEditable ? "app-secondary-button-color border-0  cursor_not_allowed" : "app-primary-button-color border-0"
                  }`}
                disabled={!isNetlistCellSelected || netlistEditable}
                data-tooltip-id="tooltip-netList-NextButton"
                data-tooltip-content="Select netlist file, validate it, and select at least one netlist cell to go next."
                data-tooltip-place="top"
              >
                Next
              </Button>
              {(!isNetlistCellSelected || netlistEditable) && (
                <ReactTooltip id="tooltip-netList-NextButton" style={{ width: "260px", zIndex: 9999 }} />
              )}
            </div>
            <div className="btn-group" role="group" aria-label="First group">
              <Button
                id="cancel-button"
                onClick={handleCancelButton}
                className="my-1 app-secondary-button-color border-0"
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
    showResultButtonInTechFileInEditMode,
    isStage1RunResultPresent,
    isStage2RunResultPresent,
    action,
    handleShowExisitingHyperResult,
    handleShowLayoutGenerationClick,
    netlistEditable,
    handleSaveProject,
    setSidebarContent,
    isNetlistCellSelected,
    selectedNetlistFileName,
    handleCancelButton,
    handleNextPage,
    handlePreviousButton,
    isUserInEditMode,
    isButtonDisabledInEditMode,
    isNetlistDataChanged,
    isTechDataChanged,
    projectName,
    isNetlistFileContentDataChanged,
    techParameterValueError
  ]);

  const toggleNetlistSidebarFullScreen = () => {
    setIsNetlistSidebarFullScreenOpen(!isNetlistSidebarFullScreenOpen);
    setIsNetlistSidebarSmallScreenOpen(false);
  };

  const toggleNetlistSidebarSmallScreen = () => {
    setIsNetlistSidebarSmallScreenOpen(!isNetlistSidebarSmallScreenOpen);
    setIsNetlistSidebarFullScreenOpen(false);
  };

  const toggleNetlistSidebarMinimize = () => {
    setIsNetlistSidebarFullScreenOpen(false);
    setIsNetlistSidebarSmallScreenOpen(false);
  };

  useEffect(() => {
    if (isNetlistSidebarFullScreenOpen) {
      setNetlistSidebarGrid("12");
    } else if (isNetlistSidebarSmallScreenOpen) {
      setNetlistSidebarGrid("3");
    } else {
      setNetlistSidebarGrid("0 d-none");
    }
  }, [isNetlistSidebarFullScreenOpen, isNetlistSidebarSmallScreenOpen, setNetlistSidebarGrid]);


  const handleEditorChange = (value) => {
    setEditorContent(value)
    setIsNetlistFileContentDataChanged(true);
  }

  const handleNetlistIconClick = async () => {
    //open in edit mode 
    if (!netlistEditable) {
      setNetlistEditable(true);
      setIsNetlistFileContentDataChanged(true)
      return;
    }
    setLoading(true);
    try {
      const validationResult = await checkValidationNetlist(editorContent);
      if (validationResult?.status !== true) {
        setValidationError(true);
        setErrorMessage(validationResult?.message);
        return;
      }
      // Proceed with setting the updated content 
      setValidationError(false);
      setNetlistEditable(false);
      setNetlistFileContent(editorContent);

      // Process cell information if available
      if (validationResult?.data?.Cell_Info) {
        const currentSelections = {};
        netlistCellInfo?.forEach(({ cell_name, is_selected }) => {
          currentSelections[cell_name] = is_selected;
        });

        //update cell information while remember previous selection
        const updatedCellInfo = validationResult?.data?.Cell_Info?.map(cell => ({
          ...cell,
          is_selected: currentSelections[cell?.cell_name] || false
        }));

        // Check if any selections changed
        const hasCellSelectionChanges = updatedCellInfo?.some(cell =>
          cell?.is_selected !== currentSelections[cell?.cell_name]
        );

        // Check if all cells are selected
        const allSelected = updatedCellInfo?.every(cell => cell?.is_selected);

        // Set all relevant state variables 
        setNetlistCellInfo(updatedCellInfo);
        setIsNetlistDataChanged(hasCellSelectionChanges);
        setIsSelectAllChecked(allSelected);
      }
    } catch (error) {
      setValidationError(true);
      setErrorMessage(true);
    } finally {
      setLoading(false);
    }
  };


  //Reset the netlist content
  const resetNetlistFileContent = useCallback(() => {
    if (defaultNetlistFileData) {
      setEditorContent(defaultNetlistFileData?.netlistFileContent)
      setNetlistFileContent(defaultNetlistFileData?.netlistFileContent);
      setNetlistCellInfo(defaultNetlistFileData?.netlistCellInfo)
    }
    // Force the <pre> tag to reset by changing its key
    // Increment key to trigger re-mount

    setIsNetlistDataChanged(false);
    setIsSelectAllChecked(false);
    setValidationError(false);
    setNetlistEditable(false);
  },
    [defaultNetlistFileData,
      setNetlistFileContent,
      setIsNetlistDataChanged,
      setIsSelectAllChecked,
      setValidationError,
      setNetlistCellInfo,
      setEditorContent,
      setNetlistEditable
    ])

  useEffect(() => {
    setEditorContent(netlistFileContent)
  }, [netlistFileContent])

  // useEffect written to avoid ResizeObser Issue .
  useEffect(() => {
    // Store the original ResizeObserver
    const OriginalResizeObserver = window.ResizeObserver;

    // Create the wrapped ResizeObserver
    window.ResizeObserver = function (callback) {
      const wrappedCallback = (entries, observer) => {
        window.requestAnimationFrame(() => {
          callback(entries, observer);
        });
      };

      return new OriginalResizeObserver(wrappedCallback);
    };

    // Copy static methods
    Object.keys(OriginalResizeObserver).forEach(staticMethod => {
      if (OriginalResizeObserver.hasOwnProperty(staticMethod)) {
        window.ResizeObserver[staticMethod] = OriginalResizeObserver[staticMethod];
      }
    });
    // Cleanup function to restore original ResizeObserver
    return () => {
      window.ResizeObserver = OriginalResizeObserver;
    };
  }, []); // Empty dependency array ensures this runs once on mount

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
          {isNetListFileSelected || isUserInEditMode ? (
            <>

              <div className={`col-${netlistSidebarGrid} netlist-sidebar`}>
                <div className={`${isNetlistSidebarFullScreenOpen ? "me-3" : ""} netlist-content`}>
                  <ul className={`list-group netlist-cell-class ${!netlistCellInfo || netlistCellInfo?.length === 0 ? "d-flex justify-content-center align-items-center" : ""}`}>
                    {loading && <div className="spinner-border"><span className="visually-hidden">Loading...</span></div>}
                    {netlistCellInfo && netlistCellInfo?.length > 0 ? (
                      <>
                        <li className="list-group-item bg-light sticky-top netlist-header">
                          <span className="d-flex align-items-center mb-2">
                            <input
                              type="text"
                              id="netlist-cell-search-box"
                              className="form-control ps-1 search-input"
                              value={searchInput}
                              placeholder="Search"
                              onChange={handleSearchInputChange}
                              onKeyUp={handleSearchSubmit}
                            />
                            {searchInput && (
                              <FontAwesomeIcon
                                icon={faTimes}
                                id="netlist-cell-search-cross-icon"
                                className="position-absolute end-0 me-5 text-secondary clear-search-icon"
                                onClick={handleClearSearch}
                              />
                            )}
                            <FontAwesomeIcon
                              icon={faSearch}
                              id="netlist-cell-search-button-box"
                              className="search-icon ms-2"
                              onClick={handleSearchSubmit}
                              value={searchInput}
                            />
                          </span>
                          {!searchTerm && (
                            <div className="d-flex align-items-center">
                              <input
                                className="form-check-input me-2"
                                id="cell-selection-deselection"
                                type="checkbox"
                                onChange={handleAllCellInfoSelection}
                                checked={isSelectAllChecked}
                                style={{ cursor: "pointer" }}
                                aria-label="Select All"
                              />
                              <label
                                htmlFor="cell-selection-deselection"
                                style={{ cursor: "pointer" }}
                              >
                                {isSelectAllChecked ? "Deselect all" : "Select all"}
                              </label>
                            </div>
                          )}
                        </li>
                        {filterNetlistCells(searchTerm).length > 0 ? (
                          filterNetlistCells(searchTerm).map((cell, index) => (
                            <li
                              className="list-group-item py-1 d-flex netlist-cell-item"
                              id={`cell-list-description-${cell?.cell_name}`}
                              key={cell?.cell_name + index}
                              onClick={() => handleCheckboxChange(cell?.cell_name)}
                            >
                              <input
                                className="form-check-input me-2"
                                id={`cell-selection-checkbox-${cell?.cell_name}`}
                                type="checkbox"
                                checked={cell?.is_selected}
                                onChange={() => handleCheckboxChange(cell?.cell_name)}
                                aria-label={`Select ${cell?.cell_name}`}
                              />
                              <label
                                id="cell-list-label-name"
                                title={cell?.cell_name}
                                className="form-check-label netlist-cell-label"
                                style={{ cursor: "pointer" }}
                                htmlFor={`cell-selection-checkbox-${cell?.cell_name}`}
                                onClick={(e) => {
                                  e.preventDefault();
                                  handleCheckboxChange(cell?.cell_name);
                                }}
                              >
                                <small>{cell?.cell_name}</small>
                              </label>
                            </li>
                          ))
                        ) : (
                          <li className="list-group-item text-center text-muted">
                            No matching cells found
                          </li>
                        )}
                      </>
                    ) : (
                      <div className="spinner-border" role="status">
                        <span className="sr-only">Loading...</span>
                      </div>
                    )}
                  </ul>
                </div>
              </div>
              <div className={`col-${isNetlistSidebarFullScreenOpen ? "0" : (isNetlistSidebarSmallScreenOpen ? "9" : "12")} flex-column p-0`} style={{
                maxHeight: "101%",
                overflowY: "auto",
                overflowX: "hidden",
              }}>
                <button
                  onClick={toggleNetlistSidebarFullScreen}
                  className="position-absolute app-primary-button-color border-0"
                  id="netlist-sidebar-fullscreen-button"
                  data-tooltip-id="netlist-sidebar-fullscreen-button-tooltip"
                  data-tooltip-content={"Maximize cell names window"}
                  style={{
                    color: "#fff",
                    top: "45%",
                    width: "25px",
                    fontSize: "12px",
                    zIndex: 999,
                    display: isNetlistSidebarFullScreenOpen ? "none" : "block",
                    marginLeft: isNetlistSidebarFullScreenOpen ? "0px" : "-10px",
                    ...(isNetlistSidebarFullScreenOpen ? { right: "0px" } : {}),
                  }}
                >
                  <ReactTooltip id="netlist-sidebar-fullscreen-button-tooltip" style={{ zIndex: 9999 }} />
                  <FontAwesomeIcon
                    icon={isNetlistSidebarFullScreenOpen ? faAnglesLeft : faAnglesRight}
                    style={{ cursor: "pointer" }}
                  />
                </button>

                <button
                  onClick={toggleNetlistSidebarSmallScreen}
                  className="position-absolute app-primary-button-color border-0"
                  id="netlist-sidebar-smallscreen-button"
                  data-tooltip-id="netlist-sidebar-smallscreen-button-tooltip"
                  data-tooltip-content={"Restore cell names window"}
                  style={{
                    color: "#fff",
                    top: "35%",
                    width: "25px",
                    fontSize: "12px",
                    zIndex: 999,
                    display: isNetlistSidebarSmallScreenOpen ? "none" : "block",
                    marginLeft: isNetlistSidebarSmallScreenOpen ? "0px" : "-10px",
                    right: isNetlistSidebarFullScreenOpen ? "0px" : undefined,
                  }}
                >
                  <ReactTooltip id="netlist-sidebar-smallscreen-button-tooltip" style={{ zIndex: 9999 }} />
                  <FontAwesomeIcon
                    icon={
                      isNetlistSidebarFullScreenOpen
                        ? faChevronLeft
                        : (isNetlistSidebarSmallScreenOpen ? faChevronRight : faChevronRight)
                    }
                    style={{ cursor: "pointer" }}
                  />
                </button>

                <button
                  onClick={toggleNetlistSidebarMinimize}
                  className="position-absolute app-primary-button-color border-0"
                  id="netlist-sidebar-minimize-button"
                  data-tooltip-id="netlist-sidebar-minimize-button-tooltip "
                  data-tooltip-content={"Minimize the cell names window"}
                  style={{
                    color: "#fff",
                    borderColor: "#0d6efd",
                    top: !isNetlistSidebarFullScreenOpen ? "35%" : "45%",
                    width: "25px",
                    fontSize: "12px",
                    zIndex: 999,
                    display: (isNetlistSidebarFullScreenOpen || isNetlistSidebarSmallScreenOpen) ? "block" : "none",
                    marginLeft: (isNetlistSidebarFullScreenOpen || isNetlistSidebarSmallScreenOpen) ? "-10px" : "0px",
                    ...((isNetlistSidebarFullScreenOpen && !isNetlistSidebarSmallScreenOpen) ? { right: "0px" } : {}),
                  }}
                >
                  <ReactTooltip id="netlist-sidebar-minimize-button-tooltip" />
                  <FontAwesomeIcon
                    icon={faAnglesLeft}
                    style={{ cursor: "pointer" }}
                  />
                </button>

                {/* netlist file content editable */}
                <div
                  className="netlist-data h-full"
                  style={{
                    padding: "0.5rem",
                    height: "98%",
                    color: 'black',
                    backgroundColor: 'white',
                  }}
                >
                  {loading && (
                    <div className="spinner-border">
                      <span className="visually-hidden">Loading...</span>
                    </div>
                  )}

                  
                  <div
                    className="text-primary text-end"
                    style={{
                      display: 'flex',
                      justifyContent: 'flex-end',
                      alignItems: 'center',
                      marginBottom: "0.5rem",
                    }}
                  >
                    {netlistEditable && (
                      <FontAwesomeIcon
                        icon={faRotate}
                        id="netlist-reset-icon"
                        style={{
                          cursor: "pointer",
                          marginRight: '10px',
                          border: "none",
                          textDecoration: "none",
                          outline: "none",
                        }}
                        className="admin-button border-0"
                        onClick={resetNetlistFileContent}
                        data-tooltip-id="netlist-content-reset-icon"
                        data-tooltip-content="Reset Netlist Content"
                      />
                    )}
                    <ReactTooltip id="netlist-content-reset-icon" style={{ zIndex: 9999 }} />

                    {netlistEditable ? (
                      <>
                        <FontAwesomeIcon
                          icon={faCheck}
                          id="netlist-check-icon"
                          style={{
                            cursor: "pointer",
                            border: "none",
                            textDecoration: "none",
                            outline: "none",
                            marginRight: "10px",
                          }}
                          className="admin-button border-0"
                          onClick={handleNetlistIconClick}
                          data-tooltip-id="netlist-content-validate-icon"
                          data-tooltip-content="Validate Netlist Content"
                        />
                        <ReactTooltip id="netlist-content-validate-icon" style={{ zIndex: 9999 }} />
                      </>
                    ) : (
                      <>
                        <FontAwesomeIcon
                          icon={faPen}
                          id="netlist-edit-icon"
                          style={{
                            cursor: "pointer",
                            border: "none",
                            textDecoration: "none",
                            outline: "none",
                            marginRight: "10px",
                          }}
                          className="admin-button border-0"
                          onClick={handleNetlistIconClick}
                          data-tooltip-id="netlist-content-edit-icon"
                          data-tooltip-content="Edit Netlist Content"
                        />
                        <ReactTooltip id="netlist-content-edit-icon" style={{ zIndex: 9999 }} />
                      </>
                    )}
                  </div>

                  {/* The Error Message Block */}
                  {validationError && (
                    <div
                      style={{
                        maxHeight: "10%",
                        overflowY: "auto",
                        color: "red",
                        padding: "0.5rem",
                        marginBottom: "0.5rem",
                        width: "100%",
                      }}
                    >
                      {Array.isArray(errorMessage) ? (
                        errorMessage?.map((msg, index) => (
                          <div key={index}>{msg}</div>
                        ))
                      ) : (
                        <div>{errorMessage}</div>
                      )}
                    </div>
                  )}

                  {/* the Editor */}
                  <div
                    id="netlist-file-Content-editable-editor"
                    style={{
                      overflowY: "hidden",
                      border: validationError ? '5px solid red' : 'none',
                      borderRadius: "5px",
                      height: validationError ? "86%" : "96%",
                    }}
                  >
                    <Editor
                      height="100%"
                      defaultValue={netlistFileContent}
                      value={editorContent}
                      onChange={handleEditorChange}
                      theme={netlistEditable ? "vs-dark" : "light"}
                      options={{
                        lineNumbers: false,
                        minimap: { enabled: false },
                        readOnly: netlistEditable ? false : true,
                        scrollBeyondLastLine: false, // Prevent scrolling beyond content
                      }}
                    />;
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="col-12 bg-light-brown-v1 d-flex flex-column justify-content-center align-items-center p-4">
              <Empty />
            </div>
          )}
        </div>
      </div >
      {netListFile && (
        <Modal
          id="select-netlistfile-modal"
          backdrop="static"
          keyboard={false}
          show={netListFile}
          onHide={handleClose}
          centered
          size="lg"
          animation={false}
          className="modal-style overflow-hidden modal-fade-in-bottom"
        >
          <Modal.Header closeButton>
            <Modal.Title>Select Netlist</Modal.Title>
          </Modal.Header>
          <Modal.Body className="p-3 pt-0 overflow-y-auto overflow-x-hidden">
            <div className="row">
              <ul className="list-group">
                <li
                  className="list-group-item border rounded mb-2 bg-light sticky-top me-0 pe-3"
                  style={{ zIndex: 1 }}
                  id={selectedNetlistFileName}
                >
                  <div className="d-flex justify-content-between ">
                    <div className="">
                      <label className="form-check-label fw-bold">
                        File Name
                      </label>
                    </div>
                    <div className="">
                      <label className="form-check-label fw-bold">
                        File Type
                      </label>
                    </div>
                  </div>
                </li>
                {netlistData && netlistData.length > 0 ? (
                  netlistData.map((data) => (
                    <li
                      key={data.FileName}
                      className={`list-group-item d-flex justify-content-between align-items-center py-2 border rounded mb-2 ${selectedNetlistFileNameLocal === data.FileName
                        ? "app-primary-button-color border-0 text-white"
                        : "bg-light"
                        }`}
                      onClick={() =>
                        handleNetListFileSelection(data.FileName, data.FileType)
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
                    No netlist files available
                  </li>
                )}
              </ul>
            </div>
          </Modal.Body>
          <Modal.Footer className="d-flex justify-content-center gap-2">
            <Button
              id="ok-button"
              onClick={handleNetlistFile}
              className={`col-4 m-2 border-0 ${selectedNetlistFileNameLocal || selectedNetlistFileTypeLocal ? "app-primary-button-color" : "app-secondary-button-color cursor_not_allowed"
                }`}
              disabled={
                !selectedNetlistFileNameLocal || !selectedNetlistFileTypeLocal
              }
              data-tooltip-id="tooltip-netlist-Okbutton"
              data-tooltip-content="Select atleast one netlist file to proceed ahead."
              data-tooltip-place="top"
            >
              Ok
            </Button>
            {(!selectedNetlistFileNameLocal || !selectedNetlistFileTypeLocal) && (<ReactTooltip id="tooltip-netlist-Okbutton" style={{ zIndex: 9999 }} />)}
            <Button
              id="cancel-button"
              onClick={handleClose}
              className="col-4 m-2 app-secondary-button-color border-0"
            >
              Cancel
            </Button>
          </Modal.Footer>
        </Modal>
      )
      }
    </>
  );
};
export default NetlistFile;
