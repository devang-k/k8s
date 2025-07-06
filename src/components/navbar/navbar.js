
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: navbar.js  
 * Description: This file is responsible to show navigation bar in all pages 
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

import React, { useEffect, useRef, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import Logo from "../../Assets/Images/Logo.svg";
import Circuit from "../../Assets/Images/networkwired.svg"
import Diagram from "../../Assets/Images/microchip.svg"
import { blackListTokenApi } from "../../server/server";
import "./navbar.css";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faUser, faHouse, faArrowRightFromBracket, faGear, faCircleInfo, faCircleUser } from "@fortawesome/free-solid-svg-icons";
import { Tooltip as ReactTooltip } from "react-tooltip";
import About from "../About/About";
import { Link } from 'react-router-dom';
import { useTechFileContext } from '../providers/TechFileProvider/TechFileContext';
import { useNetListFileContext } from '../providers/NetListFileProvider/NetListFileContext';
import { useCreateProjectContext } from "../providers/CreateProjectProvider/CreateProjectContext";
import { useEditProjectContext } from "../providers/EditProjectProvider/EditProjectContext";
import { useStage1ResultContext } from "../providers/Stage1ResultProvider/Stage1ResultContext";
import { useRunProjectContext } from "../providers/RunProjectProvider/RunProjectContext";
import { useStage2ResultContext } from "../providers/Stage2ResultProvider/Stage2ResultContext";
import { useLayoutGraphContext } from '../providers/LayoutGraphProvider/LayoutGraphContext';
import { useFilterResultsContext } from '../providers/FilterResultsProvider/FilterResultsContext';
import { useAdminContext } from "../providers/AdminProvider/AdminContext";
import { projectTypeLookup } from '../../constant';
import ModalComponent from "../utils/Modal/ModalComponent";
import { productName } from "../../constant";


const NavBar = () => {
  const location = useLocation();
  const { selectedFeatures } = location.state || {};
  const { actionSelected } = useNetListFileContext();
  const [viewAboutModel, setViewAboutModel] = useState(false);
  const { isUserOnStage2Page } = useStage2ResultContext();
  const { clearFilterResultsContext } = useFilterResultsContext();
  const [userMenu, setUserMenu] = useState(false);
  const dropdownRef = useRef(null);
  const [showModal, setShowModal] = useState(false);
  const [modalContent, setModalContent] = useState({});
  const refreshToken = localStorage.getItem("refresh-token");
  const isAdmin = localStorage.getItem("isAdmin") === "true";
  const isAdminSettingPage = location.pathname.startsWith("/admin-settings");
  const username = localStorage.getItem("username");
  const navigate = useNavigate();
  const { setIsTechFileSelected, setSelectedTechFileName, setTechFileData, setSelectedTechFileType, setIsTechDataChanged, setViewProjectTechFile, setProjectTechFileListData, setIsTechFileProjectSaved } = useTechFileContext();
  const { setActionSelected, setNetListFileData, setIsNetListFileSelected, setSelectedNetlistFileName, setSelectedNetlistFileType, setNetlistCellInfo, setNetlistFileContent, setIsSelectAllChecked, setIsNetlistDataChanged } = useNetListFileContext();
  const { setIsUserInEditMode, setUserCreatedProjectList, setIsButtonDisabledInEditMode, setShowResultButtonInStage1ResultInEditMode, setShowResultButtonInTechFileInEditMode } = useEditProjectContext();
  const { setStage1Result, setSelectedGdsItems, setStage1CellInfo, setIsGdsSelectAllChecked, setStage1GdsLayoutImageData } = useStage1ResultContext()
  const { setStage2Result, setIsUserOnStage2Page, setStage2GdsLayoutImageData } = useStage2ResultContext()
  const { setIsProjectStillRunning, webSocketObj, setIsRunningJobCompleted, setRunLayoutRunningJobLogs, setIsRunningJobErrored, setRunLayoutJobId, setListOfRunningJobsData, setRunningJobStatus } = useRunProjectContext();
  const { setAdminNetlistFileData, setUserNetlistFileContent, setAdminTechFileData, setUserTechFileContent } = useAdminContext();
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
    typeOfSelectedProject,
  } = useCreateProjectContext();
  const { setStage1GraphData, setStage2GraphData } = useLayoutGraphContext();

  const resetStateAndCloseModals = () => {
    if (webSocketObj) {
      webSocketObj.close();
    }
    setIsUserInAction1EditFromViewProject(false);
    setIsUserInAction2EditFromViewProject(false);
    setIsUserInAction3EditFromViewProject(false);
    setIsUserOnStage2Page(false)
    setStage2Result()
    setProjectDetailsSelectedForHyperExpressivityFlow()
    setSelectedProjectIdFromList()
    setProjectListWithStage1Result([])
    setSelectedFeature([])
    setProjectName()
    setRunLayoutJobId(null)
    setIsRunningJobErrored(false)
    setStage1CellInfo(null)
    setSelectedGdsItems()
    setUserCreatedProjectList()
    setActionSelected(1)
    setNetListFileData()
    setSelectedTechFileType()
    setInPreviousThroughHyperExpressivityProjectCreation(false);
    setStage1Result();
    setTechFileData();
    setIsTechFileSelected(false);
    setSelectedTechFileName("");
    setIsNetListFileSelected(false);
    setNetlistCellInfo();
    setNetlistFileContent();
    setSelectedNetlistFileType();
    setIsProjectWithStage1ResultSelectedFromList(false);
    setIsHyperExpressivityProjectSaved(false);
    setIsUserInEditMode(false);
    setSelectedNetlistFileName();
    setIsProjectSaved(false);
    setIsSelectAllChecked(false);
    setSelectedProjectNameWithStage1Result();
    setCurrentProjectId();
    setRunLayoutRunningJobLogs([]);
    setIsRunningJobCompleted(false);
    setIsButtonDisabledInEditMode(false);
    setAdminNetlistFileData();
    setIsNetlistDataChanged(false);
    setIsTechDataChanged(false);
    setUserNetlistFileContent();
    setListOfRunningJobsData(null);
    setRunningJobStatus(false);
    setAdminTechFileData();
    setUserTechFileContent();
    setShowResultButtonInStage1ResultInEditMode(false);
    setShowResultButtonInTechFileInEditMode(false);
    setTypeOfSelectedProject(0);
    setStage1GraphData(null);
    setStage2GraphData(null);
    setIsProjectStillRunning(false);
    setIsGdsSelectAllChecked(false);
    setStage1GdsLayoutImageData([]);
    setStage2GdsLayoutImageData([]);
    clearFilterResultsContext();
    setViewProjectTechFile(false);
    setProjectTechFileListData();
    setIsTechFileProjectSaved(false);
  };

  const handleLogout = async () => {
    await blackListTokenApi(refreshToken);
    localStorage.removeItem("access-token");
    localStorage.removeItem("refresh-token");
    sessionStorage.setItem("loggedOut", "true");
    localStorage.removeItem("isAdmin");
    localStorage.removeItem("username");
    setUserMenu(false);
    navigate("/");
    //window.location.reload();  //Instead of this we are clearing context on Logout.
    resetStateAndCloseModals()
  };

  // Handle clicks outside of the dropdown
  const handleClickOutside = (event) => {
    if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
      setUserMenu(false);
    }
  };
  useEffect(() => {
    // Add event listener for clicks
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Render nothing for the home page
  if (location.pathname === "/") {
    return null;
  }

  // To check active path 
  const checkActivePathName = () => {
    const pathSegments = location.pathname.split('/').filter(Boolean);
    return pathSegments.length > 0 ? pathSegments[0] : '';
  };

  const handleNavigationConfirmation = (targetPage, isLogout = false) => {
    const activePath = checkActivePathName();

    // avoiding popup on this paths
    if (activePath === "" || activePath === "home" || activePath === "user-profile" || activePath === "admin-settings") {
      if (isLogout) {
        return handleLogout();
      }
      return navigate(targetPage);
    }

    setModalContent({
      title: "Warning",
      body: <h6>The current project will be closed, and the changes may be lost. Do you want to proceed?</h6>,
      footer: (
        <div>
          <button
            className="btn app-primary-button-color text-white border-0 me-2 w-25 "
            id="user-warning-yes-button"
            onClick={async () => {
              resetStateAndCloseModals();
              setShowModal(false);
              if (isLogout) {
                await handleLogout();
              } else {
                navigate(targetPage);
              }
            }}>
            Yes
          </button>
          <button
            className="btn app-secondary-button-color text-white border-0  w-25 "
            id="user-warning-no-button"
            onClick={handleModalClose}
          >
            No
          </button>
        </div>
      ),
    });
    setShowModal(true);
  };

  const handleModalClose = () => {
    setShowModal(false);
  };

  const handleShow = () => {
    setViewAboutModel(true);
  };

  const handleClose = () => {
    setViewAboutModel(false);
  };


  return (
    <>
      <nav className="navbar app-primary-color text-light py-0 h-auto">
        <div className="container-fluid d-flex flex-wrap justify-content-between align-items-center">
          {/* Logo Section */}
          <div className="d-flex align-items-center justify-content-center justify-content-md-start logo-section">
            <span className="navbar-brand d-flex align-items-center ms-md-3">
              <img src={Logo} alt="logo" height="30" className="me-2" />
            </span>
            {/* Product Name */}
            <div
              style={{
                fontFamily: "monospace",
                fontWeight: "bold",
                fontSize: "18px",
                marginRight: "15px"
              }}
            >
              {productName}
            </div>
            {(isAdmin && isAdminSettingPage) || location?.pathname === "/home/user-profile" ? (
              <button
                className="text-white app-primary-color border-0 mr-1"
                type="button"
                id="home-navigator"
                onClick={() => navigate('/home')}
              >
                <FontAwesomeIcon icon={faHouse} style={{ fontSize: '20px' }} />
              </button>
            ) : null}
            {isAdmin && isAdminSettingPage && location?.pathname !== "/admin-settings/adminDashboard" && (
              <button
                className="text-white app-primary-color border-0 mr-1"
                type="button"
                id="Settings-navigator"
                onClick={() => navigate('/admin-settings/adminDashboard')}
              >
                <FontAwesomeIcon icon={faGear} style={{ fontSize: '20px' }} />
              </button>
            )}
          </div>

          {/* Project Name Section */}
          <div className="d-none d-sm-flex justify-content-center align-items-center my-2 my-md-0 flex-grow-1">
            <div className="navbar-content d-flex gap-3 justify-content-center w-100 text-center">
              {selectedFeatures?.map((feature) =>
                feature.startsWith("layout") ? (
                  <div key={feature} className="step-item">
                    {actionSelected !== 3 ? (
                      <span className={`text-primary py-2 px-2 text-center rounded justify-content-center ${actionSelected && "bg-white text-dark"}`} style={{ minWidth: '200px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                        {actionSelected === 1 ? (
                          <>
                            <img src={Circuit} width={25} alt="Circuit" />
                            {feature.replace(/([A-Z])/g, " $1").replace(/^./, (str) => str.toUpperCase())}
                          </>
                        ) : (
                          <>
                            <img src={Diagram} width={25} alt="Diagram" />
                            {feature.replace(/([A-Z])/g, " $1").replace(/^./, (str) => str.toUpperCase())}
                          </>
                        )}
                      </span>
                    ) : (
                      <div className="dual-text d-flex">
                        {feature === "layoutGeneration" && (
                          <span
                            className={`flex-fill p-2 rounded  d-flex justify-content-center align-items-center gap-2 ${!isUserOnStage2Page && "bg-white text-dark"}`}
                            style={{ minWidth: '200px' }}
                          >
                            <img src={Circuit} width={25} alt="Circuit" />
                            {feature.replace(/([A-Z])/g, " $1").replace(/^./, (str) => str.toUpperCase())}
                          </span>
                        )}
                        {feature === "layoutHyperexpressivity" && (
                          <span
                            className={`flex-fill p-2 rounded d-flex align-items-center gap-2 ${isUserOnStage2Page && "bg-white text-dark"}`}
                            style={{ minWidth: '200px' }}
                          >
                            <img src={Diagram} width={25} alt="Diagram" />
                            {feature.replace(/([A-Z])/g, " $1").replace(/^./, (str) => str.toUpperCase())}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                ) : null
              )}
            </div>
          </div>

          {/* User Dropdown Section */}
          <div className="d-flex align-items-center justify-content-end flex-grow-1 gap-2">
            <div>
              {projectTypeLookup[typeOfSelectedProject] !== " " && (
                <div
                  className="text-primary bg-white py-2 px-2 text-center rounded me-2"
                >
                  {projectTypeLookup[typeOfSelectedProject]}
                </div>
              )}
            </div>

            <div>
              <h6
                className="mb-0 me-3 text-white align-items-center d-flex"
                style={{ maxWidth: "150px" }}
                id="navbar-user-name"
                data-tooltip-id="tooltip-userName"
                data-tooltip-content={username}
                data-tooltip-place="bottom"
              >
                <span className="text-truncate">{username}</span>
              </h6>
            </div>
            <ReactTooltip id="tooltip-userName" style={{ zIndex: 9999 }} />
            <div className="dropdown" ref={dropdownRef}>
              <button
                className="btn text-light dropdown-toggle "
                type="button"
                id="user-menu-button"
                aria-expanded={userMenu ? "true" : "false"}
                onClick={() => setUserMenu((prev) => !prev)}
              >
                <FontAwesomeIcon icon={faUser} className="user-icon" />
              </button>
              <ul
                className={`dropdown-menu dropdown-menu-end cursor_pointer ${userMenu ? "show" : ""
                  }`}
                aria-labelledby="userMenuButton"
                style={{ right: "5px" }}
              >
                <li className="dropdown-item d-flex align-items-center"
                  onClick={() => handleNavigationConfirmation("/home/user-profile")}
                  id="profile-button-navbar"
                >
                  <FontAwesomeIcon icon={faCircleUser} className="me-2" style={{ fontSize: '16px' }} />
                  Profile
                </li>
                <li
                  id="about-versions"
                  className="dropdown-item d-flex align-items-center text-dark "
                  onClick={() => handleShow()}  // Added onClick here
                >
                  <FontAwesomeIcon
                    icon={faCircleInfo}
                    className="me-2"
                    style={{ fontSize: '16px' }}
                  />
                  <span>About</span>
                </li>

                {isAdmin && (
                  <Link
                    id="admin-settings"
                    to="/admin-settings/adminDashboard"
                    onClick={(e) => {
                      e.preventDefault();
                      handleNavigationConfirmation("/admin-settings/adminDashboard");
                    }}
                    className="dropdown-item text-dark d-flex align-items-center"
                  >
                    <FontAwesomeIcon icon={faGear} className="me-2" style={{ fontSize: '16px' }} />
                    Settings
                  </Link>
                )}
                <li
                  className="dropdown-item d-flex align-items-center"
                  onClick={() => handleNavigationConfirmation(null, true)}
                  id="logout-button-navbar"
                >
                  <FontAwesomeIcon icon={faArrowRightFromBracket} className="me-2" style={{ fontSize: '16px' }} />
                  Logout
                </li>
              </ul>
            </div>
          </div>
        </div>
      </nav>
      <ModalComponent
        id="warning-modal"
        size="md"
        show={showModal}
        handleClose={handleModalClose}
        modalContent={modalContent}
        modalCSSClass={"overflow-hidden"}
      />
      {/* Pass handleClose and viewAboutModel as props to About component */}
      <About
        showAboutModel={viewAboutModel}
        handleCloseModel={handleClose}
      />

    </>
  );
};

export default NavBar;