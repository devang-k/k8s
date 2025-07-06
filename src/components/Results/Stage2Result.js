
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: Stage2Result.js  
 * Description: This file is responsible to show Hyper Expressivity results 
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
import { fetchStageData, fetchImageData, downloadStageResults, RunResultSummaryData } from "../../server/server";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
    faImages,
    faTable,
    faChartColumn,
    faDownload, faChartLine, faFileLines, faFilter,
    faCartShopping, faRotate,
    faTrash
} from "@fortawesome/free-solid-svg-icons";
import { useCreateProjectContext } from "../providers/CreateProjectProvider/CreateProjectContext";
import { useNetListFileContext } from "../providers/NetListFileProvider/NetListFileContext";
import { useTechFileContext } from "../providers/TechFileProvider/TechFileContext";
import { useStage2ResultContext } from "../providers/Stage2ResultProvider/Stage2ResultContext";
import { useStage1ResultContext } from "../providers/Stage1ResultProvider/Stage1ResultContext";
import { useRunProjectContext } from "../providers/RunProjectProvider/RunProjectContext";
import { useEditProjectContext } from "../providers/EditProjectProvider/EditProjectContext";
import { useLayoutGraphContext } from '../providers/LayoutGraphProvider/LayoutGraphContext';
import { ToastContainer, toast } from "react-toastify";
import LayoutMetricsData from "./LayoutMetricsData";
import LayoutPexData from "./LayoutPexData";
import LayoutImageData from "./LayoutImageData";
import LayoutPexDataConsolidated from "./LayoutPexDataConsolidated";
import LayoutGraphDataStage2 from "./LayoutGraphDataStage2";
import { Tooltip as ReactTooltip } from 'react-tooltip'
import ModalComponent from "../utils/Modal/ModalComponent";
import { DownloadResultsModalBody } from "./DownloadResultsModalBody"
import RunResultSummary from "./RunResultSummary";
import LayoutTotalData from "./LayoutTotalData";
import FilterRunResults from "../utils/FilterRunResults/FilterRunResults";
import { useFilterResultsContext } from "../providers/FilterResultsProvider/FilterResultsContext";
import ViewCart from "../utils/ViewCart/ViewCart";

import useApplyFilterHook from "../../Hooks/applyFilterHook/useApplyFilterHook";
import useClearAllLevelFilter from "../../Hooks/clearAllLevelFiltersHook/useClearAllLevelFilter";

import { isDebugModeOn } from "../../constant";

const Stage2ResultDisplay = () => {
    const { stage2Level2Filter, isFilterApplied, isStage2Level2FilterApplied, setIsStage2Level2FilterApplied, selectedDownloadOption, setSelectedDownloadOption, filterRequestParameter, isStage2FilterApplied, setIsStage2FilterApplied, clearFilterResultsContext, stage2GdsCartData, stage2GraphSelectedGdsCells } = useFilterResultsContext();
    const { setSidebarContent, toggleSidebar, isSidebarCollapsed, terminalHeight } = useOutletContext();
    const { stage2Result, setStage2Result, setIsUserOnStage2Page, stage2RunResultSummaryData, setStage2RunResultSummaryData, setStage2GdsLayoutImageData, stage2TotalGDSNumber, setStage2TotalGDSNumber } = useStage2ResultContext();
    const { stage1RunResultSummaryData, stage1Result, setStage1Result, setSelectedGdsItems, isGdsSelectAllChecked, setIsGdsSelectAllChecked, setStage1RunResultSummaryData, setStage1GdsLayoutImageData, setStage1TotalGDSNumber, selectedGdsItems } = useStage1ResultContext();
    const { setIsUserInEditMode, setIsButtonDisabledInEditMode, setShowResultButtonInStage1ResultInEditMode, setShowResultButtonInTechFileInEditMode } = useEditProjectContext();
    const {
        currentProjectId,
        setCurrentProjectId,
        setIsProjectSaved,
        setSelectedProjectIdFromList,
        selectedProjectNameWithStage1Result,
        setSelectedProjectNameWithStage1Result,
        setProjectListWithStage1Result,
        setIsHyperExpressivityProjectSaved,
        setIsProjectWithStage1ResultSelectedFromList,
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
        actionSelected,
        setNetlistFileContent,
        setIsNetListFileSelected,
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


    const { handleApplyFilterStage2 } = useApplyFilterHook();
    const { handleClearAllLevelFilter } = useClearAllLevelFilter(2);

    const { setIsProjectStillRunning, webSocketObj, setRunLayoutJobId, setIsRunningJobCompleted, setRunLayoutRunningJobLogs, setIsRunningJobErrored } = useRunProjectContext();
    const { stage2GraphData, setStage1GraphData, setStage2GraphData } = useLayoutGraphContext();
    const [gdsData, setGdsData] = useState([]);
    const [page, setPage] = useState(0);
    const [loadingMore, setLoadingMore] = useState(false);
    const [hasMoreImages, setHasMoreImages] = useState(true);
    const [totalImages, setTotalImages] = useState(0);
    const [currentPexView, setCurrentPexView] = useState("totaldata");
    const location = useLocation();
    const { projectName, selectedFeatures, action } = location.state || {};
    const loadingRef = useRef(false);
    const scrollRefGdsImage = useRef(null);
    const scrollRefGdsMetrics = useRef(null);
    const scrollRefGdsPex = useRef(null);
    const navigate = useNavigate();
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

    // const [showImageColumn, setShowImageColumn] = useState(false);
    const [showImageColumn, setShowImageColumn] = useState(false);
    const [isTableImageLoading, setIsTableImageLoading] = useState(false);
    const [showGDSLayoutImageData, setShowGDSLayoutImageData] = useState(); // This state stores the Layout Images Data
    const [gdsLayoutToggle, setGdsLayoutToggle] = useState(false); //This state handle the Layout toggle sync between Total Pex data and Graph Data

    // below function will help in closing filter pop up modal
    const closeFilterResultSlider = () => {
        document.getElementById("mySidenav").style.width = "0";
        setFilterResultSlider(false);
    }

    const handlePreviousButton = useCallback(() => {
        setIsUserOnStage2Page(false);
        navigate("../stage1result", {
            state: { projectName, selectedFeatures, action },
        });
    }, [navigate, projectName, selectedFeatures, action, setIsUserOnStage2Page]);

    const handleCancelButton = useCallback(() => {
        if (webSocketObj) {
            webSocketObj.close();
        }
        setRunLayoutJobId(null);
        setIsUserInAction1EditFromViewProject(false);
        setIsUserInAction2EditFromViewProject(false);
        setIsUserInAction3EditFromViewProject(false);
        setGdsData([]);
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
        setSelectedProjectIdFromList();
        setSelectedProjectNameWithStage1Result();
        setProjectListWithStage1Result();
        setSelectedGdsItems([]);
        setRunLayoutRunningJobLogs([]);
        setIsRunningJobCompleted(false);
        setIsRunningJobErrored(false);
        setSelectedGdsItems([]);
        setStage1Result();
        setStage2Result();
        setIsUserInEditMode(false);
        setIsButtonDisabledInEditMode(false);
        setIsHyperExpressivityProjectSaved(false);
        setIsProjectWithStage1ResultSelectedFromList(false);
        setIsUserOnStage2Page(false);
        setInPreviousThroughHyperExpressivityProjectCreation(false);
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
        navigate("/home");
        setStage1RunResultSummaryData()
        setStage2RunResultSummaryData()
        setStage1GdsLayoutImageData([])
        setStage2GdsLayoutImageData([])
        setIsStage1RunResultPresent(false)
        setIsStage2RunResultPresent(false)
        clearFilterResultsContext()
        setStage2TotalGDSNumber(0)
        setStage1TotalGDSNumber(0)
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
        setIsProjectWithStage1ResultSelectedFromList,
        setIsHyperExpressivityProjectSaved,
        setIsUserInEditMode,
        setIsButtonDisabledInEditMode,
        setStage1Result,
        setIsRunningJobCompleted,
        setIsRunningJobErrored,
        setRunLayoutRunningJobLogs,
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
        setSelectedGdsItems,
        setInPreviousThroughHyperExpressivityProjectCreation,
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
        setStage2TotalGDSNumber,
        setStage1TotalGDSNumber,
        setViewProjectTechFile,
        setProjectTechFileListData,
        setIsTechFileProjectSaved
    ]);

    const handleDownloadModalClose = () => {
        setCheckedValues({ gds: false, metrics: false, pex: false });  // Reset checkboxes
        setSelectedDownloadOption(3);
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

        let downloadTypeReqVal;
        if (selectedDownloadOption === 3) {
            // if download all will check here if filterall or download all
           // (filterRequestParameter?.cells?.length > 0 || stage2GraphSelectedGdsCells) ? downloadTypeReqVal = 2 : downloadTypeReqVal = 3; // 3 -> download all 2-> download filterall 
           if(( stage2GraphSelectedGdsCells?.length > 0 || !filterRequestParameter?.cellSelectAll ||  filterRequestParameter?.filterParametersName?.filterLevel1 !== null || filterRequestParameter?.filterParametersName?.filterLevel2?.length >0) ){
            downloadTypeReqVal = 2;
            setSelectedDownloadOption(2);
          }else{
            downloadTypeReqVal = 3
            setSelectedDownloadOption(3);
          }
        } else {
            downloadTypeReqVal = selectedDownloadOption;
        };

        const downloadPayload = {
            project_id: currentProjectId,
            stage: 2,
            file_types: Object?.keys(selectedData)?.filter(key => selectedData[key]), // Send only checked values
            // filter: (stage2GraphSelectedGdsCells) ? null : (filterRequestParameter?.cells?.length > 0 && (downloadTypeReqVal === 1 || downloadTypeReqVal === 4 || downloadTypeReqVal === 2)) ? filterRequestParameter : null, // sending filtered request to download all results
            filter:  stage2GraphSelectedGdsCells?.length > 0 ? null : filterRequestParameter ? filterRequestParameter :null,
            filterByLayout: (stage2GraphSelectedGdsCells?.length > 0) ? stage2GraphSelectedGdsCells : null,
            downloadType: downloadTypeReqVal || 3,//making default as download all
            fileList: selectedDownloadOption === 1 ? stage2GdsCartData : null // if cart download then send list otherwise null
        };

        try {
            // Make the API call to download the data
            const response = await downloadStageResults(downloadPayload);

            if (response?.data && response?.data instanceof Blob) {
                const downloadUrl = URL.createObjectURL(response.data);
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
                setViewCartOption(false);
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
        handleClearAllLevelFilter();
        setGdsLayoutToggle(false);
        setShowGDSLayoutImageData();
        setStage2GraphData({
            PEX_Consolidated: stage2GraphData?.PEX_Consolidated,
        });
        setStage2GdsLayoutImageData([]);
    };

    const isAnyCheckboxSelected = Object?.values(checkedValues)?.includes(true);
    const DownloadResultsModalContent = {
        title: "Download HyperExpressivity Results",
        body: (<DownloadResultsModalBody isAnyCheckboxSelected={isAnyCheckboxSelected} checkedValues={checkedValues} handleCheckboxChange={handleCheckboxChange} isDownloading={isDownloading} userStage={2} />),
        footer: (
            <>
                <Button
                    id="layout-hyperexpressivity-result-cancel-button"
                    onClick={() => handleDownloadModalClose()}
                    className="app-secondary-button-color border-0 w-25"
                    disabled={isDownloading} // Disable cancel button during download
                >
                    Cancel
                </Button>
                <Button
                    id="layout-hyperexpressivity-result-download-button"
                    onClick={() => gdsResultDownloadButton(checkedValues)} // Pass the current state (checkedValues) to the function
                    className={selectedDownloadOption === 4 ? "app-primary-button-color border-0 w-25" : !isAnyCheckboxSelected ? "w-25 app-secondary-button-color border-0 cursor_not_allowed" : "app-primary-button-color border-0 w-25"}
                    disabled={selectedDownloadOption === 4 ? false : !isAnyCheckboxSelected || isDownloading} // Disable button if no checkboxes are selected or if downloading
                >
                    {isDownloading ? "Downloading..." : "Download"}
                </Button>
            </>
        ),
    };

    useEffect(() => {
        // setting gdsdata to empty when filter is applied to make sure data is refreshed
        if (isStage2FilterApplied || isStage2Level2FilterApplied) {

            setGdsData([]);// emptying it to refresh gds data on filter
            setPage(0);

        }
    }, [isStage2FilterApplied, isStage2Level2FilterApplied]);

    // Check if the context has initial data and load it
    useEffect(() => {
        setIsStage2FilterApplied(false);// chnaging filter applied value to false , to make sure reapplying of filter works
        setIsStage2Level2FilterApplied(false); //changing filter applied value to false , to make sure reapplying of filter works
        if (stage2Result?.data?.Items?.length && gdsData?.length === 0) {
            const itemsData = stage2Result?.data?.Items;
            const PEX_Consolidated = stage2Result?.data?.PEX_Consolidated;
            const imagePaths = itemsData?.map(item => item?.LayoutData);
            setTotalImages(stage2Result?.data?.TotalItems || 0);

            const loadInitialStage2Data = async () => {
                loadingRef.current = true;
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
                        name: item?.LayoutData?.split("/").pop().replace(".png", ""),
                        metricsData: item?.MetricsData,
                        pexData: item?.PEXData,
                    }));
                    // Set initial data in local state
                    setGdsData({
                        items: initialImages,
                        PEX_Consolidated: PEX_Consolidated
                    });
                } finally {
                    loadingRef.current = false; // Reset loading to false once data is set or error encountered
                }
            };

            loadInitialStage2Data();
        }
    }, [stage2Result, gdsData?.length, setIsStage2FilterApplied, setIsStage2Level2FilterApplied]); // Dependencies to watch for changes

    // Below function gives the Run Result Summary Data for Stage1 and Stage2 based on the action
    const fetchRunResultSummaryData = useCallback(async (action) => {
        try {
            // If action is 3, we need to call the API twice, once for stage 1 and once for stage 2
            if (action === 3) {
                // Call for Stage 1 if stage1RunResultSummaryData is not already set
                if (!stage1RunResultSummaryData) {
                    const RunResultSummaryReqStage1 = {
                        "projectId": currentProjectId,
                        "stage": 1
                    };
                    const RunResultSummaryStage1Res = await RunResultSummaryData(RunResultSummaryReqStage1);
                    if (RunResultSummaryStage1Res?.status_code === 200) {
                        setStage1RunResultSummaryData(RunResultSummaryStage1Res); // Assuming you have a state for stage 1 data
                    }
                }

                // Call for Stage 2 only if stage2RunResultSummaryData is not already set
                if (stage1RunResultSummaryData && !stage2RunResultSummaryData) {
                    const RunResultSummaryReqStage2 = {
                        "projectId": currentProjectId,
                        "stage": 2
                    };
                    const RunResultSummaryStage2Res = await RunResultSummaryData(RunResultSummaryReqStage2);
                    if (RunResultSummaryStage2Res?.status_code === 200) {
                        setStage2RunResultSummaryData(RunResultSummaryStage2Res);

                    }
                }
            } else {
                // Below endpoint is called for the action other than 3
                if (!stage2RunResultSummaryData) {
                    const RunResultSummaryReq = {
                        "projectId": currentProjectId,
                        "stage": 2
                    };
                    const RunResultSummaryStage2Res = await RunResultSummaryData(RunResultSummaryReq);
                    if (RunResultSummaryStage2Res?.status_code === 200) {
                        setStage2RunResultSummaryData(RunResultSummaryStage2Res);
                    }
                }
            }
        } catch (error) {
            console.error("Error fetching data:", error);
        }
    }, [currentProjectId, setStage2RunResultSummaryData, setStage1RunResultSummaryData, stage1RunResultSummaryData, stage2RunResultSummaryData]);

    // The below useEffect hook calls the function based on selected action
    useEffect(() => {
        fetchRunResultSummaryData(action);
    }, [fetchRunResultSummaryData, action]);


    // onScroll it will trigger the loadStage2Data function with incrementing page 1
    const loadStage2Data = useCallback(async (pageNumber) => {
        if (loadingRef.current || !hasMoreImages) return;

        loadingRef.current = true;
        setLoadingMore(true);

        try {
            // Fetch new data from API based on pageNumber
            const newStage2Res = await fetchStageData(currentProjectId, 2, pageNumber, filterRequestParameter ? filterRequestParameter : null);

            if (newStage2Res?.status === false || !newStage2Res?.data?.Items.length) {
                setHasMoreImages(false);
                return;
            }

            const newItemsData = Array.isArray(newStage2Res?.data?.Items) ? newStage2Res?.data?.Items : [];
            const PEX_Consolidated = newStage2Res?.data?.PEX_Consolidated;
            const newPageNumber = newStage2Res?.data?.PageNumber;
            const newPageSize = newStage2Res?.data?.PageSize;
            const newTotalItems = newStage2Res?.data?.TotalItems;
            const newRemainingItems = newStage2Res?.data?.RemainingItems;
            const newTotalGDSGeneratedCount = newStage2Res?.data?.TotalGdsCount;

            // Update total images count
            setTotalImages(newStage2Res?.data?.TotalItems || 0);

            // Fetch image data
            const imagePaths = newItemsData?.map(item => item?.LayoutData);
            const imagesData = await fetchImageData(imagePaths);

            if (!imagesData || !imagesData?.images || imagesData?.images?.length !== newItemsData?.length) {
                toast.error("Mismatch in image data fetched");
                console.error("Mismatch in image data fetched", imagesData);
                return;
            }

            const newImages = newItemsData?.map((item, index) => ({
                src: `data:image/png;base64,${imagesData?.images[index].encodedImage}`,
                name: item?.LayoutData?.split("/").pop().replace(".png", ""),
                metricsData: item?.MetricsData,
                pexData: item?.PEXData,
            }));

            // Append the new data to the context
            setStage2Result(prevResult => ({
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
                    RemainingItems: newRemainingItems, // Update RemainingItems with the new value
                    TotalGdsCount: newTotalGDSGeneratedCount //Update totalgds generatedcount
                },
            }));

            setGdsData(prevState => ({
                items: [...(Array.isArray(prevState?.items) ? prevState.items : []), ...newImages],
                PEX_Consolidated: !PEX_Consolidated ? prevState?.PEX_Consolidated : PEX_Consolidated
            }));

        } catch (error) {
            toast.error("Error while fetching stage2 data");
            console.error("Error fetching stage2 data:", error);
        } finally {
            loadingRef.current = false;
            setLoadingMore(false);
        }
    }, [currentProjectId, hasMoreImages, setStage2Result, filterRequestParameter]);

    // If stage2Result is not loaded
    useEffect(() => {
        if (!stage2Result?.data) {
            loadStage2Data()
        }
    }, [stage2Result, loadStage2Data])

    const handleScroll = useCallback((ref, setPage) => {
        if (!ref?.current) {
            return;
        }
        const { scrollTop, scrollHeight, clientHeight } = ref?.current;
        if (scrollTop == null || scrollHeight == null || clientHeight == null) {
            return;
        }
        if (!loadingRef.current && scrollTop + clientHeight >= scrollHeight - 50) {
            const nextPageNumber = () => {
                const newPage = page + 1;
                stage2Result?.data?.RemainingItems > 0 && loadStage2Data(newPage);
                return newPage;
            };
            setPage(nextPageNumber);
        }
    }, [stage2Result, loadStage2Data, page]);

    const debouncedScroll = useCallback((ref, setPage) => {
        let timer;
        return () => {
            clearTimeout(timer);
            timer = setTimeout(() => handleScroll(ref, setPage), 200);
        };
    }, [handleScroll]);

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
    }, [setPage, debouncedScroll, currentPexView]);

    //to store total GDS value

    useEffect(() => {
        if (stage2Result?.data?.TotalGdsCount) {
            setStage2TotalGDSNumber(stage2Result?.data?.TotalGdsCount);
        }
    }, [stage2Result, setStage2TotalGDSNumber]);

    useEffect(() => {
        setSidebarContent({
            upper: (
                <div>
                    <div className="mb-2">
                        <h6 className="mb-2">Project Name:</h6>
                        <span
                            id="sidebar-project-name"
                            className="text-muted text-break text-dark"
                        > {projectName} </span>
                    </div>
                    <h6 className="mb-2">Selected Netlist File:</h6>
                    <span className="text-muted text-break text-dark" id="netlist-selected-filename">
                        {selectedNetlistFileName
                            ? selectedNetlistFileName
                            : "No file selected"}
                    </span>
                    <h6 className="mt-2">Selected PDK/Tech File:</h6>
                    <span className="text-muted text-break text-dark" id="techfile-selected-filename">
                        {selectedTechFileName ? selectedTechFileName : "No file selected"}
                    </span>
                    {actionSelected === 2 && (
                        <>
                            <h6 className="mt-2">Selected Project Name With Layouts:</h6>
                            <span className="text-muted text-break text-dark" id="selected-project-name-with-layouts">
                                {selectedProjectNameWithStage1Result ? selectedProjectNameWithStage1Result : "No file selected"}
                            </span>
                        </>
                    )}
                    <div className="d-flex align-items-center gap-1 mt-1" id="side-bar-upper-no-of-GDS-images-generated">
                        <h6 className="mt-2">No. of Generated GDS Images:</h6>
                        {/* <span className="text-muted text-break text-dark" id="no-of-GDS-images-generated">{totalImages ? totalImages : 0}</span> */}
                        {/** reading total no of generated imgaes from end pt as it send no of gds generated*/}
                        <span className="text-muted text-dark" id="no-of-GDS-images-generated">{stage2TotalGDSNumber || 0}</span>
                    </div>
                    {/* below is displayed only if filter is applied */}
                    {(isFilterApplied || stage2Level2Filter?.length > 0) && (
                        <div className="d-flex align-items-center gap-1 mt-1" id="side-bar-upper-filtered-no-of-GDS-images-generated">
                            <h6 className="">No. of Filtered GDS Images:</h6>
                            <span className="text-muted text-break text-dark mb-1" id="filtered-no-of-GDS-images-generated-stage2">
                                {stage2Result?.status === false ? 0 : (totalImages ? totalImages : 0)}
                            </span>
                        </div>
                    )}
                    <>
                        <div className="d-flex align-items-center gap-1" id="side-bar-upper-selected-no-of-GDS-items">
                            <h6 className="mt-2">Selected No of GDS Items:</h6>
                            <span className="text-muted text-break text-dark" id="selected-no-of-GDS-items">
                                {selectedGdsItems?.length
                                    ? selectedGdsItems?.length
                                    : stage1Result?.data?.TotalItems}
                            </span>
                        </div>
                    </>
                </div>
            ),
            lower: (
                <div className="col-12">
                    <div className="row">
                        <div className="btn-group" role="group" aria-label="Second group">
                            <Button
                                id="previous-button-stage2-result-page"
                                className="ms-0 ms-md-0 me-md-2 my-1 w-100 app-primary-button-color border-0"
                                onClick={handlePreviousButton}
                            >
                                Previous
                            </Button>
                            <Button
                                id="cancel-button-stage2-results-page"
                                className={`ms-0 my-1 w-100 app-secondary-button-color border-0 ${!true ? "cursor_not_allowed" : ""}`}
                                onClick={handleCancelButton}
                            >
                                Close
                            </Button>
                        </div>
                    </div>
                </div>

            )
        });
    }, [stage2Level2Filter, selectedGdsItems, stage2Result, stage1Result, selectedProjectNameWithStage1Result, actionSelected, stage2TotalGDSNumber, setSidebarContent, selectedNetlistFileName, selectedTechFileName, totalImages, handlePreviousButton, handleCancelButton, stage1Result?.data?.TotalItems, isGdsSelectAllChecked, projectName, isFilterApplied]);


    const handleGDSImageToggle = (e) => {
        setShowImageColumn(e.target.checked);
        setGdsLayoutToggle(e.target.checked);
    }
    return (
        <>
            {/* Modal to get filter options from user */}
            {/* for stage2 as well we will be reading data from stage1 summary itself */}
            {filterResultSlider && (<FilterRunResults closeFilterResultSlider={closeFilterResultSlider} runSummaryData={stage1RunResultSummaryData?.data} filterStage={2} />)}
            <ModalComponent
                id="download-gds-result-modal"
                size="lg"
                show={downloadResultModal}
                handleClose={() => setDownloadResultModal(false)} // Close the modal on close button
                modalContent={DownloadResultsModalContent}
                modalCSSClass={"overflow-hidden;"}
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
                        <ul
                            className="nav nav-tabs justify-content-center"
                            id="stage2-result-tabs-list"
                            role="tablist"
                        >
                            {stage2RunResultSummaryData && (
                                <li className="nav-item ms-auto tabs-border" role="presentation">
                                    <a
                                        className="nav-link tabs-btn fw-bold text-uppercase border px-4 py-2"
                                        id="run-result-summary-tab-stage-2"
                                        role="tab"
                                        data-bs-toggle="tab"
                                        href="#run-result-summary-stage-2"
                                        aria-controls="summary-tab"
                                        aria-selected="true"
                                        data-tooltip-id="Summary-tooltip"
                                        data-tooltip-content="Run Summary"
                                        data-tooltip-place="top"
                                    >
                                        <FontAwesomeIcon icon={faFileLines} style={{ fontSize: "20px" }} />
                                    </a>
                                    <ReactTooltip id="Summary-tooltip" style={{ zIndex: 9999 }} />
                                </li>
                            )}
                            <li className={`nav-item tabs-border ${!stage2RunResultSummaryData && "ms-auto"}`} role="presentation">
                                <a
                                    className="nav-link active tabs-btn fw-bold text-uppercase border px-4 py-2"
                                    id="gds-image-tab-stage-2"
                                    role="tab"
                                    data-bs-toggle="tab"
                                    href="#gds-image-stage-2"
                                    aria-controls="gds-image-stage-2"
                                    aria-selected="true"
                                    data-tooltip-id="gds-tooltip"
                                    data-tooltip-content="GDS Layouts"
                                    data-tooltip-place="top"
                                >
                                    <FontAwesomeIcon
                                        icon={faImages}
                                        style={{ fontSize: "20px" }}
                                    />
                                </a>
                                <ReactTooltip id="gds-tooltip" style={{ zIndex: 9999 }} />
                            </li>
                             {/* metric tab is only visible in qa env for analysis it is not visible in prod it is enabled disabled based on the env flag */}
                             {isDebugModeOn && (
                            <li className="nav-item tabs-border"
                                role="presentation"
                            >
                                <a
                                    className="nav-link tabs-btn fw-bold text-uppercase border px-4 py-2"
                                    id="gds-metrics-tab-stage-2"
                                    role="tab"
                                    data-bs-toggle="tab"
                                    href="#gds-metrics-stage-2"
                                    aria-controls="gds-metrics-stage-2"
                                    aria-selected="true"
                                    data-tooltip-id="Metric-tooltip"
                                    data-tooltip-content="Metric Values"
                                    data-tooltip-place="top"
                                >
                                    <FontAwesomeIcon
                                        icon={faTable}
                                        style={{ fontSize: "20px" }}
                                    />
                                </a>
                                <ReactTooltip id="Metric-tooltip" style={{ zIndex: 9999 }} />
                            </li>
                             )}
                            <li className="nav-item tabs-border"
                                role="presentation"
                            >
                                <a
                                    className="nav-link tabs-btn fw-bold text-uppercase border px-4 py-2"
                                    id="gds-pex-tab-stage-2"
                                    role="tab"
                                    data-bs-toggle="tab"
                                    href="#gds-pex-stage-2"
                                    aria-controls="gds-pex-stage-2"
                                    aria-selected="true"
                                    data-tooltip-id="PEX-tooltip"
                                    data-tooltip-content="PEX Predictions"
                                    data-tooltip-place="top"
                                >
                                    <FontAwesomeIcon
                                        icon={faChartColumn}
                                        style={{ fontSize: "20px" }}
                                    />
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
                            <li className="nav-item ms-auto d-flex" role="presentation">
                                <div className="nav-item ms-auto d-flex align-items-center me-3">
                                    {stage2GdsCartData?.length > 0 && (
                                        <button
                                            className="border-0 bg-transparent active tabs-btn"
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
                                                className="view-cart-count position-relative text-white bottom-4 px-1 rounded"
                                            >
                                                {stage2GdsCartData?.length}
                                            </span>
                                            <ReactTooltip id="view-cart-tooltip" style={{ zIndex: 9999 }} />
                                        </button>

                                    )}
                                    {/* sync button to sync filter level2 across tab */}
                                    {/* apply filter api call button */}
                                    {(isStage2Level2FilterApplied || stage2Level2Filter?.length > 0) && (
                                        <button
                                            className="btn btn-link button-primary-color p-0 me-3"
                                            id="stage-1-graph-filter2-sync-across-tab-btn"
                                            onClick={handleApplyFilterStage2}
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
                                    {(stage1RunResultSummaryData?.data && stage2RunResultSummaryData?.data) && (
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
                                            <FontAwesomeIcon
                                                icon={faFilter}
                                                style={{ fontSize: "16px" }}
                                            />
                                            <ReactTooltip id="filter-results-tooltip" style={{ zIndex: 9999 }} />
                                        </button>
                                    )}
                                    {((isFilterApplied) || (isStage2Level2FilterApplied || stage2Level2Filter.length > 0) || stage2GraphSelectedGdsCells) && (
                                        <button
                                            className="border-0 bg-transparent active tabs-btn"
                                            id="stage-2-clear-filter-button"
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
                                        id="gds-download-tab"
                                        role="tab"
                                        aria-controls="gds-download"
                                        aria-selected="true"
                                        data-tooltip-id="download-tooltip"
                                        data-tooltip-content="Download Result"
                                        data-tooltip-place="top"
                                        onClick={downloadButton}
                                    >
                                        <FontAwesomeIcon
                                            icon={faDownload}
                                            style={{ fontSize: "16px" }}
                                        />

                                        <ReactTooltip id="download-tooltip" style={{ zIndex: 9999 }} />
                                    </button>
                                </div>
                            </li>
                        </ul>
                        <div
                            className="tab-content flex-grow-1"
                            id="gds-data-stage-2-content"
                            style={{ overflowY: "auto" }}
                        >
                            <div
                                className="tab-pane fade show w-100 h-100"
                                id="run-result-summary-stage-2"
                                role="tabpanel"
                                aria-labelledby="run-result-summary-tab-stage-2"
                                ref={scrollRefGdsImage}
                                style={{ overflowY: "auto", maxHeight: "calc(100vh - 0px)" }}
                            >
                                <div className="col-3 d-flex justify-content-start w-100 align-items-center my-2 ps-3">
                                    <RunResultSummary stage2RunResultSummaryData={stage2RunResultSummaryData} />
                                </div>
                            </div>
                            <div
                                className="tab-pane fade show active h-100"
                                id="gds-image-stage-2"
                                role="tabpanel"
                                aria-labelledby="gds-image-stage-2"
                                ref={scrollRefGdsImage}
                                style={{ overflowY: "auto", maxHeight: "calc(100vh - 0px)" }}
                            >
                                <LayoutImageData
                                    gdsData={gdsData}
                                    loadingRef={loadingRef}
                                    actionSelected={actionSelected}
                                    loadingMore={loadingMore}
                                    setViewCartOption={setViewCartOption}
                                    stageGdsCartData={stage2GdsCartData}
                                    userCurrentStage={2}
                                />
                            </div>
                            <div
                                className="tab-pane fade h-100"
                                id="gds-metrics-stage-2"
                                role="tabpanel"
                                aria-labelledby="gds-metrics-stage-2"
                                ref={scrollRefGdsMetrics}
                                style={{ overflowY: "auto", maxHeight: "calc(100vh - 0px)" }}
                            >
                                <LayoutMetricsData
                                    gdsData={gdsData}
                                    loadingRef={loadingRef}
                                    actionSelected={actionSelected}
                                    loadingMore={loadingMore}
                                />
                            </div>

                            <div
                                className="tab-pane fade h-100"
                                id="gds-pex-stage-2"
                                role="tabpanel"
                                aria-labelledby="gds-pex-stage-2"
                                ref={scrollRefGdsPex}
                                style={{ overflowY: "auto", maxHeight: "calc(100vh - 0px)" }}
                            >
                                <div className="col-12 d-flex justify-content-start align-items-center my-2">
                                    <div className="d-flex justify-content-start align-items-center my-2">
                                        <div className="form-check ms-3">
                                            <input
                                                className="form-check-input shadow-none"
                                                type="radio"
                                                id="stage2-total-data-view"
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
                                                id="stage2-pex-data-view"
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
                                                id="stage2-consolidated-data-view"
                                                checked={currentPexView === "consolidateddata"}
                                                onChange={() => setCurrentPexView("consolidateddata")}
                                            />
                                            <label className="form-check-label" htmlFor="consolidated-data-view">
                                                Consolidated PEX View
                                            </label>
                                        </div>

                                        {(currentPexView === "totaldata" && stage2Result?.status) && (
                                            <div className="form-check ms-3 form-switch">
                                                <input
                                                    className="form-check-input shadow-none"
                                                    type="checkbox"
                                                    role="switch"
                                                    id="stage-2-GDS-image-toggle-button"
                                                    onChange={handleGDSImageToggle}
                                                    checked={gdsLayoutToggle}
                                                    style={{ cursor: "pointer" }}
                                                    disabled={false}
                                                />
                                                <label className="form-check-label" htmlFor="stage-2-GDS-image-toggle-button">
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
                                        userCurrentStage={2}
                                        stageGdsCartData={stage2GdsCartData}
                                        setViewCartOption={setViewCartOption}
                                        gdsLayoutToggle={gdsLayoutToggle}
                                        setGdsLayoutToggle={setGdsLayoutToggle}
                                        showGDSLayoutImageData={showGDSLayoutImageData}
                                        setShowGDSLayoutImageData={setShowGDSLayoutImageData}
                                    />
                                ) : null}
                            </div>
                            {/* Tab 4 Content with Toggle */}
                            <div
                                className="tab-pane fade h-100"
                                id="gds-graphs"
                                role="tabpanel"
                                aria-labelledby="gds-graph-tab"
                                style={{ overflowY: "auto", maxHeight: "calc(100vh - 0px)" }}
                            >
                                <LayoutGraphDataStage2
                                    totalImages={totalImages}
                                    projectName={projectName}
                                    stage={2}
                                    toggleSidebar={toggleSidebar}
                                    isSidebarCollapsed={isSidebarCollapsed}
                                    terminalHeight={terminalHeight}
                                    currentProjectId={currentProjectId}
                                    selectedProjectIdFromList={currentProjectId}
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
            {viewCartOption && (<ViewCart setViewCartOption={setViewCartOption} viewCartOption={viewCartOption} setSelectedCellFromList={setSelectedCellFromList} selectedCellFromList={selectedCellFromList} setDownloadResultModal={setDownloadResultModal} userCurrentStage={2} stageGdsCartData={stage2GdsCartData} />)}
        </>
    );
};

export default Stage2ResultDisplay;

