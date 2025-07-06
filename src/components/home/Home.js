
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: Home.js  
 * Description: This file is responsible to show home page after user login. 
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

import React, { useState, useEffect, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "./Home.css";
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
import Carousel from 'react-bootstrap/Carousel';
import { validateProjectName, getProjectWithStage1ResultsForUser, getProjectListForUser, fetchUserDataFromSavedProject, fetchStageData, getListOfRunningJob, deleteUserProject } from "../../server/server";
import { useTechFileContext } from '../providers/TechFileProvider/TechFileContext';
import { useNetListFileContext } from '../providers/NetListFileProvider/NetListFileContext';
import CreateProjectModalBody from './CreateProjectModalBody';
import ProjectFeatureModalBody from './ProjectFeatureModalBody';
import DeleteProjectModalBody from "./DeleteProjectModalBody";
import { useCreateProjectContext } from "../providers/CreateProjectProvider/CreateProjectContext";
import { useEditProjectContext } from "../providers/EditProjectProvider/EditProjectContext";
import { useStage1ResultContext } from "../providers/Stage1ResultProvider/Stage1ResultContext";
import { useRunProjectContext } from "../providers/RunProjectProvider/RunProjectContext";
import ModalComponent from "../utils/Modal/ModalComponent";
import { ProjectWithStage1ResultListModalBody } from "./ProjectWithStage1ResultListModalBody";
import ViewProjectResult from "./ViewProjectResult";
import { ToastContainer, toast } from "react-toastify";
import { Tooltip as ReactTooltip } from 'react-tooltip'
import RunningJobModalBody from "./RunningJobModalBody";
import CreateProjectTypeSelectionModalBody from "./CreateProjectTypeSelectionModalBody";
import { useResetContextData } from "../../Hooks/ResetContextHook"
import Footer from "../Footer/Footer"
import Working from "../../Assets/Images/create.png"
import View from "../../Assets/Images/backlog.png"
import Edit from "../../Assets/Images/Edit.png"
import CarouselImage1 from "../../Assets/Images/CarouselImg1.png"
import CarouselImage2 from "../../Assets/Images/CarouselImg2.png"
import CarouselImage3 from "../../Assets/Images/CarouselImg3.png"
import { currentAppVersion } from '../../constant'

const LandingPage = () => {
  const resetContext = useResetContextData();
  const { setIsTechFileSelected, setSelectedTechFileName, setTechFileData, setSelectedTechFileType, setDefaultTechFileData, setViewProjectTechFile, setIsTechFileProjectSaved } = useTechFileContext();
  const { setIsNetListFileSelected, setSelectedNetlistFileName, setSelectedNetlistFileType, setActionSelected, setNetlistCellInfo, setNetlistFileContent, setIsSelectAllChecked, actionSelected, setDefaultNetlistFileData } = useNetListFileContext();
  const { isUserInEditMode, setIsUserInEditMode, userCreatedProjectList, setUserCreatedProjectList } = useEditProjectContext();
  const { setStage1Result, setSelectedGdsItems, setIsGdsSelectAllChecked } = useStage1ResultContext()
  const {
    setCurrentProjectId,
    isProjectSaved,
    setIsProjectSaved,
    currentProjectId,
    setProjectListWithStage1Result,
    projectListWithStage1Result,
    selectedFeature,
    setSelectedFeature,
    setSelectedProjectIdFromList,
    setSelectedProjectNameWithStage1Result,
    setIsProjectWithStage1ResultSelectedFromList,
    setIsHyperExpressivityProjectSaved,
    inPreviousThroughHyperExpressivityProjectCreation,
    setInPreviousThroughHyperExpressivityProjectCreation,
    setProjectDetailsSelectedForHyperExpressivityFlow,
    setIsUserInAction3EditFromViewProject,
    setIsUserInAction2EditFromViewProject,
    setIsUserInAction1EditFromViewProject,
    setTypeOfSelectedProject,
  } = useCreateProjectContext();
  const { setIsProjectStillRunning, listOfRunningJobsData, setListOfRunningJobsData, setRunningJobStatus, setRunLayoutJobId } = useRunProjectContext();

  const location = useLocation();
  const navigate = useNavigate();
  const initialProjectName = location.state?.projectName || "";
  const initialSelectedFeatures = location.state?.selectedFeatures || [];
  const initialProjectFeatureModal =
    location.state?.projectFeatureModal || false;
  const initialCreateProjectModal = location.state?.createProjectModal || false;
  const [createProjectModal, setCreateProjectModal] = useState(false);
  const [projectFeatureModal, setProjectFeatureModal] = useState(
    initialProjectFeatureModal
  );
  const initialSelectProjectOptionModal = location.state?.selectProjectOptionModal || false;
  const [selectProjectOptionModal, setSelectProjectOptionModal] = useState(initialSelectProjectOptionModal);
  const [projectName, setProjectName] = useState(initialProjectName);
  const [projectNameError, setProjectNameError] = useState("");
  const [checkedItems, setCheckedItems] = useState({
    layoutGeneration: initialSelectedFeatures?.includes("layoutGeneration"),
    layoutHyperexpressivity: initialSelectedFeatures?.includes(
      "layoutHyperexpressivity"
    ),
  });
  const [isHyperexpressivityModalOpen, setIsHyperexpressivityModalOpen] =
    useState(location?.state?.isHyperexpressivityModalOpen || false);
  const [
    hyperexpressivityProjectListModalContent,
    setHyperexpressivityProjectListModalContent,
  ] = useState({
    title: "",
    body: "",
    footer: "",
  });
  const [isProjectWithStage1ResultSelectedInModal, setIsProjectWithStage1ResultSelectedInModal] = useState(false);
  const initialViewProjectModal =
    location.state?.viewProjectModal || false;
  const [viewProjectModal, setViewProjectModal] = useState(initialViewProjectModal);
  const [viewProjectListdata, setViewProjectListdata] = useState({
    title: "",
    body: "",
    footer: ""
  });
  const [typeOfProjectCreationSelectionModalBody, setTypeOfProjectCreationSelectionModalBody] = useState({
    title: "",
    body: "",
    footer: "",
  });
  const [viewProjectListFileSelectedInModal, setViewProjectListFileSelectedInModal] = useState(false);
  const [typeOfProjectCreationSelectedInModal, setTypeOfProjectCreationSelectedInModal] = useState(false);
  const [selectedFileNameFromListOfSavedProject, setSelectedFileNameFromListOfSavedProject] = useState()
  const [selectedNetlistFileNameFromList, setSelectedNetlistFileNameFromList] = useState();
  const [selectedTechFileNameFromList, setSelectedTechFileNameFromList] = useState();
  const [selectedProjectIdFromStage1ListRow, setSelectedProjectIdFromStage1ListRow] = useState();
  const [selectedProjectNameFromStage1ListRow, setSelectedProjectNameFromStage1ListRow] = useState();
  const [listOfRunningJobModal, setListOfRunningJobModal] = useState();
  const [runningJobListData, setRunningJobListData] = useState({
    title: "",
    body: "",
    footer: ""
  });
  const [deleteProjectModal, setDeleteProjectModal] = useState(false);
  const [projectVersion, setProjectVersion] = useState();
  const isNextButtonDisabled = !Object.values(checkedItems)?.some(Boolean); //Check for enabling disabling next button

  // convert current app version to number
  const currentVersion = Number(currentAppVersion);

  // below is the state to update the state of the view project file
  const handleViewProjectModalSelectedInModal = useCallback((
    isViewProjectListFileSelected, version
  ) => {
    setViewProjectListFileSelectedInModal(isViewProjectListFileSelected);
    setProjectVersion(version);
  }, [setViewProjectListFileSelectedInModal, setProjectVersion]);

  // below is the state to update the state of the project creation type selection
  const handleProjectCreationTypeSelection = useCallback((
    isProjectTypeSelected, selectedProjectType
  ) => {
    setTypeOfProjectCreationSelectedInModal(isProjectTypeSelected);
    setTypeOfSelectedProject(selectedProjectType);

  }, [setTypeOfSelectedProject]);

  //below function will update the state for whether project is selected from list or not
  const handleStateSetForProjectSelection = useCallback(
    (
      isProjectSelected,
      currentSelectedProjectId,
      projectNameSelected,
      currentSelectedNetListFileName,
      currentSelectedTechFileName
    ) => {
      setSelectedProjectIdFromList(currentSelectedProjectId);
      setSelectedNetlistFileNameFromList(currentSelectedNetListFileName);
      setSelectedTechFileNameFromList(currentSelectedTechFileName);
      setIsProjectWithStage1ResultSelectedInModal(isProjectSelected);
      setSelectedProjectIdFromStage1ListRow(currentSelectedProjectId);
      setSelectedProjectNameFromStage1ListRow(projectNameSelected);
    },
    [setSelectedProjectIdFromList]
  );

  // function to handle closing of hyperexpressivity project list modal
  const handleCloseHyperexpressivityProjectList = useCallback(() => {
    setIsHyperexpressivityModalOpen(false);
    navigate("/home", { replace: true });
    setProjectName();
    setCheckedItems({
      layoutGeneration: true,
      layoutHyperexpressivity: true,
    });
    setIsProjectWithStage1ResultSelectedInModal(false);
  }, [navigate]);

  // below function handles cancel of select project type modal
  const handleCancelProjectTypeSelection = useCallback(() => {
    setSelectProjectOptionModal(false);
    setProjectName("");
    setCreateProjectModal(false);
    setTypeOfProjectCreationSelectedInModal(false);
    resetContext();

  }, [resetContext]);

  /* below function handles ok button click on project list with stage1 result modal*/
  const handleOkClickOnProjectListWithStage1ResultModal = useCallback(() => {
    setSelectedNetlistFileName(selectedNetlistFileNameFromList);
    setSelectedTechFileName(selectedTechFileNameFromList);
    setSelectedProjectNameWithStage1Result(
      selectedProjectNameFromStage1ListRow
    ); // setting selected project name with stage1 result in context
    setSelectedProjectIdFromList(selectedProjectIdFromStage1ListRow);
    navigate(`/dashboard/stage1result`, {
      state: { projectName, selectedFeatures: selectedFeature, actionSelected },
    });
    setIsHyperexpressivityModalOpen(false);
  }, [
    selectedFeature,
    selectedProjectIdFromStage1ListRow,
    selectedProjectNameFromStage1ListRow,
    setSelectedProjectIdFromList,
    setSelectedProjectNameWithStage1Result,
    actionSelected,
    navigate,
    projectName,
    selectedNetlistFileNameFromList,
    selectedTechFileNameFromList,
    setSelectedNetlistFileName,
    setSelectedTechFileName,
  ]);

  const handleCreateNewProjectClick = async () => {
    try {
      const validationResponse = await validateProjectName({ projectName });
      if (validationResponse?.status) {
        setProjectNameError("");
        setCreateProjectModal(false);
        setProjectFeatureModal(true);
        setCheckedItems({
          layoutGeneration: true,
          layoutHyperexpressivity: true
        })

        return true;
      } else {
        setProjectNameError(validationResponse?.message);
        return false;
      }
    } catch (error) {
      console.error("Error validating project name:", error);
      return false;
    }
  };

  const handlePOCProjectCreationClick = () => {
    //For POC feature introduction on success of create project modal ok click will now navigate user to select project option & then to select feature
    setSelectProjectOptionModal(true);
    // below removes hyperexpressivity selection for poc project types
    setCheckedItems({
      layoutGeneration: checkedItems?.layoutGeneration || false
    })
  }
  const handleCheckboxChange = (e) => {
    const { name, checked } = e.target;
    setCheckedItems((prev) => ({
      ...prev,
      [name]: checked,
    }));
    setSelectedFeature((prev) => ({
      ...prev,
      [name]: checked,
    })); //setting feature in context
  };

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      const selectedFeatures = Object.keys(checkedItems)?.filter(
        (key) => checkedItems[key]
      );
      setSelectedFeature(selectedFeatures);
      let action;
      if (
        selectedFeatures.length === 1 &&
        selectedFeatures[0] === "layoutGeneration"
      ) {
        action = 1;
        setActionSelected(1);
      } else if (
        selectedFeatures?.length === 1 &&
        selectedFeatures[0] === "layoutHyperexpressivity"
      ) {
        action = 2;
        setActionSelected(2);
      } else if (selectedFeatures?.length > 1) {
        action = 3;
        setActionSelected(3);
      }
      // once action is set navigating user to respective flow
      if (action === 1 || action === 3) {
        //user navigates to netlist file selection page
        navigate("/dashboard/netlist-file", {
          state: { projectName, selectedFeatures, action },
        });
      } else if (action === 2) {
        //modal to displaying projects having stage1 results for user list will be shown
        const projectWithStage1ResultsRes =
          await getProjectWithStage1ResultsForUser();
        setProjectListWithStage1Result(projectWithStage1ResultsRes); //setting projectlist having stage1 data in context
        setProjectFeatureModal(false);
        navigate("/dashboard/stage1result", {
          state: { projectName, selectedFeatures, action },
        });
      }
    },
    [
      checkedItems,
      navigate,
      projectName,
      setSelectedFeature,
      setActionSelected,
      setProjectListWithStage1Result,
    ]
  );

  const handleCreateProjectClick = () => {
    setProjectNameError("");
    setCreateProjectModal(true);
  };

  const handleCloseViewProject = useCallback(() => {
    setIsUserInEditMode(false);
    setViewProjectModal(false);
    setIsUserInAction3EditFromViewProject(false);
    setViewProjectListFileSelectedInModal(false);
    setProjectVersion();
  }, [
    setIsUserInAction3EditFromViewProject,
    setViewProjectModal,
    setViewProjectListFileSelectedInModal,
    setIsUserInEditMode,
    setProjectVersion
  ]);

  // below function delete the user project 
  const confirmDeleteProjectButton = async () => {
    const deleteUserProjectRes = await deleteUserProject(currentProjectId);
    try {
      if (deleteUserProjectRes?.status === true) {
        setDeleteProjectModal(false);
        toast.success(deleteUserProjectRes?.message, { autoClose: 10000 })
        setViewProjectListFileSelectedInModal(false);
        setViewProjectModal(false);
      }
      else {
        toast.error(deleteUserProjectRes?.message);
      }
    }
    catch (error) {
      console.error("Error while deleting the project", error)
    }
  }

  //Delete project modal Content
  const deleteProjectModalContent = {
    title: "Confirm delete",
    body: <DeleteProjectModalBody selectedFileNameFromListOfSavedProject={selectedFileNameFromListOfSavedProject} />,
    footer: (<>
      <Button className="delete-button-color border-0 w-25" onClick={confirmDeleteProjectButton} id="cofirm-delete-project-yes-button"> Yes </Button>
      <Button className="w-25 app-secondary-button-color border-0" onClick={() => { setDeleteProjectModal(false); }} id="confirm-delete-project-no-button">No</Button>
    </>
    )
  }

  // below function handles click on delete button
  const handleDeleteProject = () => {
    setDeleteProjectModal(true);
  }

  // below function handles user selecting some project to edit from view project 

  const handleViewProjectSelection = useCallback(async () => {
    setViewProjectModal(false);
    setIsUserInEditMode(true);
    const userDataFromSavedProjectRes = await fetchUserDataFromSavedProject(currentProjectId);
    try {
      if (userDataFromSavedProjectRes?.status && userDataFromSavedProjectRes?.status_code === 200) {
        setTypeOfSelectedProject(userDataFromSavedProjectRes?.data?.project_details?.project_type || 0);
        const selectedAction = userDataFromSavedProjectRes?.data?.project_details?.action;
        setActionSelected(selectedAction);
        setViewProjectTechFile(true)
        let projectFeatureSelection  // This variable stores the selected feature from saved project 
        let projectNameInSavedProject = userDataFromSavedProjectRes?.data?.project_details?.project_name // This variable stores the project Name from saved project
        if (selectedAction === 1 || selectedAction === 3) {
          setNetlistCellInfo(userDataFromSavedProjectRes?.data?.project_details?.netlist_metadata?.cellSelections);
          const decodedNetlistFileContent = atob(userDataFromSavedProjectRes?.data?.netlistFileContent);
          setNetlistFileContent(decodedNetlistFileContent);
          setDefaultNetlistFileData(
            {
              netlistFileContent: decodedNetlistFileContent,
              netlistCellInfo:userDataFromSavedProjectRes?.data?.project_details?.netlist_metadata?.cellSelections
            }
          )
          setSelectedNetlistFileName(userDataFromSavedProjectRes?.data?.project_details?.netlist_metadata?.fileName);
          if (selectedAction === 1) {
            projectFeatureSelection = ["layoutGeneration"];
            setSelectedFeature(["layoutGeneration"]);
            setIsUserInAction1EditFromViewProject(true);
            setSelectedGdsItems(userDataFromSavedProjectRes?.data?.project_details?.selectedLayouts)
          } else if (selectedAction === 3) {
            projectFeatureSelection = ["layoutGeneration", "layoutHyperexpressivity"];
            setSelectedFeature(["layoutGeneration", "layoutHyperexpressivity"]);
            setIsUserInAction3EditFromViewProject(true);
            let selectedLayouts = userDataFromSavedProjectRes?.data?.project_details?.selectedLayouts;
            setSelectedGdsItems(selectedLayouts);
            setIsGdsSelectAllChecked(selectedLayouts?.length === 0);
          }
          setTechFileData(userDataFromSavedProjectRes);
          setIsTechFileProjectSaved(true);
          setDefaultTechFileData(JSON.parse(JSON.stringify(userDataFromSavedProjectRes)))
          setSelectedTechFileName(userDataFromSavedProjectRes?.data?.project_details?.tech_metadata?.fileName);
          setSelectedNetlistFileType(userDataFromSavedProjectRes?.data?.project_details?.netlist_metadata?.netlistType);
          setSelectedTechFileType(userDataFromSavedProjectRes?.data?.project_details?.tech_metadata?.techType);
          navigate("/dashboard/netlist-file", {
            state: { projectName: projectNameInSavedProject, selectedFeatures: projectFeatureSelection, action: selectedAction },
          });
        }
        else if (selectedAction === 2) {
          projectFeatureSelection = ["layoutHyperexpressivity"];
          setSelectedFeature(["layoutHyperexpressivity"]);
          const stageOneProjectId = userDataFromSavedProjectRes?.data?.project_details?.stage_one_project;
          // Trigger API call. stage 1 and page 0
          //in action 2  current action2 project id itself gives data for stage1 for which it was created
          const stage1Res = await fetchStageData(currentProjectId, 1, 0);
          let selectedLayouts = userDataFromSavedProjectRes?.data?.project_details?.selectedLayouts;
          setSelectedGdsItems(selectedLayouts)
          setIsGdsSelectAllChecked(selectedLayouts?.length === 0);
          setStage1Result(stage1Res);
          setSelectedProjectIdFromList(stageOneProjectId);
          setSelectedProjectNameWithStage1Result(userDataFromSavedProjectRes?.data?.project_details?.stage_one_project_name);
          setSelectedNetlistFileName(userDataFromSavedProjectRes?.data?.project_details?.netlist_metadata?.fileName)
          setSelectedTechFileName(userDataFromSavedProjectRes?.data?.project_details?.tech_metadata?.fileName);
          setProjectDetailsSelectedForHyperExpressivityFlow(userDataFromSavedProjectRes?.data?.project_details);
          setActionSelected(selectedAction);
          setIsHyperExpressivityProjectSaved(true);
          setIsUserInAction2EditFromViewProject(true);
          navigate(`/dashboard/stage1result`, { state: { projectName: projectNameInSavedProject, selectedFeatures: projectFeatureSelection, action: selectedAction } })
        }
      }
    }
    catch (err) {
      toast.error(userDataFromSavedProjectRes?.message)
      console.error("Fetching the saved project data", err)
    }
  }, [
    setIsUserInAction1EditFromViewProject,
    setIsUserInAction2EditFromViewProject,
    setIsUserInAction3EditFromViewProject,
    setViewProjectModal,
    setIsUserInEditMode,
    currentProjectId,
    setNetlistCellInfo,
    setNetlistFileContent,
    setSelectedNetlistFileName,
    setSelectedNetlistFileType,
    setSelectedFeature,
    setSelectedTechFileName,
    setSelectedTechFileType,
    setTechFileData,
    setIsTechFileProjectSaved,
    setProjectDetailsSelectedForHyperExpressivityFlow,
    setStage1Result,
    setSelectedProjectNameWithStage1Result,
    setSelectedProjectIdFromList,
    setActionSelected,
    setIsHyperExpressivityProjectSaved,
    navigate,
    setSelectedGdsItems,
    setDefaultTechFileData,
    setTypeOfSelectedProject,
    setIsGdsSelectAllChecked,
    setDefaultNetlistFileData,
    setViewProjectTechFile
  ]);

  // function to handle click on list of running job
  const handleListOfRunningJob = async () => {
    try {
      const listOfRunningJobRes = await getListOfRunningJob(false);// sending showAllJobs as false since by default we dont want all jobs to be visible , only running jobs should be visible
      if (listOfRunningJobRes?.status === true) {
        setListOfRunningJobModal(true);
        setListOfRunningJobsData(listOfRunningJobRes);
      }
      else {
        setListOfRunningJobModal(true);
        setListOfRunningJobsData(listOfRunningJobRes?.response?.data);
      }
    }
    catch (error) {
      console.error("Fetching list of running jobs", error);
    }
  }

  // below function handles the click on view on running jobs modal
  const handleRunningJobViewButton = useCallback(async (jobId) => {
    if (listOfRunningJobsData && listOfRunningJobsData?.status === true) {
      const selectedProjectFromListOfRunningJobs = listOfRunningJobsData?.data?.find(job => job?.id === jobId)
      try {
        const userDataFromSavedProjectRes = await fetchUserDataFromSavedProject(selectedProjectFromListOfRunningJobs?.project?.id);
        if (userDataFromSavedProjectRes?.status === true) {
          let projectNameInRunningProject = selectedProjectFromListOfRunningJobs?.project?.project_name
          const selectedAction = selectedProjectFromListOfRunningJobs?.action;
          setActionSelected(selectedProjectFromListOfRunningJobs?.action);
          setRunLayoutJobId(selectedProjectFromListOfRunningJobs?.id);
          let projectFeatureSelection // This variable stores the selected feature from saved project 
          if (selectedAction === 1) {
            projectFeatureSelection = ["layoutGeneration"];
            setSelectedFeature(["layoutGeneration"]);
          }
          else if (selectedAction === 2) {
            projectFeatureSelection = ["layoutHyperexpressivity"];
            setSelectedFeature(["layoutHyperexpressivity"]);
            (userDataFromSavedProjectRes?.data?.project_details?.selectedLayouts?.length &&
              setSelectedGdsItems(userDataFromSavedProjectRes?.data?.project_details?.selectedLayouts)
            )
          }
          else if (selectedAction === 3) {
            projectFeatureSelection = ["layoutGeneration", "layoutHyperexpressivity"];
            setSelectedFeature(["layoutGeneration", "layoutHyperexpressivity"]);
          }
          setSelectedNetlistFileName(userDataFromSavedProjectRes?.data?.project_details?.netlist_metadata?.fileName)
          setSelectedTechFileName(userDataFromSavedProjectRes?.data?.project_details?.tech_metadata?.fileName)
          setRunningJobStatus(true);
          navigate("/dashboard/loader", {
            state: { projectName: projectNameInRunningProject, selectedFeatures: projectFeatureSelection, action: selectedAction },
          })
        }
        else {
          setListOfRunningJobModal(false);
          toast.error(userDataFromSavedProjectRes?.response?.data?.message);
        }
      }
      catch (error) {
        console.error("fetching user project details", error);
      }
    }
    else {
      toast.error(listOfRunningJobsData?.response?.data?.message);
    }
  }, [navigate, setRunningJobStatus, listOfRunningJobsData, setSelectedNetlistFileName, setSelectedTechFileName, setSelectedFeature, setActionSelected, setRunLayoutJobId, setSelectedGdsItems])

  // handling Running job modal button fuction
  const handleListOfRunningJobModalCancel = useCallback(() => {
    setListOfRunningJobModal(false);
    setListOfRunningJobsData();
  }, [setListOfRunningJobsData]);

  //function to handle click of view project 
  const handleViewProject = async () => {
    setViewProjectModal(true);
    const viewProjectList = await getProjectListForUser();
    setUserCreatedProjectList(viewProjectList);
  }

  //below function handles click of cancel on modal create project & feature
  const resetStateAndCloseModals = useCallback(() => {
    setIsUserInAction1EditFromViewProject(false);
    setIsUserInAction2EditFromViewProject(false);
    setIsUserInAction3EditFromViewProject(false);
    setInPreviousThroughHyperExpressivityProjectCreation(false);
    setStage1Result();
    setIsProjectSaved(false);
    setTechFileData();
    setCreateProjectModal(false);
    setProjectFeatureModal(false);
    setProjectName("");
    setCheckedItems({
      layoutGeneration: false,
      layoutHyperexpressivity: false,
    });
    setIsTechFileSelected(false);
    setSelectedTechFileName("");
    setIsNetListFileSelected(false);
    setSelectedNetlistFileName(null);
    setNetlistCellInfo();
    setNetlistFileContent();
    setSelectedNetlistFileType();
    //making all state stored in location to be removed
    navigate("/home", { replace: true });
    setIsSelectAllChecked(false);
    setIsUserInEditMode(false);
    setViewProjectListFileSelectedInModal(false);
    setIsProjectWithStage1ResultSelectedFromList(false);
    setIsHyperExpressivityProjectSaved(false);
    setCurrentProjectId();
    setSelectedProjectNameFromStage1ListRow();
    setSelectedProjectNameWithStage1Result();
    setTypeOfSelectedProject(0);
    setTypeOfProjectCreationSelectedInModal(false);
    setSelectProjectOptionModal(false);
    setIsProjectStillRunning(false);
    resetContext();
  }, [setIsProjectStillRunning, resetContext, navigate, setCurrentProjectId, setInPreviousThroughHyperExpressivityProjectCreation, setIsHyperExpressivityProjectSaved, setIsNetListFileSelected, setIsProjectSaved, setIsProjectWithStage1ResultSelectedFromList, setIsSelectAllChecked, setIsTechFileSelected, setIsUserInAction1EditFromViewProject, setIsUserInAction2EditFromViewProject, setIsUserInAction3EditFromViewProject, setIsUserInEditMode, setNetlistCellInfo, setNetlistFileContent, setSelectedNetlistFileName, setSelectedNetlistFileType, setSelectedProjectNameWithStage1Result, setSelectedTechFileName, setStage1Result, setTechFileData, setTypeOfSelectedProject]);

  const handleNextFromPreviousHyperFlow = async () => {
    const projectCheckRes = await handleCreateNewProjectClick();
    if (projectCheckRes) {
      setProjectFeatureModal(false);
      const projectWithStage1ResultsRes = await getProjectWithStage1ResultsForUser();
      setProjectListWithStage1Result(projectWithStage1ResultsRes); //setting projectlist having stage1 data in context
      navigate("/dashboard/stage1result", {
        state: { projectName, selectedFeatures: selectedFeature, action:2, nextButtonClicked: true },
      });
    }
  };

  // this gives the data of the selected project
  useEffect(() => {
    if (userCreatedProjectList && selectedFileNameFromListOfSavedProject) {
      const selectedProjectFile = userCreatedProjectList?.data?.filter(project => project?.project_name === selectedFileNameFromListOfSavedProject);
      setCurrentProjectId(selectedProjectFile[0]?.id);
    }
  }, [userCreatedProjectList, selectedFileNameFromListOfSavedProject, setCurrentProjectId])

  useEffect(() => {
    if (initialProjectFeatureModal) {
      setProjectFeatureModal(true);
    }
  }, [initialProjectFeatureModal]);

  //useeffect checks if create project modal is sent as true
  useEffect(() => {
    if (initialCreateProjectModal) {
      setCreateProjectModal(true);
    }
  }, [initialCreateProjectModal]);

  //below use effect handles opening of project list with stage1 result modal
  useEffect(() => {
    if (
      (location?.state?.isHyperexpressivityModalOpen ||
        isHyperexpressivityModalOpen) &&
      projectListWithStage1Result
    ) {
      setIsHyperexpressivityModalOpen(true);
      setHyperexpressivityProjectListModalContent({
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
            <span>
              <Button
                id="ok-button-stage1projectlist-hyperexpressivity-flow"
                className={`col-4 m-2 ${isProjectWithStage1ResultSelectedInModal ? "app-primary-button-color border-0" : ""} `}
                disabled={!isProjectWithStage1ResultSelectedInModal}
                onClick={handleOkClickOnProjectListWithStage1ResultModal}
                data-tooltip-id="tooltip-loadlayout-okButton"
                data-tooltip-content="Select project to proceed ahead."
                data-tooltip-place="top"
              >
                Ok
              </Button>
            </span>
            {(
              !isProjectWithStage1ResultSelectedInModal ? ["hover"] : []
            ) && (<ReactTooltip id="tooltip-loadlayout-okButton" style={{ zIndex: 9999 }} />)}
            <Button
              id="cancel-button-stage1projectlist-hyperexpressivity-flow"
              onClick={handleCloseHyperexpressivityProjectList}
              className="col-4 m-2 app-secodary-button-color"
            >
              Cancel
            </Button>
          </>
        ),
      });
    }
  }, [
    isHyperexpressivityModalOpen,
    actionSelected,
    projectListWithStage1Result,
    location,
    currentProjectId,
    handleCloseHyperexpressivityProjectList,
    navigate,
    isProjectWithStage1ResultSelectedInModal,
    handleOkClickOnProjectListWithStage1ResultModal,
    handleStateSetForProjectSelection,
  ]);

  // below use effect handles opening of project list with view project modal
  useEffect(() => {
    //if view project modal is true then set body for modal
    if (viewProjectModal && userCreatedProjectList !== null) {
      setViewProjectListdata({
        title: "Choose a Project",
        body: (
          <ViewProjectResult
            viewProjectResultList={userCreatedProjectList?.data}
            handleViewProjectModalSelectedInModal={
              handleViewProjectModalSelectedInModal
            }
            setSelectedFileNameFromListOfSavedProject={
              setSelectedFileNameFromListOfSavedProject
            }
          />
        ),
        footer: (
          <>
            <span>
              <Button
                id="ok-button-viewProjectList"
                className={`col-4 m-2 w-25 ${viewProjectListFileSelectedInModal && (projectVersion === currentVersion || projectVersion > currentVersion)
                  ? "app-primary-button-color border-0"
                  : "app-secondary-button-color border-0 cursor_not_allowed"
                  }`}
                onClick={handleViewProjectSelection}
                disabled={!viewProjectListFileSelectedInModal || (projectVersion !== currentVersion || currentVersion > projectVersion)}
                data-tooltip-id="tooltip-projectlist-OkButton"
                data-tooltip-content={
                  !viewProjectListFileSelectedInModal
                    ? "Select one project from above list to proceed ahead."
                    : (currentVersion !== projectVersion || currentVersion > projectVersion) &&
                      "Project is incompatible."
                }
                data-tooltip-place="top"
              >
                Ok
              </Button>
              {(!viewProjectListFileSelectedInModal || (currentVersion !== projectVersion || currentVersion > projectVersion)) && (<ReactTooltip id="tooltip-projectlist-OkButton" style={{ zIndex: 9999 }} />)}
            </span>
            <Button
              id="cancel-button"
              onClick={handleCloseViewProject}
              className="col-4 m-2 w-25 app-secondary-button-color border-0 "
            >
              Cancel
            </Button>
            <Button
              id="delete-project-button"
              className={` w-25 border-0 ${viewProjectListFileSelectedInModal ? "" : " cursor_not_allowed"
                }`}
              disabled={!viewProjectListFileSelectedInModal}
              onClick={handleDeleteProject}
              data-tooltip-id="tooltip-projectlist-delete-button"
              data-tooltip-content="Select one project from above list to Delete the file."
              data-tooltip-place="top"
            >
              Delete
            </Button>
            {(!viewProjectListFileSelectedInModal) && (<ReactTooltip id="tooltip-projectlist-delete-button" style={{ zIndex: 9999 }} />)}
          </>
        ),
      });
    }
  }, [
    viewProjectModal,
    userCreatedProjectList,
    viewProjectListFileSelectedInModal,
    handleViewProjectSelection,
    handleCloseViewProject,
    setSelectedFileNameFromListOfSavedProject,
    projectVersion,
    handleViewProjectModalSelectedInModal,
    currentVersion
  ]);

  // below use effect handles opening of creation of project selection modal open
  useEffect(() => {
    //if project selection modal is true then set body for modal to give user option to select project creation option
    if (selectProjectOptionModal) {
      setTypeOfProjectCreationSelectionModalBody({
        title: "Select Project Type",
        body: (<CreateProjectTypeSelectionModalBody handleProjectCreationTypeSelection={handleProjectCreationTypeSelection} />),
        footer: (
          <>

            <Button
              id="previous-button-select-project-type-modal"
              onClick={() => { setCreateProjectModal(true); setSelectProjectOptionModal(false); setTypeOfSelectedProject(0) }}
              className="col-3 m-2 app-primary-button-color border-0"
            >
              Previous
            </Button>

            <Button
              id="cancel-button-select-project-type-modal"
              onClick={resetStateAndCloseModals}
              className="col-3 m-2 app-secondary-button-color border-0"
            >
              Cancel
            </Button>
            <Button
              id="ok-button-project-type-selection"
              className={`col-3 m-2 ${typeOfProjectCreationSelectedInModal
                ? "app-primary-button-color border-0"
                : "app-secondary-button-color border-0 cursor_not_allowed"
                }`}
              onClick={() => { setProjectFeatureModal(true) }} //also set ehich poc feature is selected here
              disabled={!typeOfProjectCreationSelectedInModal}
              data-tooltip-id="tooltip-projectlist-OkButton"
              data-tooltip-content="Select one project type from above list to proceed ahead."
              data-tooltip-place="top"
            >
              Next
            </Button>
            {(!typeOfProjectCreationSelectedInModal) && (<ReactTooltip id="tooltip-projectlist-OkButton" style={{ zIndex: 9999 }} />)}

          </>
        ),
      });
    }
  }, [setTypeOfSelectedProject, selectProjectOptionModal, handleProjectCreationTypeSelection, typeOfProjectCreationSelectedInModal, resetStateAndCloseModals]);

  // below use effect handles opening of list of running jobs with running jobs modal
  useEffect(() => {
    if (listOfRunningJobModal && listOfRunningJobsData !== null) {
      setRunningJobListData({
        title: "List of Running Jobs",
        body: (
          <RunningJobModalBody listOfRunningJobsData={listOfRunningJobsData} handleRunningJobViewButton={handleRunningJobViewButton} />
        ),
        footer: (
          <Button id="list-of-running-job-cancel-button" onClick={handleListOfRunningJobModalCancel} className="col-4 m-2 app-secondary-button-color border-0" >Cancel</Button>
        )
      })
    }
  }, [setRunningJobListData, listOfRunningJobModal, listOfRunningJobsData, handleRunningJobViewButton, handleListOfRunningJobModalCancel])

  return (
    <>
      <ToastContainer
        closeButton={true}
        position="top-center"
        autoClose={false}
        theme="colored"
      />
      <div className="container-fluid d-flex flex-column justify-content-center align-items-center" id="background-img">
        <div className="w-100 d-flex justify-content-center align-items-center mt-3" style={{ height: "60vh", overflow: 'hidden' }}>
          <Carousel className="w-100 h-100" interval={2000}>
            <Carousel.Item>
              <img
                className="d-block mx-auto w-75 h-100"
                src={CarouselImage1}
                alt="First slide"
                style={{ objectFit: 'contain' }}
              />
            </Carousel.Item>
            <Carousel.Item>
              <img
                className="d-block mx-auto w-75 h-100"
                src={CarouselImage2}
                alt="Second slide"
                style={{ objectFit: 'contain' }}
              />
            </Carousel.Item>
            <Carousel.Item>
              <img
                className="d-block mx-auto w-75 h-100"
                src={CarouselImage3}
                alt="Third slide"
                style={{ objectFit: 'contain' }}
              />
            </Carousel.Item>
          </Carousel>
        </div>
        <div className="row d-flex align-items-center text-center w-100 pt-3 mb-2" style={{ height: "40vh", overflow: 'hidden' }}>
          <div className="col-12 col-md-4 mb-3 d-flex align-items-center h-100">
            <button
              onClick={handleCreateProjectClick}
              id="create-project-btn"
              className="w-100 h-75 rounded-3 app-secondary-color cursor_pointer"
              // style={{ height: "60%" }}
            >
              <img src={Working} alt="create-project" />
              <br />
              <span className="text-black">Create Projects</span>
            </button>
          </div>
          <div className="col-12 col-md-4 mb-3 d-flex align-items-center h-100">
            <button
              id="running-jobs-btn"
              className="w-100 h-75 app-secondary-color rounded-3 cursor_pointer"
              // style={{ height: "60%" }}
              onClick={handleListOfRunningJob}
            >
              <img src={View} alt="view-project" />
              <br />
              <span className="text-black">View Running/Queued Jobs</span>
            </button>
          </div>
          <div className="col-12 col-md-4 mb-3 d-flex align-items-center h-100">
            <button
              onClick={handleViewProject}
              id="view-edit-project-btn"
              // style={{ height: "60%" }}
              className="w-100 h-75 app-secondary-color rounded-3 cursor_pointer"
            >
              <img src={Edit} alt="view-edit-delete-project" />
              <br />
              <span className="text-black">View/Edit/Delete Projects</span>
            </button>
          </div>
        </div>
      </div>


      <Footer />
      {/* create project modal */}
      <Modal
        id="create-project-modal"
        backdrop="static"
        keyboard={false}
        show={createProjectModal}
        onHide={resetStateAndCloseModals}
        centered
        size="lg"
        animation={false}
        className="modal-style overflow-hidden modal-fade-in-bottom"
      >
        <Modal.Header closeButton>
          <Modal.Title>Create a New Project</Modal.Title>
        </Modal.Header>
        <Modal.Body className="d-flex align-items-center justify-content-center">
          <CreateProjectModalBody
            projectName={projectName}
            setProjectName={setProjectName}
            projectNameError={projectNameError}
            setProjectNameError={setProjectNameError}
            handleCreateNewProjectClick={handleCreateNewProjectClick}
            handleCreatePOCProjectType={handlePOCProjectCreationClick}
          />
        </Modal.Body>
        <Modal.Footer className="d-flex justify-content-center">
          <Button
            onClick={resetStateAndCloseModals}
            className="col-3 app-secondary-button-color border-0 "
          >
            Cancel
          </Button>
          {/* next button is only visible on modal when user lands on this modal through previous button on hyper expressivity flow. */}
          {inPreviousThroughHyperExpressivityProjectCreation && (
            <>
              <Button
                onClick={handleNextFromPreviousHyperFlow}
                className={`col-3 ${!projectName || projectNameError ? "app-secondary-button-color border-0  cursor_not_allowed" : "app-primary-button-color border-0 "}`}
                disabled={!projectName || projectNameError}
                data-tooltip-id="next-button-on-createproject-modal"
                data-tooltip-content={"Please enter valid project name to proceed ahead."}
              >
                Next
              </Button>

              {(!projectName || projectNameError) && <ReactTooltip id="next-button-on-createproject-modal" place="top" style={{ width: "260px", zIndex: 9999 }} />}
            </>
          )}
        </Modal.Footer>
      </Modal>

      <Modal
        id="project-feature-modal"
        backdrop="static"
        keyboard={false}
        show={projectFeatureModal}
        onHide={resetStateAndCloseModals}
        centered
        size="lg"
        animation={false}
        className="modal-style overflow-hidden modal-fade-in-bottom"
      >
        <Modal.Header closeButton>
          <Modal.Title>Select Project Features</Modal.Title>
        </Modal.Header>
        <Modal.Body className="d-flex align-items-center justify-content-center">
          <ProjectFeatureModalBody
            checkedItems={checkedItems}
            handleCheckboxChange={handleCheckboxChange}
          />
        </Modal.Body>
        <Modal.Footer className="d-flex justify-content-center gap-2">
          <Button
            id="previous-button"
            onClick={() => {
              setProjectFeatureModal(false);
              setCreateProjectModal(true);

            }}
            className={`col-3 ${isProjectSaved || isUserInEditMode ? "app-secondary-button-color border-0  cursor_not_allowed" : "app-primary-button-color border-0 "
              }`}
            disabled={isProjectSaved || isUserInEditMode}
          >
            Previous
          </Button>
          <Button
            id="cancel-button"
            onClick={resetStateAndCloseModals}
            className="col-3 app-secondary-button-color border-0 "
          >
            Cancel
          </Button>
          <Button
            id="next-button"
            onClick={handleSubmit}
            className={`col-3 ${isNextButtonDisabled ? "app-secondary-button-color border-0  cursor_not_allowed" : "app-primary-button-color border-0 "
              }`}
            disabled={isNextButtonDisabled}
            data-tooltip-id="tooltip-projectFeature-NextButton"
            data-tooltip-content="Please select atleast one feature to proceed next."
            data-tooltip-place="top"
          >
            Next
          </Button>
          {(isNextButtonDisabled) && (<ReactTooltip id="tooltip-projectFeature-NextButton" style={{ width: "200px", zIndex: 9999 }} />)}
        </Modal.Footer>
      </Modal>
      {/* Modal which will display project creation options i.e normal or poc project creation option */}
      <ModalComponent
        id={"typeof-project-creation-selection-modal"}
        show={selectProjectOptionModal}
        handleClose={handleCancelProjectTypeSelection}
        modalContent={typeOfProjectCreationSelectionModalBody}
        bodyClassName={"p-3 pt-0 overflow-auto"}
      />
      {/* modal for showing list of user projects having stage1 results , shown when user is in only hyperexpressivity creation flow */}
      <ModalComponent
        id={"projectlist-with-stage1-result-modal"}
        show={isHyperexpressivityModalOpen}
        handleClose={handleCloseHyperexpressivityProjectList}
        modalContent={hyperexpressivityProjectListModalContent}
        bodyClassName={"p-3 pt-0 overflow-auto"}
      />
      {/* user view project modal, show the list of project that have the results*/}
      <ModalComponent
        id={"view-project-list-modal"}
        show={viewProjectModal}
        handleClose={handleCloseViewProject}
        modalContent={viewProjectListdata}
        bodyClassName={"p-3 pt-0 overflow-auto"}
      />
      {/* Modal which shows list of running job */}
      <ModalComponent
        id={"list-of-running-jobs-modal"}
        show={listOfRunningJobModal}
        handleClose={handleListOfRunningJobModalCancel}
        modalContent={runningJobListData}
        bodyClassName={"p-3 pt-0 overflow-auto"}
      />
      {/* Delete project Modal */}
      <ModalComponent
        id={"delete-project-modal"}
        size="md"
        show={deleteProjectModal}
        handleClose={() => { setDeleteProjectModal(false) }}
        modalTitleCSSClass={{ color: '#910303' }}
        modalContent={deleteProjectModalContent}
        modalCSSClass={"overflow-hidden"}
      />
    </>
  );


};

export default LandingPage;
