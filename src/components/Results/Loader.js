
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: Loader.js  
 * Description: This file is responsible to show loading spinner till result is getting generate 
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
import { webSocketHostName } from "../../constant";
import { useNavigate, useOutletContext, useLocation } from "react-router-dom";
import { Button } from "react-bootstrap";
import { ToastContainer, toast } from "react-toastify";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faXmark } from "@fortawesome/free-solid-svg-icons";
import { useCreateProjectContext } from "../providers/CreateProjectProvider/CreateProjectContext";
import { useNetListFileContext } from "../providers/NetListFileProvider/NetListFileContext";
import { useTechFileContext } from "../providers/TechFileProvider/TechFileContext";
import { fetchStageData, getJobDetailsOfJobID } from "../../server/server";
import { useStage1ResultContext } from "../providers/Stage1ResultProvider/Stage1ResultContext";
import { useStage2ResultContext } from "../providers/Stage2ResultProvider/Stage2ResultContext";
import { useRunProjectContext } from "../providers/RunProjectProvider/RunProjectContext";
import { useEditProjectContext } from "../providers/EditProjectProvider/EditProjectContext";
import { useLayoutGraphContext } from "../providers/LayoutGraphProvider/LayoutGraphContext";
import { Tooltip as ReactTooltip } from "react-tooltip";

const Loader = () => {
    const { setSidebarContent } = useOutletContext();
    const { setStage1Result, setSelectedGdsItems, selectedGdsItems, setStage1RunResultSummaryData, setStage1GdsLayoutImageData ,setStage1TotalGDSNumber} = useStage1ResultContext();
    const { setStage2Result, isUserOnStage2Page, setIsUserOnStage2Page, setStage2RunResultSummaryData, setStage2GdsLayoutImageData ,setStage2TotalGDSNumber } = useStage2ResultContext();
    const { setStage1GraphData, setStage2GraphData } = useLayoutGraphContext();
    const [isApiResultLoading, setIsApiResultLoading] = useState(false);
    const { setIsButtonDisabledInEditMode, setIsUserInEditMode, setShowResultButtonInStage1ResultInEditMode, setShowResultButtonInTechFileInEditMode } = useEditProjectContext();
    const {
        currentProjectId,
        setCurrentProjectId,
        setIsProjectSaved,
        setIsHyperExpressivityProjectSaved,
        setSelectedProjectNameWithStage1Result,
        setIsProjectWithStage1ResultSelectedFromList,
        setSelectedProjectIdFromList,
        setIsUserInAction3EditFromViewProject,
        setIsUserInAction2EditFromViewProject,
        setIsUserInAction1EditFromViewProject,
        setInPreviousThroughHyperExpressivityProjectCreation,
        setTypeOfSelectedProject,
        setIsStage1RunResultPresent,
        setIsStage2RunResultPresent,

    } = useCreateProjectContext();
    const {
        selectedNetlistFileName,
        setNetlistFileContent,
        setIsNetListFileSelected,
        setNetlistCellInfo,
        setSelectedNetlistFileName,
        setSelectedNetlistFileType,
        setIsSelectAllChecked,
        setIsNetlistDataChanged,
        actionSelected,
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
    const { webSocketObj, setRunLayoutJobId, setWebSocketObj, runLayoutJobId, isRunningJobCompleted, setIsRunningJobCompleted, setRunLayoutRunningJobLogs, isRunJobErrored, setIsRunningJobErrored, runningJobStatus, setRunningJobStatus,setIsProjectStillRunning,isProjectStillRunning } = useRunProjectContext();
    const location = useLocation();
    const { projectName, selectedFeatures, action } = location.state || {};
    let navigate = useNavigate();

    const handlePreviousButton = useCallback(() => {
        if (action === 1) {
            setIsRunningJobErrored(false);
            navigate(`../techfiles`, {
                state: { projectName, selectedFeatures, action },
            });
        } else if (action === 2) {
            setIsRunningJobErrored(false);
            navigate(`../stage1result`, { state: { projectName, selectedFeatures, action } });
        } else if (action === 3) {
            setIsRunningJobErrored(false);
            if (isUserOnStage2Page) {
                setIsUserOnStage2Page(false);
                navigate(`../stage1result`, { state: { projectName, selectedFeatures, action } });
            } else if (!isUserOnStage2Page) {
                navigate(`../techfiles`, {
                    state: { projectName, selectedFeatures, action },
                });
            }
        }
    }, [setIsUserOnStage2Page, navigate, projectName, selectedFeatures, action, setIsRunningJobErrored, isUserOnStage2Page]);

    const handleCancelButton = useCallback(() => {
        if (webSocketObj) {
            webSocketObj.close();
        }
        setRunLayoutJobId(null);
        setIsUserInAction1EditFromViewProject(false);
        setIsUserInAction2EditFromViewProject(false);
        setIsUserInAction3EditFromViewProject(false);
        setIsRunningJobErrored(false);
        setStage1Result([]);
        setIsButtonDisabledInEditMode(false);
        setIsUserInEditMode(false);
        setIsRunningJobCompleted(false);
        setRunLayoutRunningJobLogs([]);
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
        setSelectedGdsItems([]);
        setIsUserOnStage2Page(false);
        setIsHyperExpressivityProjectSaved(false);
        setSelectedProjectNameWithStage1Result();
        setIsProjectWithStage1ResultSelectedFromList(false);
        setStage2Result();
        setInPreviousThroughHyperExpressivityProjectCreation(false);
        setRunningJobStatus(false);
        setIsNetlistDataChanged(false);
        setIsTechDataChanged(false);
        setShowResultButtonInStage1ResultInEditMode(false);
        setShowResultButtonInTechFileInEditMode(false);
        setStage1GraphData(null);
        setStage2GraphData(null);
        setTypeOfSelectedProject(0);
        setIsProjectStillRunning(false);
        setDefaultTechFileData();
        setStage1RunResultSummaryData();
        setStage2RunResultSummaryData();
        setStage1GdsLayoutImageData([]);
        setStage2GdsLayoutImageData([]);
        setIsStage1RunResultPresent(false);
        setIsStage2RunResultPresent(false);
        navigate("/home");
        setStage2TotalGDSNumber(0)
        setStage1TotalGDSNumber(0)
        setViewProjectTechFile(false);
        setProjectTechFileListData();
        setIsTechFileProjectSaved(false);
    }, [
        setIsStage1RunResultPresent,
        setIsStage2RunResultPresent,
        setIsProjectStillRunning,
        setTypeOfSelectedProject,
        setRunLayoutJobId,
        webSocketObj,
        setIsUserInAction1EditFromViewProject,
        setIsUserInAction2EditFromViewProject,
        setIsUserInAction3EditFromViewProject,
        setIsProjectWithStage1ResultSelectedFromList,
        setStage2Result,
        setRunningJobStatus,
        setSelectedProjectNameWithStage1Result,
        setIsHyperExpressivityProjectSaved,
        setIsUserOnStage2Page,
        setStage1Result,
        setIsRunningJobErrored,
        setIsButtonDisabledInEditMode,
        setIsUserInEditMode, setIsRunningJobCompleted, setRunLayoutRunningJobLogs, navigate, setIsTechFileSelected, setSelectedTechFileName, setNetlistCellInfo, setIsNetListFileSelected,
        setNetlistFileContent, setSelectedNetlistFileName, setSelectedNetlistFileType, setIsProjectSaved,
        setIsSelectAllChecked, setCurrentProjectId, setSelectedGdsItems, setInPreviousThroughHyperExpressivityProjectCreation, setIsNetlistDataChanged, setIsTechDataChanged, setShowResultButtonInStage1ResultInEditMode, setShowResultButtonInTechFileInEditMode, setStage1GraphData, setStage2GraphData, setDefaultTechFileData, setStage1RunResultSummaryData, setStage2RunResultSummaryData, setStage1GdsLayoutImageData, setStage2GdsLayoutImageData, setStage1TotalGDSNumber,setStage2TotalGDSNumber, setViewProjectTechFile, setProjectTechFileListData, setIsTechFileProjectSaved]);

    const handleShowResultButton = useCallback(async () => {
        if (isApiResultLoading) return; // Prevent multiple clicks

        try {
            setIsApiResultLoading(true); // Set loading state to true before the API call
            if (action === 1) {
                // Trigger API call. stage 1 and page 0
                const stage1Res = await fetchStageData(currentProjectId, 1, 0);
                setStage1Result(stage1Res)
                setStage1GraphData(null);
                setStage2GraphData(null);
                navigate(`../stage1result`, { state: { projectName, selectedFeatures, action } });
            } else if (action === 2) {
                setIsUserOnStage2Page(true); // setting indication that user is on stage2 page
                // Trigger API call. stage 2 and page 0
                const stage2Res = await fetchStageData(currentProjectId, 2, 0);
                setSelectedGdsItems(stage2Res?.data?.selectedLayouts);
                setStage2Result(stage2Res);
                setStage1GraphData(null);
                setStage2GraphData(null);
                // Then navigate to the desired route with state
                navigate(`../stage2result`, { state: { projectName, selectedFeatures, action } });
            }
            else if (action === 3) {
                if (isUserOnStage2Page) {
                    const stage2Res = await fetchStageData(currentProjectId, 2, 0);
                    setSelectedGdsItems(stage2Res?.data?.selectedLayouts);
                    setStage2Result(stage2Res);
                    setStage1GraphData(null);
                    setStage2GraphData(null);
                    // Then navigate to the desired route with state
                    navigate(`../stage2result`, { state: { projectName, selectedFeatures, action: 3 } });
                } else if (!isUserOnStage2Page) {
                    const stage1Res = await fetchStageData(currentProjectId, 1, 0);
                    setStage1Result(stage1Res)
                    setStage1GraphData(null);
                    setStage2GraphData(null);
                    setSelectedGdsItems([]);
                    setSelectedProjectIdFromList(currentProjectId);
                    navigate(`../stage1result`, { state: { projectName, selectedFeatures, action: 3 } });
                }
            }
        }
        catch (error) {
            console.error('Error fetching stage data:', error);
        } finally {
            setIsApiResultLoading(false); // Reset loading state after API call
        }
    }, [setSelectedGdsItems, setIsUserOnStage2Page, isApiResultLoading, navigate, setStage1GraphData, setStage2GraphData, selectedFeatures, action, currentProjectId, setStage2Result, projectName, setStage1Result, isUserOnStage2Page, setSelectedProjectIdFromList]);

    //function to handle run job error cancellation 
    const handleCancelRunJobError = useCallback(() => {
        setIsRunningJobErrored(true); // setting this back to false once user clicks cancel on toaster  
    }, [setIsRunningJobErrored]);

    const CloseButton = ({ closeToast }) => (
        <FontAwesomeIcon icon={faXmark} id="run-toaster-cross-icon" onClick={() => { closeToast(); handleCancelRunJobError() }} />
    );

    //below use effect sets content for sidebar 
    useEffect(() => {
        setSidebarContent({
            upper: (
                <div >
                    <div className="mb-2">
                        <h6 className="mb-2">Project Name:</h6>
                        <span
                            id="sidebar-project-name"
                            className="text-dark py-2 text-break text-muted"
                        > {projectName} </span>
                    </div>
                    <div className="mb-2">
                        <h6 className="mb-2">Selected Netlist File:</h6>
                        {selectedNetlistFileName ? (<span id="netlist-selected-filename"
                            className="text-dark py-2 text-break text-muted">
                            {selectedNetlistFileName}
                        </span>) : <span className="text-muted" id="netlist-selected-filename">No file selected</span>}
                    </div>
                    <div className="mb-2">
                        <h6 className="mb-2">Selected PDK/Tech File:</h6>
                        {selectedTechFileName ? (<span id="techfile-selected-filename"
                            className="text-dark py-2 text-break">
                            {selectedTechFileName}
                        </span>) : <span className="text-muted" id="techfile-selected-filename">No file selected</span>}
                    </div>

                    {(actionSelected === 2 || actionSelected === 3) && (
                        <>
                            <div className="d-flex align-items-center gap-1" id="side-bar-upper-selected-no-of-GDS-items">
                                <h6 className="mb-0">Selected No of GDS Items:</h6>
                                {selectedGdsItems ? (<span id="selected-no-of-GDS-items"
                                    className="text-dark py-2 text-break">
                                    {selectedGdsItems?.length}
                                </span>) : <span className="text-muted" id="selected-no-of-GDS-items">0</span>
                                }
                            </div>
                        </>
                    )}
                </div>
            ),
            lower: (
                <div className="mb-1">
                    <div className="btn-group col-12" role="group" aria-label="Show Result button">
                        {!runningJobStatus && !isRunJobErrored && (<Button
                            id="show-stages-result-button"
                            className={`mx-0 my-1 w-100 border-0 ${!isRunningJobCompleted || !isApiResultLoading ? "app-primary-button-color border-0 cursor_not_allowed" : "app-secondary-button-color border-0"}`}
                            onClick={handleShowResultButton}
                            disabled={!isRunningJobCompleted || isApiResultLoading} // Step 4: Disable button when loading
                        >
                            {!isRunningJobCompleted || isApiResultLoading ? 'Loading...' : 'Show Result'} {/* Optional: Show loading text */}
                        </Button>)}
                    </div>
                    <div className="row">
                        <div className="btn-group" role="group" aria-label="Second group">
                            {!runningJobStatus && 
                                <Button
                                    id="previous-button"
                                    className={`me-0 ms-md-0 me-md-2 my-1 w-100 ${isApiResultLoading || isProjectStillRunning ? "app-primary-button-color border-0 cursor_not_allowed" : "app-primary-button-color border-0"}`}
                                    onClick={handlePreviousButton}
                                    disabled={isApiResultLoading || isProjectStillRunning}
                                    data-tooltip-id="tooltip-previous-button-on-loader"
                                    data-tooltip-content="Wait for run to be complete to go previous."
                                    data-tooltip-place="top"
                                >
                                    Previous
                                    {(isApiResultLoading || isProjectStillRunning) && (
                                        <ReactTooltip id="tooltip-previous-button-on-loader" style={{ width: 130, zIndex: 9999 }} />
                                    )}
                                </Button>

                            }
                            <Button
                                id="next-button"
                                className={`ms-0 my-1 w-100 app-secondary-button-color border-0`}
                                onClick={handleCancelButton}
                            >
                                Close
                            </Button>
                        </div>
                    </div>
                </div>
            )
        });
    }, [isProjectStillRunning, actionSelected, selectedGdsItems, isRunJobErrored, isRunningJobCompleted, isApiResultLoading, setSidebarContent, selectedNetlistFileName, selectedTechFileName, handlePreviousButton, handleCancelButton, handleShowResultButton, runningJobStatus, projectName]);

    //useeffect to show toaster message for run project error
    useEffect(() => {
        if (isRunJobErrored) {
            toast.error("Running of project failed , please retry running project.");//will show toaster to user on error
        }
    }, [isRunJobErrored]);


    //below useeffect opens websocket connection as soon as project is set to run
    useEffect(() => {
        let ws;
        if (runLayoutJobId) {
            //reading websocket hostname from env
            ws = new WebSocket(`${webSocketHostName}/${runLayoutJobId}/`);
            setWebSocketObj(ws);
            setIsProjectStillRunning(true);
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.message === "__close__") {
                    // If the close message is received, mark the job as complete and close the socket
                    console.log("Job Completed");
                    ws.close();
                } else {
                    //fetching current time in hrs , min ,sec
                    let now = new Date();
                    setRunLayoutRunningJobLogs((prevState) => [...prevState, `${now.getHours()}:${now.getMinutes()}:${now.getSeconds()} -Status :${data.status}: ${data.message}`])
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            ws.onclose = async () => {
                console.log('WebSocket connection closed');
                setIsProjectStillRunning(false);
                //checking in database if job was run successfully or not
                const getJobDetailsRes = await getJobDetailsOfJobID(runLayoutJobId);
                try {
                    if (getJobDetailsRes?.status && getJobDetailsRes?.data?.status === 'COMPLETED') {
                        //job is completed successfully , setting run job completed to be true
                        setIsRunningJobCompleted(true);
                    } else if (getJobDetailsRes?.status && getJobDetailsRes?.data?.status === 'FAILED') {
                        setIsRunningJobErrored(true);
                        setIsRunningJobCompleted(false);
                        console.error("Project Failed to Run in some of the steps");
                    }
                } catch (error) {
                    console.error("Error while fetching job details from DB", error);
                };
            };
        }
    }, [setIsProjectStillRunning, runLayoutJobId, setWebSocketObj, setIsRunningJobCompleted, setIsRunningJobErrored, setRunLayoutRunningJobLogs])


    return (
        <>
            <ToastContainer
                closeButton={CloseButton}
                position="top-center"
                autoClose={false}
                theme="colored"
            />
            {!isRunningJobCompleted && !isRunJobErrored ? (
                <div className="d-flex flex-column justify-content-center align-items-center" style={{ height: "100%" }}>
                    <div className="spinner-border" role="status">
                        <span className="sr-only">Loading...</span>
                    </div>
                    <p className="mt-3 text-muted">Generating result, please wait...</p>
                </div>)
                :
                <>
                    {isRunningJobCompleted && runningJobStatus ? (
                        <div className="d-flex flex-column justify-content-center align-items-center" style={{ height: "100%" }}>
                            <p className="mt-3 text-muted">Results Generated Successfully.</p>
                        </div>
                    ) : (
                        isRunningJobCompleted && (
                            <div className="d-flex flex-column justify-content-center align-items-center" style={{ height: "100%" }}>
                                <p className="mt-3 text-muted">Results Generated Successfully. Click show results to view run project results.</p>
                            </div>
                        )
                    )}

                </>
            }
            {(isRunJobErrored && !isRunningJobCompleted) && (
                <div className="d-flex flex-column justify-content-center align-items-center" style={{ height: "100%" }}>
                    <p className="mt-3 text-muted"> Running JobErrored , Retry Running Project Again or Contact Administrator. </p>
                </div>
            )}
        </>
    );
};

export default Loader;