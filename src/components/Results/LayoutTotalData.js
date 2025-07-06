import React, { useState, useEffect, useCallback, useMemo } from 'react';
import Table from '../utils/Table/Table';
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faDownload, faImage, faMinus, faPlus, faShoppingCart, faTrash } from '@fortawesome/free-solid-svg-icons';
import { useFilterResultsContext } from "../providers/FilterResultsProvider/FilterResultsContext";
import { useStage2ResultContext } from "../providers/Stage2ResultProvider/Stage2ResultContext";
import { useStage1ResultContext } from '../providers/Stage1ResultProvider/Stage1ResultContext';
import { useCreateProjectContext } from "../providers/CreateProjectProvider/CreateProjectContext.js";
import { fetchImageData } from "../../server/server";
import ModalComponent from "../utils/Modal/ModalComponent";
import ContextMenu from '../utils/ContextMenu/ContextMenu';
import useGetTableFilterData from "../../Hooks/getTableFilterData/useGetTableFilterData"
import useSingleGdsDownload from "../../Hooks/downloadSingleGdsFileHook/useSingleGdsDownload.js";
import useGdsLayoutCart from "../../Hooks/gdsLayoutCartHook/useGdsLayoutCart";
import useClearAllLevelFilter from "../../Hooks/clearAllLevelFiltersHook/useClearAllLevelFilter";

const LayoutTotalData = ({ gdsData = [], setIsTableImageLoading, loadingRef, userCurrentStage, stageGdsCartData, setViewCartOption, gdsLayoutToggle, setGdsLayoutToggle, showGDSLayoutImageData, setShowGDSLayoutImageData}) => {
    const { stage1GdsLayoutImageData, setStage1GdsLayoutImageData } = useStage1ResultContext();
    const { stage1TotalPexDataFilters, stage2TotalPexDataFilters, stage1Level2Filter, stage2Level2Filter, setStage1Level2Filter, setStage2Level2Filter } = useFilterResultsContext();
    const { isUserOnStage2Page, stage2GdsLayoutImageData, setStage2GdsLayoutImageData } = useStage2ResultContext();
    const { currentProjectId } = useCreateProjectContext();
    const { downloadGDSFile } = useSingleGdsDownload();
    const [fetchedImageData, setFetchedImageData] = useState([]);
    const [confirmTableImageDataFetchModal, setConfirmTableImageDataFetchModal] = useState(false);
    const [hasFetchedImages, setHasFetchedImages] = useState(false);
    const [totalPexDataContextMenu, setTotalPexDataContextMenu] = useState(false);
    const [selectedGdsName, setSelectedGdsName] = useState();
    const [selectedGdsImage, setSelectedGdsImage] = useState();
    const [contextMenuPosition, setContextMenuPosition] = useState(null);
    const { handleCart, isGDSAddedToCart, handleClearCart } = useGdsLayoutCart(selectedGdsName, userCurrentStage);
    const {handleClearAllLevelFilter} = useClearAllLevelFilter(isUserOnStage2Page ? 2 : 1);


    const updateGdsLayoutImageData = useCallback((newImages) => {
        if (isUserOnStage2Page) {
            setStage2GdsLayoutImageData(newImages);
        } else {
            setStage1GdsLayoutImageData(newImages);
        }
    }, [setStage1GdsLayoutImageData, setStage2GdsLayoutImageData, isUserOnStage2Page]);

    const imageMap = useMemo(() => {
        const images = isUserOnStage2Page
            ? [...stage2GdsLayoutImageData, ...fetchedImageData]
            : [...stage1GdsLayoutImageData, ...fetchedImageData];

        return images?.reduce((acc, img) => {
            acc[img?.file] = img?.encodedImage;
            return acc;
        }, {});
    }, [isUserOnStage2Page, stage1GdsLayoutImageData, stage2GdsLayoutImageData, fetchedImageData]);

    //below function handles the view layout in different tab.
    const handleViewLayout = () => {
        const newTab = window.open();
        if (newTab) {
            newTab.document.body.innerHTML =
                `<div style="display: flex; flex-direction: column; height: 90vh; justify-content: center; align-items: center; text-align: center;">
                   <h2>${selectedGdsName}</h2>
                   <img   src="data:image/png;base64,${selectedGdsImage}"  alt="${selectedGdsName}" style="width: 100%; height: 100%; object-fit: contain;" />
                 </div>`;
            newTab.document.title = selectedGdsName; // Setting gds name as title
        }
    }

    // context menu options
    const ContextMenuData = [
        {
            title: 'Download',
            action: () => { downloadGDSFile(selectedGdsName, currentProjectId, setTotalPexDataContextMenu, userCurrentStage) },
            icon: <FontAwesomeIcon icon={faDownload} />
        },
        {
            title: 'View Layout',
            action: handleViewLayout,
            icon: <FontAwesomeIcon icon={faImage} />
        },
        {
            title: isGDSAddedToCart ? "Remove from cart" : "Add to cart",
            action: () => { handleCart() },
            icon: <FontAwesomeIcon icon={isGDSAddedToCart ? faMinus : faPlus} />
        },
        ...(stageGdsCartData?.length > 0 ? [{
            title: "View Cart",
            action: () => { setViewCartOption(true) },
            icon: <FontAwesomeIcon icon={faShoppingCart} />
        }] : []),
        ...(stageGdsCartData?.length > 0 ? [{
            title: "Clear Cart",
            action: () => { handleClearCart(setSelectedGdsName, setViewCartOption) },
            icon: <FontAwesomeIcon icon={faTrash} />
        }] : [])

    ]

    // below function handle the click on gds layout image
    const handleTotalPexLayoutImage = (fileName, imgData, e) => {
        setSelectedGdsName(fileName);
        const { clientX, clientY } = e;
        setContextMenuPosition({ x: clientX, y: clientY });
        setSelectedGdsImage(imgData);
        setTotalPexDataContextMenu(true);
    }

    const alldata = useMemo(() => {
        if (!gdsLayoutToggle) {
            return gdsData?.PEX_Consolidated?.flatMap(item => item?.data) || [];
        }

        return gdsData?.PEX_Consolidated?.flatMap(item =>
            item?.data?.map(dataItem => ({
                ...dataItem,
                LayoutGDS: imageMap[dataItem?.File] ? (
                    <div className="position-relative" style={{ border: `${stageGdsCartData?.includes(dataItem?.File) ? "4px" : "0px"} solid #1b5376` }}>
                        <img
                            src={`data:image/png;base64,${imageMap[dataItem?.File]}`}
                            alt={`Layout GDS ${dataItem?.File}`}
                            className="img-fluid w-100"
                            onClick={(e) => handleTotalPexLayoutImage(dataItem?.File, imageMap[dataItem?.File], e)}
                        />
                    </div>
                ) : null
            }))
        ) || [];
    }, [gdsData, gdsLayoutToggle, imageMap, stageGdsCartData]);

    // use filtered data based on stage1 & stage2 filters
    const selectedFilters = isUserOnStage2Page ? stage2Level2Filter : stage1Level2Filter;
    // Use the hook
    const { filteredData } = useGetTableFilterData(alldata, selectedFilters);

    const allKeys = useMemo(() => {
        const keys = new Set(alldata?.flatMap(item => Object.keys(item)) || []);
        if (gdsLayoutToggle && keys.size > 0) keys.add("LayoutGDS");
        return [...keys];
    }, [alldata, gdsLayoutToggle]);

    const getLayoutDataList = useCallback(() => {
        return gdsData?.PEX_Consolidated?.flatMap(pexItem =>
            pexItem?.data?.map(item => item?.LayoutData || null) || []
        ) || [];
    }, [gdsData]);

    const convertTableFilterToGraphFilter = (tableFilter) => {
        let graphFilter = [];

        Object.entries(tableFilter).forEach(([key, filter]) => {
            if (filter.constraints && filter.constraints.length > 0) {
                let value1 = null;
                let value2 = null;
                let filterationValue = null;
                
                const constraints = filter.constraints;
                // delta calculation is done to avoid adding the values given in graph. 
                let delta = 0.0001
                
                if (constraints.length === 1) {
                    const { value, matchMode } = constraints[0];
                    if (value !== null) {
                        switch (matchMode) {
                            case 'equals':
                                filterationValue = '=';
                                value1 = value2 = value;
                                break;
                            case 'notEquals':
                                filterationValue = '!=';
                                value1 = value2 = value;
                                break;
                            case 'lt':
                                filterationValue = '<';
                                value2 = (parseFloat(value) - delta).toFixed(4);
                                break;
                            case 'gt':
                                filterationValue = '>';
                                value1 = (parseFloat(value) + delta).toFixed(4);
                                break;
                            case 'lte':
                                filterationValue = '<=';
                                value2 = value;
                                break;
                            case 'gte':
                                filterationValue = '>=';
                                value1 = value;
                                break;
                            default:
                                break;
                        }
                    }
                } else if (constraints.length === 2) {
                    const valueLte = constraints.find(c => c.matchMode === 'lte');
                    const valueGte = constraints.find(c => c.matchMode === 'gte');
                    const valueLt = constraints.find(c => c.matchMode === 'lt');
                    const valueGt = constraints.find(c => c.matchMode === 'gt');

                    if (valueLte && valueGte) {
                        filterationValue = "between";
                        value1 = valueGte.value;
                        value2 = valueLte.value;
                    } else if (valueLt && valueGt) {
                        filterationValue = "between";
                        if (valueLt > valueGt) {
                            value1 = (parseFloat(valueLt.value) - delta).toFixed(4);
                            value2 =(parseFloat(valueGt.value) + delta).toFixed(4);
                        }
                        else if (valueLt < valueGt) {
                            value1 = (parseFloat(valueGt.value) + delta).toFixed(4);
                            value2 = (parseFloat(valueLt.value) - delta).toFixed(4);
                        }
                        else {
                            value1 = valueLt.value;
                            value2 = valueGt.value;
                        }
                    }
                    else if (valueLt && valueGte) {
                        // Handle case: valueLt and valueGte
                        filterationValue = "between";
                        value1 = (parseFloat(valueLt.value) - delta).toFixed(4);
                        value2 = valueGte.value;
                    } else if (valueLte && valueGt) {
                        // Handle case: valueLte and valueGt
                        filterationValue = "between";
                        value1 = valueLte.value;
                        value2 = (parseFloat(valueGt.value) + delta).toFixed(4);
                    }
                }

                if (filterationValue && (value1 !== null || value2 !== null)) {
                    graphFilter.push({
                        parameterName1: key,
                        parameterName2: null,
                        filterationValue,
                        value1,
                        value2
                    });
                }
            }
        });
        return graphFilter;
    };

    const clearFilter = () => {
        if (!isUserOnStage2Page) {
            setStage1Level2Filter([]);
        } else {
            setStage2Level2Filter([]);
        }
        handleClearAllLevelFilter();
    };

    const handleTableImageModalClose = () => {
        setGdsLayoutToggle(false);
        setConfirmTableImageDataFetchModal(false);
    };

    const handleTableImageProceedButton = async () => {
        setConfirmTableImageDataFetchModal(false);
        await fetchImages();
        setHasFetchedImages(true);
    };

  // if the gdstoggle is false and data is not present in showGDSLayoutImageData 
  useEffect(()=>{
  if(!gdsLayoutToggle && !showGDSLayoutImageData){
     setHasFetchedImages(false);
    }
    },[gdsLayoutToggle, showGDSLayoutImageData, setHasFetchedImages])

    const fetchImages = useCallback(async () => {
        const layoutDataList = getLayoutDataList();
        if (!layoutDataList?.length) return;
        const imageData = isUserOnStage2Page ? stage2GdsLayoutImageData : stage1GdsLayoutImageData;

        if (imageData?.length > 0) {
            setIsTableImageLoading(false);
            return;
        }
            
        // if the data is already then avoiding hitting the endpoint
        if((gdsLayoutToggle && showGDSLayoutImageData)  || hasFetchedImages){
            return;
        }

        setIsTableImageLoading(true);
        try {
            const imageResponse = await fetchImageData(layoutDataList);
            updateGdsLayoutImageData(imageResponse?.images);
            setFetchedImageData(imageResponse?.images);
            setShowGDSLayoutImageData(imageResponse?.images);
            setGdsLayoutToggle(true);
        } catch (error) {
            console.error('Error fetching images:', error);
        } finally {
            setIsTableImageLoading(false);
        }
    }, [getLayoutDataList, isUserOnStage2Page, stage1GdsLayoutImageData, stage2GdsLayoutImageData, updateGdsLayoutImageData, setIsTableImageLoading, setShowGDSLayoutImageData, gdsLayoutToggle, showGDSLayoutImageData,hasFetchedImages, setGdsLayoutToggle]);

    // setting image data if already present in the imageMap
    useEffect(() => {
        if(imageMap && !showGDSLayoutImageData && gdsLayoutToggle){
        const imageData = Object?.entries(imageMap)?.map(([file, encodedImage]) => ({
          file,
          encodedImage
        }));
      
        // Set the transformed data into state
        setShowGDSLayoutImageData(imageData);
    }
      }, [setShowGDSLayoutImageData, showGDSLayoutImageData,imageMap, gdsLayoutToggle]);

    // update the images data on the table 
    useEffect(() => {
        if (gdsLayoutToggle && showGDSLayoutImageData) {
            updateGdsLayoutImageData(showGDSLayoutImageData)
        }
    }, [gdsLayoutToggle, showGDSLayoutImageData, updateGdsLayoutImageData])

    useEffect(() => {
        if (!isUserOnStage2Page) {
            const graphFilterJson = convertTableFilterToGraphFilter(stage1TotalPexDataFilters);
            if (graphFilterJson?.length > 0) {
                setStage1Level2Filter(graphFilterJson);
            }
        } else {
            const graphFilterJson = convertTableFilterToGraphFilter(stage2TotalPexDataFilters);
            if (graphFilterJson?.length > 0) {
                setStage2Level2Filter(graphFilterJson);
            }
        }
    }, [stage1TotalPexDataFilters, stage2TotalPexDataFilters, setStage1Level2Filter, setStage2Level2Filter, isUserOnStage2Page]);

    useEffect(() => {
        const layoutDataList = getLayoutDataList();

        if (gdsLayoutToggle && !hasFetchedImages) {
            if (layoutDataList?.length > 500) {
                setConfirmTableImageDataFetchModal(true);
            } else {
                fetchImages();
                setHasFetchedImages(true);
            }
        }
    }, [gdsLayoutToggle, getLayoutDataList, fetchImages, hasFetchedImages, setHasFetchedImages]);

    const TableImageModalContent = {
        title: "Table Images",
        body: (
            <p>
                Loading images for over 500 records. This may take some time. Do you wish to proceed and load tooltip images?
            </p>
        ),
        footer: (
            <div className="btn-group w-100" role="group" aria-label="Button group">
                <button
                    onClick={handleTableImageModalClose}
                    className="btn btn-secondary ms-0 ms-md-0 me-md-2 w-50"
                >
                    No
                </button>
                <button
                    onClick={handleTableImageProceedButton}
                    className="btn btn-primary ms-0 w-50"
                >
                    Yes
                </button>
            </div>
        ),
    };

    return (
        <div className='bg-white' style={{ height: `calc(100% - 62px)` }}>
            {/* Show loader when data is loading */}
            {loadingRef?.current ? (
                <div className="d-flex justify-content-center align-items-center" style={{ height: "100%" }}>
                    <div className="spinner-border" role="status">
                        <span className="sr-only">Loading...</span>
                    </div>
                </div>
            )
                : (
                    <div className="relative h-100">
                        <Table
                            data={filteredData}
                            columns={allKeys}
                            rowsPerPage={50}
                            emptyMessage="No data found"
                            clearFilter={clearFilter}
                            saveFiltersInContext={true}
                        />
                        <ModalComponent
                            id="stage-1-confirm-table-image-fetch-modal"
                            size="md"
                            show={confirmTableImageDataFetchModal}
                            handleClose={() => setConfirmTableImageDataFetchModal(false)}
                            modalContent={TableImageModalContent}
                            modalCSSClass="overflow-hidden"
                        />
                        <ContextMenu
                            show={totalPexDataContextMenu}
                            menuOptions={ContextMenuData}
                            onHide={() => { setTotalPexDataContextMenu(false) }}
                            position={contextMenuPosition}
                        />
                    </div>
                )}
        </div>
    );
};

export default LayoutTotalData;