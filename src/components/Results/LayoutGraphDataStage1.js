
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: LayoutGraphDataStage1.js  
 * Description: This file is responsible to show stage 1 Layout Graph Data 
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

import React, { useEffect, useState, useRef, useCallback } from "react";
import { fetchImageData } from "../../server/server";
import * as echarts from 'echarts/core';
import {
  DatasetComponent,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  TransformComponent,
  LegendComponent,
  ToolboxComponent,
  DataZoomComponent,
  BrushComponent
} from 'echarts/components';
import { ScatterChart, LineChart } from 'echarts/charts';
import { UniversalTransition, LabelLayout } from 'echarts/features';
import { CanvasRenderer } from 'echarts/renderers';
import { useLayoutGraphContext } from '../providers/LayoutGraphProvider/LayoutGraphContext';
import { useStage1ResultContext } from "../providers/Stage1ResultProvider/Stage1ResultContext";
import { useCreateProjectContext } from "../providers/CreateProjectProvider/CreateProjectContext";
import { downloadSingleGDSImage } from '../../server/server'
import { toast } from "react-toastify";
import ModalComponent from "../utils/Modal/ModalComponent";
import { Slider } from "@mui/material";
import { Tooltip as ReactTooltip } from 'react-tooltip'
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faFilter, faTimes, faDownload, faImage, faPlus, faMinus, faShoppingCart, faTrash } from '@fortawesome/free-solid-svg-icons';
import ContextMenu from "../utils/ContextMenu/ContextMenu";
import useViewLayoutImageHook from "../../Hooks/ViewLayoutHook/useViewLayoutImageHook";
import useGdsLayoutCart from "../../Hooks/gdsLayoutCartHook/useGdsLayoutCart";
import useClearAllLevelFilter from "../../Hooks/clearAllLevelFiltersHook/useClearAllLevelFilter";
import { useFilterResultsContext } from "../providers/FilterResultsProvider/FilterResultsContext";
import useApplyFilterHook from "../../Hooks/applyFilterHook/useApplyFilterHook";


echarts.use([
  DatasetComponent,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  TransformComponent,
  ScatterChart,
  LineChart,
  UniversalTransition,
  LabelLayout,
  ToolboxComponent,
  CanvasRenderer,
  DataZoomComponent,
  BrushComponent
]);

const LayoutGraphDataStage1 = ({ columns, totalImages, projectName, toggleSidebar, isSidebarCollapsed, setViewCartOption, setSelectedCellFromList, terminalHeight, gdsLayoutToggle, setGdsLayoutToggle, showGDSLayoutImageData, setShowGDSLayoutImageData, loadingRef }) => {

  const { stage1Result, stage1GdsLayoutImageData, setStage1GdsLayoutImageData } = useStage1ResultContext();
  const { stage1GraphData, setStage1GraphData } = useLayoutGraphContext();
  const { currentProjectId } = useCreateProjectContext();
  const { techVariationFilterSelectedParameter, stage1FilteredLevel2Cells, isFilterApplied, setFilterRequestParameter, stage1FilterSelectedCells, stage1IsAllCellSelectedForFilter, stage1TotalPexDataFilters, stage1Level2Filter, setStage1Level2Filter, setIsGraphFilterCleared, stage1GdsCartData, stage1GraphSelectedGdsCells, setStage1GraphSelectedGdsCells } = useFilterResultsContext();
  const [loading, setLoading] = useState(false);
  const [dropdownOptions, setDropdownOptions] = useState([]);
  const [selectedOption1, setSelectedOption1] = useState("Capacitance Sum");
  const [selectedOption2, setSelectedOption2] = useState("Total Polygon Area (um^2)");// making this name change for google basline branch only , since core changed its name
  const [isGDSImagesNeeded, setIsGDSImagesNeeded] = useState(false);
  const [confirmLargeDataFetchModal, setConfirmLargeDataFetchModal] = useState(false);
  const [confirmTooltipImageDataFetchModal, setConfirmTooltipImageDataFetchModal] = useState(false);
  const [hasFetchedImages, setHasFetchedImages] = useState(false);
  const [hasModalBeenShown, setHasModalBeenShown] = useState(false);
  const [numericFields, setNumericFields] = useState(null);
  const [isGraphFilterSidebarOpen, setIsGraphFilterSidebarOpen] = useState(false);
  const [contextMenuOnStage1, setContextMenuOnStage1] = useState(false);
  const [selectedCellNameOnGraph, setSelectedCellNameOnGraph] = useState();// it stores user clicked gds name
  const [selectedLayoutData, setSelectedLayoutData] = useState();
  const [viewLayoutLoading, setViewLayoutLoading] = useState(false);
  const [menuPosition, setMenuPosition] = useState(null);

    const { handleApplyFilterStage1 } = useApplyFilterHook();


  // custom hooks
  const { handleCart, isGDSAddedToCart, handleClearCart } = useGdsLayoutCart(selectedCellNameOnGraph, 1);//sending 1 here as user is working on layout stage1 cart
  const {handleClearAllLevelFilter} = useClearAllLevelFilter(1);

  const { getImageData } = useViewLayoutImageHook(
    {
      selectedLayoutData,
      selectedCellNameOnGraph,
      setViewLayoutLoading,
      viewLayoutLoading,
    }
  );

  const chartDom = useRef(null);
  const myChart = useRef(null);
  const colorMap = useRef({}); // A ref to store color assignments to cells
  const stage1GraphSelectedCellsRef = useRef(null);  // A ref to store cell selected in graph

  const generateRandomColor = useCallback((existingColors, cellName) => {
    // If color is already assigned to the cell, return it
    if (colorMap.current[cellName]) {
      return colorMap.current[cellName];
    }

    let isUnique = false;
    let color = '';

    while (!isUnique) {
      // Generate a random dark color with lower RGB values
      const r = Math.floor(Math.random() * 128); // Red between 0-127
      const g = Math.floor(Math.random() * 128); // Green between 0-127
      const b = Math.floor(Math.random() * 128); // Blue between 0-127

      color = `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;

      isUnique = !existingColors?.includes(color);
    }

    // Store the color in the map for future use
    colorMap.current[cellName] = color;
    return color;
  }, []);

  // below useEffect sets the toggle of if the images Data is not present
  useEffect(()=>{
    if(stage1GdsLayoutImageData?.length === 0){
      setGdsLayoutToggle(false);
      setShowGDSLayoutImageData();
    }
  });

// if the gdstoggle is false and data is not present in showGDSLayoutImageData 
  useEffect(()=>{
    if(!gdsLayoutToggle && !showGDSLayoutImageData){
      setHasFetchedImages(false);
    }
  },[gdsLayoutToggle, showGDSLayoutImageData, setHasFetchedImages])

  const handleGDSTooltipImageToggle = async () => {  
  if ((!hasFetchedImages || !gdsLayoutToggle) && stage1GraphData?.imagesData) {
    setGdsLayoutToggle(prevState => !prevState);
  } else if ((gdsLayoutToggle && showGDSLayoutImageData) && !hasFetchedImages) {
    setGdsLayoutToggle(false);
  }

    // if the data is fetched and the Layout Data is available.
    if (hasFetchedImages && showGDSLayoutImageData && !gdsLayoutToggle) {
      setGdsLayoutToggle(prevState => !prevState);
    }

    // If images have already been fetched, toggle the state as usual
    if (hasFetchedImages) {
      setIsGDSImagesNeeded(prevState => !prevState);
      setGdsLayoutToggle(prevState => !prevState);
    } else {
      // If totalImages > 500 and modal hasn't been shown before, show the modal
      if (totalImages > 500 && !hasModalBeenShown) {
        setConfirmTooltipImageDataFetchModal(true);
        setHasModalBeenShown(true); // Mark modal as shown
      } else {
        // Otherwise, directly toggle the state and fetch data if totalImages <= 500 or modal has been shown
        const newState = !isGDSImagesNeeded;
        setIsGDSImagesNeeded(newState);

        if (newState && totalImages <= 500) {
          fetchDataTooltipImage();
        }
      }
    }
  };

  // Updating stage1graph data it the data is available and toggle is true.
  useEffect(() => {
    if (showGDSLayoutImageData && gdsLayoutToggle) {
      setStage1GraphData(prevState => ({
        ...prevState,
        imagesData: showGDSLayoutImageData || [],
        PEX_Consolidated: stage1Result?.data?.PEX_Consolidated || [],
      }));
      setIsGDSImagesNeeded(true)
    }
    else{
      setIsGDSImagesNeeded(false);
    }
  }, [gdsLayoutToggle, setStage1GraphData, showGDSLayoutImageData, stage1Result])


  const handleTooltipImageProceedButton = async () => {
    // Close the modal when the user proceeds
    setConfirmTooltipImageDataFetchModal(false);

    // Toggle the state to reflect the new status of the switch
    const newState = !isGDSImagesNeeded;
    setIsGDSImagesNeeded(newState);
    await fetchDataTooltipImage();
    // If switching on and totalImages <= 500, fetch data directly
    if (newState && totalImages < 500) {
      fetchDataTooltipImage();
    }
  };

  const handleTooltipImageModalClose = () => {
    setConfirmTooltipImageDataFetchModal(false);
  };

  const handleProceedButton = () => {
    setConfirmLargeDataFetchModal(false);
    fetchData();
  };

  // downloading single GDS file
  const downloadGDSFile = async () => {
    if (selectedCellNameOnGraph && currentProjectId) {
      const selectedGDS = [selectedCellNameOnGraph];
      const stage1GDSImageDownloadReq = {
        stage: 1,
        projectId: currentProjectId,
        fileList: selectedGDS,
      };

      try {
        const stage1GDSImageDownloadRes = await downloadSingleGDSImage(stage1GDSImageDownloadReq);
        if (stage1GDSImageDownloadRes?.status === 200) {
          const blob = new Blob([stage1GDSImageDownloadRes?.data], { type: 'application/zip' });
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;

          // Extract filename from headers or set a default
          const contentDisposition = stage1GDSImageDownloadRes?.headers["x-filename"];
          let fileName = 'download.zip'; // Default filename

          if (contentDisposition) {
            const fileNameMatch = contentDisposition.match(/filename="(.+)"/);
            if (fileNameMatch && fileNameMatch[1]) {
              fileName = fileNameMatch[1];
            } else {
              fileName = contentDisposition;
            }
          }

          // Set the filename for the download
          link.download = fileName;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
          setContextMenuOnStage1(false);
          toast.success("GDS downloaded successfully", { autoClose: 10000 });
        }
      } catch (error) {
        console.error('Error downloading GDS image:', error);
      }
    }
  }

  // below function open the layout image in seperate tab
  const handleViewLayout = () => {
    getImageData();
  }

  // Context Menu option
  const ContextMenuData = [
    {
      title: 'Download',
      action: downloadGDSFile,
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
    ...(stage1GdsCartData?.length > 0 ? [{
      title: "View Cart",
      action: () => { setViewCartOption(true) },
      icon: <FontAwesomeIcon icon={faShoppingCart} />
    }] : []),
    ...(stage1GdsCartData?.length > 0 ? [{
      title: "Clear Cart",
      action: () => { handleClearCart(setSelectedCellFromList, setViewCartOption) },
      icon: <FontAwesomeIcon icon={faTrash} />
    }] : [])
  ];

  // ** Fetching Functions **
  const fetchData = useCallback(async () => {
    if (!selectedOption1 || !selectedOption2) return;
    if (selectedOption1 && selectedOption2 && (!stage1GraphData || stage1GraphData?.PEX_Consolidated?.length === 0)) {
      setLoading(true);
      const mergedData = {
        PEX_Consolidated: stage1Result?.data?.PEX_Consolidated || [],
        ...(showGDSLayoutImageData && { imagesData: showGDSLayoutImageData || [] })
      };
      setStage1GraphData(mergedData);
      setLoading(false);
      setConfirmLargeDataFetchModal(false);
    }

     // if the filter is applied and data is updated
    if(gdsLayoutToggle && showGDSLayoutImageData){
      setIsGDSImagesNeeded(true);
    }
  }, [stage1Result, selectedOption1, selectedOption2, stage1GraphData, setStage1GraphData, showGDSLayoutImageData, gdsLayoutToggle, setIsGDSImagesNeeded]);

  const getLayoutDataList = useCallback(async () => {
    return stage1GraphData?.PEX_Consolidated?.flatMap(pexItem =>
      pexItem?.data?.map(item => item?.LayoutData)
    ) || [];
  }, [stage1GraphData]);

  const fetchDataTooltipImage = useCallback(async () => {
    if (!isGDSImagesNeeded && !stage1GraphData?.imagesData?.length) {
      // Directly use existing context data if available
      if (stage1GdsLayoutImageData && Array.isArray(stage1GdsLayoutImageData) && stage1GdsLayoutImageData?.length > 0) {
        try {
          setStage1GraphData(prevState => ({
            ...prevState,
            imagesData: stage1GdsLayoutImageData || [],
          }));
          setHasFetchedImages(true);
        } catch (error) {
          console.error("Error merging images:", error);
        }
        return; // No need to fetch images again
      }
      else {
        // Fetch images if context data is unavailable
        const layoutDataList = await getLayoutDataList();
        if (!layoutDataList?.length) return;

         // If the Data is already present then avoid hitting the endpoint again.
        if ((gdsLayoutToggle && showGDSLayoutImageData)  || hasFetchedImages) {
          setIsGDSImagesNeeded(true);
          return;
        }
        setLoading(true); // Set loading to true when fetching starts

          try {
          const imagesData = await fetchImageData(layoutDataList);
          if (imagesData?.status && imagesData?.status_code === 200) {
            setStage1GraphData(prevState => ({
              ...prevState,
              imagesData: imagesData?.images || [],
            }));
            setStage1GdsLayoutImageData(imagesData?.images || []);
            setShowGDSLayoutImageData(imagesData?.images)
            setHasFetchedImages(true);
            setGdsLayoutToggle(true);
          }
        } catch (error) {
          console.error("Error fetching images:", error);
        } finally {
          setLoading(false); // Set loading to false once fetching is complete (success or failure)
        }
      }
    }
  }, [isGDSImagesNeeded, stage1GraphData, getLayoutDataList, setStage1GraphData, stage1GdsLayoutImageData, setStage1GdsLayoutImageData, gdsLayoutToggle, showGDSLayoutImageData, setShowGDSLayoutImageData, hasFetchedImages, setHasFetchedImages, setGdsLayoutToggle]);

  const handleStage1GraphApplyFilter = useCallback(() => {
    setStage1GraphSelectedGdsCells(stage1GraphSelectedCellsRef.current);
  }, [setStage1GraphSelectedGdsCells]);

  // useEffect to trigger the function when context updates
  useEffect(() => {
    if (stage1GraphSelectedGdsCells !== null) {
      handleApplyFilterStage1();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage1GraphSelectedGdsCells]);

// This function handles the closing of the modal for large data.
const handleLargeDataModal = ()=>{
  fetchData();
  setConfirmLargeDataFetchModal(false)
}

  const updateChart = useCallback((dataToRender = stage1GraphData?.PEX_Consolidated) => {

    // handles when there is no data on chart.
    if (!dataToRender || dataToRender.length === 0) {
      const noChartData = {
        title: {
          show: true,
          textStyle: {
            color: '#bcbcbc'
          },
          text: 'No Data',
          left: 'center',
          top: 'center'
        },
        xAxis: {
          data: [],
        }, 
        yAxis: {
          data: [],
        }, 
        series: [
          {
            type: 'scatter',
            center: ['50%', '60%'],
            data: []  
          }
        ]
      };

      if(!myChart.current){
        myChart.current = echarts.init(chartDom?.current);
      }
     
      if (myChart?.current) {
        myChart.current.clear();  // Clear any old data or state
        myChart.current.setOption(noChartData); // Set the "No Data" message on the chart
      }
    
      return; // Exit function early if no data
    }

    if (!selectedOption1 || !selectedOption2 || !stage1GraphData) return;

    let xMin = Infinity, xMax = -Infinity, yMin = Infinity, yMax = -Infinity;
    const cellColorMap = {};
    const existingColors = [];
    const imageMap = {};

    // Populate imageMap only if images are needed
    if (isGDSImagesNeeded) {
      stage1GraphData?.imagesData?.forEach(image => {
        imageMap[image.file.replace(/_0$/, '')] = image.encodedImage;
      });
    }
    // Generate color mapping for cells
    dataToRender?.forEach(cell => {
      const cellColor = generateRandomColor(existingColors, cell?.name);
      cellColorMap[cell?.name] = cellColor;
      existingColors?.push(cellColor); // This helps with uniqueness checking, but colors are now stored persistently
    });

    // Determine global min/max values for missing filters
    let globalMinMax = {};

    dataToRender?.forEach(cell => {
      if (cell.data && Array.isArray(cell.data)) {
        cell.data.forEach(entry => {
          stage1Level2Filter.forEach(({ parameterName1 }) => {
            const value = Number(entry[parameterName1]);
            if (!isNaN(value)) {
              if (!globalMinMax[parameterName1]) {
                globalMinMax[parameterName1] = { min: value, max: value };
              } else {
                globalMinMax[parameterName1].min = Math.min(globalMinMax[parameterName1].min, value);
                globalMinMax[parameterName1].max = Math.max(globalMinMax[parameterName1].max, value);
              }
            }
          });
        });
      }
    });

    // Calculate min/max values for axes
    dataToRender?.forEach(cell => {
      if (cell.data && Array.isArray(cell.data)) {
        cell.data.forEach(entry => {
          const xValue = Number(entry[selectedOption2]);
          const yValue = Number(entry[selectedOption1]);

          // Ensure filters are correctly applied
          const passesFilters = stage1Level2Filter.every(({ parameterName1, value1, value2 }) => {
            const value = Number(entry[parameterName1]);
            const minValue = value1 !== null ? Number(value1) : globalMinMax[parameterName1]?.min;
            const maxValue = value2 !== null ? Number(value2) : globalMinMax[parameterName1]?.max;

            return !isNaN(value) && (value >= minValue) && (value <= maxValue);
          });

          // Ensure valid data points and filter conditions
          if (passesFilters && !isNaN(xValue) && !isNaN(yValue)) {
            xMin = Math.min(xMin, xValue);
            xMax = Math.max(xMax, xValue);
            yMin = Math.min(yMin, yValue);
            yMax = Math.max(yMax, yValue);
          }
        });
      }
    });

    // Chart option configuration
    const option = {
      tooltip: {
        trigger: 'item',
        confine: true,
        formatter: function (params) {
           // Check if item is in cart
          const isInCart = stage1GdsCartData?.includes(params?.name);
          // Only display image in tooltip if isGDSImagesNeeded is true
          const imageHtml = isGDSImagesNeeded && params?.data?.image
            ? `<img 
                src="data:image/png;base64,${params?.data?.image}" 
                alt="${params?.name}"
                style="width: 100%; height: 100%; object-fit: cover; border-bottom: 1px solid #ddd;"
                loading="lazy"
              />`
            : '';

          return `
            <div className="card" style="width: 12rem; border-radius: 12px; overflow: hidden;">
              ${imageHtml}
              <div class="card-body text-start" style="padding: 0.5rem;">
                <p class="card-text m-0" style="font-size: 0.8rem; font-weight: bold; color: #333;">${params?.name}</p>
                <p class="m-0" style="font-size: 0.8rem; color: #555;">${selectedOption2}: <span class="fw-bold">${params?.value[0]}</span></p>
                <p class="m-0" style="font-size: 0.8rem; color: #555;">${selectedOption1}: <span class="fw-bold">${params?.value[1]}</span></p>
                ${isInCart ? `<p class="m-0">🛒 In Cart</p>` : ''}
              </div>
            </div>
          `;
        },
        extraCssText: `
            width: 12rem;
            white-space: normal;
            padding: 0;
            overflow: hidden;`
      },
      toolbox: {
        feature: {
          saveAsImage: {
            type: 'png',
            name: projectName + '_stage1'
          },
          brush: {
            type: ['rect', 'polygon', 'keep', 'clear']
          },
          myApplyGraphFilterButton: {
            show: true,
            title: 'Apply Filter',
            icon: 'path://M3 9l4 4L17 5M3 12l4 4L17 8',
            onclick: handleStage1GraphApplyFilter
          },
        },
        top: -10,
      },
      brush: {
        toolbox: ['rect', 'polygon', 'keep', 'clear'],
        xAxisIndex: 'all',
        yAxisIndex: 'all'
      },
      grid: {
        left: '3%',
        right: '4%',
        top: '8%',
        bottom: '8%',
        containLabel: true,
        height: "75%"
      },
      xAxis: {
        name: selectedOption2,
        type: 'value',
        boundaryGap: false,
        nameLocation: 'middle',
        nameGap: 25,
        min: Number((xMin - (xMax - xMin) * 0.05).toFixed(4)),
        max: Number((xMax + (xMax - xMin) * 0.05).toFixed(4)),
        splitLine: { lineStyle: { type: 'dashed' } },
        axisLabel: { fontSize: 12, color: '#555' }
      },
      yAxis: {
        name: selectedOption1,
        type: 'value',
        boundaryGap: false,
        nameLocation: 'middle',
        nameGap: 40,
        min: Number((yMin - (yMax - yMin) * 0.05).toFixed(4)),
        max: Number((yMax + (yMax - yMin) * 0.05).toFixed(4)),
        splitLine: { lineStyle: { type: 'dashed' } },
        axisLabel: { fontSize: 12, color: '#555' }
      },
      legend: {
        data: Object.keys(cellColorMap),
        orient: 'horizontal',
        top: 'top',
        left: 'center',
        textStyle: { fontSize: 12, color: '#333' }
      },
      series: dataToRender?.map(cell => ({
        name: cell?.name,
        type: 'scatter',
        data: cell?.data
          ?.filter(entry => {
            return stage1Level2Filter.every(({ parameterName1, value1, value2 }) => {
              const value = Number(entry[parameterName1]);
              if (isNaN(value)) return false; // Ensure valid numerical values

              const minValue = value1 !== null ? Number(value1) : globalMinMax[parameterName1]?.min;
              const maxValue = value2 !== null ? Number(value2) : globalMinMax[parameterName1]?.max;

              return value >= minValue && value <= maxValue;
            });
          })
          .map(entry => {
            const image = isGDSImagesNeeded ? imageMap[entry['File']] || "" : null;
            // Check if the point is in the cart
            const isInCart = stage1GdsCartData?.includes(entry['File']);
            return {
              name: entry['File'],
              layoutData: entry['LayoutData'],
              value: [Number(entry[selectedOption2]), Number(entry[selectedOption1])],
              image: image,
              symbolSize: isInCart ? 14 : 10, // Highlight items in cart
              itemStyle: {
                borderColor: isInCart ? '#0acf00' : '#4682b4', // green border for cart items
                borderWidth: isInCart ? 2 : 0, // Border applied after padding
                opacity: 1, // Ensure visibility
              }
            };
          }),
        symbolSize: 10,
        itemStyle: {
          color: cellColorMap[cell?.name] || '#4682b4',
        },
      })),
      dataZoom: [
        {
          type: 'slider',
          show: true,
          xAxisIndex: [0],
          start: 0,
          end: 100,
          height: 18,
          bottom: 10
        },
        {
          type: 'slider',
          show: true,
          yAxisIndex: [0],
          start: 0,
          end: 100,
          width: 18,
          right: 10,
        },
        // Mouse wheel zooming for X-axis only
        {
          type: "inside",
          xAxisIndex: [0], // Affects only X-axis
          zoomOnMouseWheel: true, // Enable zooming on mouse wheel
          moveOnMouseWheel: false, // Disable panning using the mouse wheel
          moveOnMouseMove: true   // Enables dragging for zooming
        },
        // Mouse wheel zooming for Y-axis only
        {
          type: "inside",
          yAxisIndex: [0], // Affects only Y-axis
          zoomOnMouseWheel: true, // Enable zooming on mouse wheel
          moveOnMouseWheel: false, // Disable panning using the mouse wheel
          moveOnMouseMove: true   // Enables dragging for zooming
        }
      ]
    };
    // Initialize the chart only once
    if (!chartDom.current) {
      console.error("Chart DOM is not available");
      return;
    }

    if (!myChart?.current) {
      myChart.current = echarts.init(chartDom?.current);
    } else {
      myChart?.current.clear();
    }

    myChart?.current?.setOption(option, { notMerge: false, lazyupdate: false });
    myChart?.current?.dispatchAction({
      type: 'takeGlobalCursor',
      key: 'brush',
      brushOption: {
          brushType: '', // keeping empty so unselect bydefault'
          brushMode: 'keep'  // Ensures selections are kept
      }
    });

    // Event handler for brush selection (to capture the selected points)
    myChart?.current?.on('brushselected', function (params) {
      if (!params.batch[0]?.selected.length) return;
      const GDSCellNames = (params?.batch[0]?.selected?.flatMap(selection =>
        selection?.dataIndex?.map(index => option?.series[selection?.seriesIndex]?.data[index]?.name)
      ));
      stage1GraphSelectedCellsRef.current = GDSCellNames;
    });    
    
   
    myChart?.current?.off('click'); // Remove any existing click listeners

    myChart?.current?.on('click', async function (params) {

      myChart?.current?.dispatchAction({
        type: 'hideTip'
      });

      const { offsetX: xCoord, offsetY: yCoord } = params?.event;
      setSelectedCellNameOnGraph(params?.data?.name);
      setSelectedLayoutData([params?.data?.layoutData]);
      setMenuPosition({ x: xCoord, y: yCoord });
      setContextMenuOnStage1(true);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedOption1, selectedOption2, stage1GraphData, generateRandomColor, projectName, isGDSImagesNeeded, stage1Level2Filter, setContextMenuOnStage1, setSelectedCellNameOnGraph, setSelectedLayoutData, stage1GdsCartData]);

  const LargeDataFetchModalContent = {
    title: "Large Data Fetch Warning",
    body: (
      <>
        <p>
          Loading dataset with over 500 records. This might take some time to complete.
        </p>
      </>
    ),
    footer: (
      <>
        <button
          onClick={() => { handleProceedButton(); }}
          className="btn btn-primary w-50"
        >
          Ok
        </button>
      </>
    ),
  };

  const TooltipImageModalContent = {
    title: "Tooltip Images",
    body: (
      <>
        <p>
          Loading tooltip images for over 500 records. This may take some time. Do you wish to proceed and load tooltip images?
        </p>
      </>
    ),
    footer: (
      <>
        <div className="btn-group w-100" role="group" aria-label="Button group">
          <button
            onClick={() => { handleTooltipImageModalClose(); }}
            className="btn btn-secondary ms-0 ms-md-0 me-md-2 w-50"
          >
            No
          </button>
          <button
            onClick={() => { handleTooltipImageProceedButton(); }}
            className="btn btn-primary ms-0 w-50"
          >
            Yes
          </button>
        </div>

      </>
    ),
  };

  // Add this useEffect to reset graph data when project changes
  useEffect(() => {
    // Reset graph data when stage1Result changes (new project loaded)
    setStage1GraphData(null);
    setIsGDSImagesNeeded(false);
    setHasFetchedImages(false);
    setIsGDSImagesNeeded(false);
    setHasFetchedImages(false);
    setStage1GdsLayoutImageData([]);
    colorMap.current = {}; // Reset color mappings for new data
    
    // we dont want to add dependency on other states so added below line.
    // eslint-disable-next-line
  }, [stage1Result, setStage1GraphData]);

  // ** Modal turn On if totalImages > 500 **
  useEffect(() => {
    if (selectedOption1 && selectedOption2 && !stage1GraphData && totalImages > 500) {
      setConfirmLargeDataFetchModal(true);
    } else if (totalImages <= 500) {
      fetchData();
    }
  }, [selectedOption1, selectedOption2, stage1GraphData, totalImages, fetchData]);

  useEffect(() => {
    // This useEffect is triggered when `isGDSImagesNeeded` changes
    if (isGDSImagesNeeded && !hasFetchedImages && selectedOption1 && selectedOption2 && totalImages <= 500) {
      // If totalImages <= 500, directly fetch the tooltip images
      fetchDataTooltipImage();
    }
  }, [isGDSImagesNeeded, totalImages, hasFetchedImages, fetchDataTooltipImage, selectedOption1, selectedOption2]);


  useEffect(() => {
    if (columns) {
      setDropdownOptions(columns);
    }
  }, [columns]);

  // Handle resizing chart on window resize
  useEffect(() => {
    // Resize chart if it's available and active tab is 'gds-graph-tab'
    const resizeChart = () => {
      const activeTab = document.querySelector('.nav-tabs .active');
      if (myChart?.current && activeTab?.id === 'gds-graph-tab') {
        myChart.current.resize();
      }
    };

    // Handle tab change and resize chart only when 'gds-graph-tab' becomes active
    const handleTabChange = (e) => {
      if (e.target.id === 'gds-graph-tab') {
        resizeChart();
      }
    };

    // Attach event listener for tab change
    const tabContainer = document.querySelector('.nav-tabs');
    if (tabContainer) {
      tabContainer.addEventListener('shown.bs.tab', handleTabChange);
    }

    // Perform resize only if the tab is active and dependencies change
    resizeChart();

    // Add window resize listener to adjust chart size if tab is active
    const handleWindowResize = () => {
      resizeChart();
    };
    window?.addEventListener('resize', handleWindowResize);

    // Cleanup function to remove event listeners when the component is unmounted
    return () => {
      window?.removeEventListener('resize', handleWindowResize);
      if (tabContainer) {
        tabContainer.removeEventListener('shown.bs.tab', handleTabChange);
      }
    };
  }, [isSidebarCollapsed, terminalHeight, isGraphFilterSidebarOpen, myChart]);

  // I have kept this connect if case we need in future. earlier we were using this condition to plot graph. 
  // useEffect(() => {
  //   if (stage1GraphData && selectedOption1 && selectedOption2) {
  //     updateChart();
  //   }
  // }, [stage1GraphData, selectedOption1, selectedOption2, updateChart, stage1Level2Filter]);
  
  useEffect(() => {
    if (stage1Level2Filter) {
      updateChart();
    }
  }, [stage1Level2Filter, stage1TotalPexDataFilters, updateChart]);


  const filteredOptions1 = dropdownOptions?.filter(option => option !== selectedOption2);
  const filteredOptions2 = dropdownOptions?.filter(option => option !== selectedOption1);

  // getting numeric fields from pexConsolidated data for graph filters
  const findNumericFields = (data) => {
    if (!Array.isArray(data)) return null;

    const fields = data.reduce((fields, item) => {
      if (Array.isArray(item.data)) {
        item.data.forEach((subItem) => {
          Object.entries(subItem).forEach(([key, value]) => {
            if (typeof value === "number") {
              fields[key] = fields[key] || { min: value, max: value };
              fields[key].min = Math.min(fields[key].min, value);
              fields[key].max = Math.max(fields[key].max, value);
            }
          });
        });
      }
      return fields;
    }, {});

    // Check if all fields have the same min and max
    const allSame = Object.values(fields).every(({ min, max }) => min === max);
    return allSame ? null : fields;
  };


  // setting numeric fields for graph filters
  useEffect(() => {
    const numericFieldsResult = findNumericFields(stage1GraphData?.PEX_Consolidated);
    setNumericFields(numericFieldsResult);
  }, [stage1GraphData]);


  // reset graph filters
  const handleGraphResetFilters = () => {
    // Reset to initial values from numericFields
    const resetFilters = {};

    if (numericFields) {
      Object.entries(numericFields).forEach(([field, { min, max }]) => {
        resetFilters[field] = { min, max };
      });
    }
    setStage1Level2Filter([]);
    handleClearAllLevelFilter();
    
    setIsGraphFilterCleared(true);
    updateChart();
  };

  const handleSliderChange = (field, newValue) => {
    const [minValue, maxValue] = newValue;
    setStage1GraphSelectedGdsCells(null);
    setIsGraphFilterCleared(true);
    setStage1Level2Filter((prev) => {
      // Ensure it's always an array and create a new reference
      const updatedFilters = Array.isArray(prev) ? [...prev] : [];

      const existingIndex = updatedFilters.findIndex((f) => f.parameterName1 === field);

      if (existingIndex !== -1) {
        updatedFilters[existingIndex] = {
          parameterName1: field,
          parameterName2: null,
          filterationValue: "between",
          value1: minValue,
          value2: maxValue,
        };
      }
      else {
        updatedFilters.push({
          parameterName1: field,
          parameterName2: null,
          filterationValue: "between",
          value1: minValue,
          value2: maxValue,
        });
      }

      // Return a new array reference to trigger re-render
      return [...updatedFilters];
    });
  };

  const toggleGraphFilterSidebar = () => {
    if ((!isSidebarCollapsed && !isGraphFilterSidebarOpen) || (isSidebarCollapsed && isGraphFilterSidebarOpen)) {
      toggleSidebar();
      setIsGraphFilterSidebarOpen(!isGraphFilterSidebarOpen);
    }
    else if ((isSidebarCollapsed && !isGraphFilterSidebarOpen) || (!isSidebarCollapsed && isGraphFilterSidebarOpen)) {
      setIsGraphFilterSidebarOpen(!isGraphFilterSidebarOpen);
    }
  };

  // updating filterequest parameter as soon as stage1level2filter updates
  useEffect(() => {
    // below need to check if level1 filter is applied then handle else act accordingly 
    let filterParameters;
    // we send only elements in filter on which filter is applied i.e if selectall is true in parameter variation we do not consider it for filter
    if (isFilterApplied) {
      filterParameters = techVariationFilterSelectedParameter?.filter((parameter) => parameter?.selectAllValue === false)
    }
    const filterRequest = {

      cellSelectAll: isFilterApplied ? stage1IsAllCellSelectedForFilter : true,// default sending all cells for filtering
      cells: isFilterApplied ? stage1FilterSelectedCells : stage1FilteredLevel2Cells?.length > 0 ? stage1FilteredLevel2Cells : [],

      filterParametersName: {
        filterLevel1: (isFilterApplied && filterParameters?.length > 0) ? filterParameters : null,
        filterLevel2: stage1Level2Filter ? stage1Level2Filter : null, // here compulsory level2 filter will set
      }

    };
    setFilterRequestParameter(filterRequest);

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    stage1Level2Filter])

  return (
    <div className="position-relative bg-white h-100">
    {loadingRef?.current && (
        <div className="d-flex justify-content-center align-items-center" style={{ height: "100%" }}>
          <div className="spinner-border" role="status">
            <span className="sr-only">Loading...</span>
          </div>
        </div>
      )}
      {/* Main Content */}
      <div className="container-fluid h-100">
        <div className="row h-100">
          {/* Graph View Section - col-9 */}
          <div className={`${isGraphFilterSidebarOpen ? 'col-9' : 'col-12'} d-flex p-2 flex-column`}>
            {/* Controls Section */}
            {stage1GraphData?.PEX_Consolidated?.length > 0 && (
            <div className="row g-3 align-items-center justify-content-center" id="leftgraphview">
            {/* Tooltip Images Toggle */}
            <div className={`${isGraphFilterSidebarOpen && !isSidebarCollapsed ? 'col-md-4' : 'col-md-3'} col-12`}>
              <div className="bg-white d-flex align-items-center px-3 py-2 border rounded" style={{ height: '38px' }}>
                <div className="form-check form-switch d-flex align-items-center m-0">
                  <input
                    className="form-check-input shadow-none me-2"
                    type="checkbox"
                    role="switch"
                    checked={isGDSImagesNeeded}
                    disabled={!(selectedOption1 && selectedOption2) && !stage1GraphData}
                    onChange={handleGDSTooltipImageToggle}
                    id="stage-1-tooltip-images-toggle"
                    style={{ cursor: 'pointer' }}
                  />
                  <label className="form-check-label" htmlFor="stage-1-tooltip-images-toggle">
                    Show GDS Layouts
                  </label>
                  {loading && <div className="spinner-border spinner-border-sm ms-2" role="status"><span className="visually-hidden">Loading...</span></div>}
                </div>
              </div>
            </div>

            {/* Y-Axis and X-Axis Dropdowns */}
            <div className={`${isGraphFilterSidebarOpen && !isSidebarCollapsed ? 'col-md-8' : 'col-md-6'} col-12 d-flex gap-3`}>
              <select
                className="form-select flex-grow-1"
                id="stage-1-y-axis-select"
                value={selectedOption1}
                onChange={(e) => setSelectedOption1(e.target.value)}
                disabled={loading}
              >
                <option value="" disabled>Select Y-Axis</option>
                {filteredOptions1.map((option, index) => (
                  <option key={index} value={option}>{option}</option>
                ))}
              </select>

              <select
                className="form-select flex-grow-1"
                id="stage-1-x-axis-select"
                value={selectedOption2}
                onChange={(e) => setSelectedOption2(e.target.value)}
                disabled={loading}
              >
                <option value="" disabled>Select X-Axis</option>
                {filteredOptions2.map((option, index) => (
                  <option key={index} value={option}>{option}</option>
                ))}
              </select>

              {/* Filter Button */}
              {numericFields && (
                <button
                  id="stage-1-graph-filter-button"
                  className="btn app-primary-button-color d-flex align-items-center justify-content-center"
                  onClick={toggleGraphFilterSidebar}
                  style={{ height: '38px', width: '42px' }}
                  data-tooltip-id="stage-1-graph-filter-btn-tooltip"
                  data-tooltip-content="Filters"
                  data-tooltip-place="top"
                >
                  <FontAwesomeIcon icon={faFilter} className="text-white" />
                  <ReactTooltip id="stage-1-graph-filter-btn-tooltip" style={{ zIndex: 9999 }} />
                </button>
              )}
            </div>
          </div>
            ) }

            {/* Chart Area */}
            <div ref={chartDom} className={`${isGraphFilterSidebarOpen ? 'col-9' : 'col-12'} row overflow-hidden`} id="stage-1-graph" style={{ position: 'absolute', height: '83%', bottom: '0' }} >
              {contextMenuOnStage1 &&
                (<ContextMenu
                  show={contextMenuOnStage1}
                  menuOptions={ContextMenuData}
                  onHide={() => setContextMenuOnStage1(false)}
                  position={menuPosition}
                  containerRef={chartDom}
                />)
              }
            </div>

            {viewLayoutLoading && (
              <div className="h-100 w-100 d-flex justify-content-center align-items-center">
                <div className="spinner-border ms-2" style={{ zIndex: 999 }} role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
              </div>
            )}
          </div>
          {/* Filter Sidebar - col-3 */}
          <div className={`app-secondary-color p-2 h-100 overflow-auto ${isGraphFilterSidebarOpen ? 'col-3 d-block' : 'd-none'}`}>
            <div className="d-flex justify-content-between align-items-center mb-4">
              <h5 className="m-0 text-dark font-weight-bold">Filters</h5>
              <div>
                {/* apply filter api call button */}
                {stage1Level2Filter.length > 0 && (
                  <>
                    {/* <button
                  className="btn btn-link button-primary-color p-0 me-3"
                  id="stage-1-graph-filter2-sync-across-tab-btn"
                  onClick={handleApplyFilterStage1}
                  style={{ transition: 'color 0.2s ease' }}
                  //onMouseEnter={(e) => e.target.style.color = '#007bff'}  
                  //onMouseLeave={(e) => e.target.style.color = 'inherit'}
                  data-tooltip-id="stage-1-graph-filter2-sync-across-tab-btn-tooltip"
                  data-tooltip-content="Sync Filtered Data Across Tabs"
                  data-tooltip-place="top"
                >
                  <FontAwesomeIcon icon={faRotate} size="md" />
                  <ReactTooltip id="stage-1-graph-filter2-sync-across-tab-btn-tooltip" style={{ zIndex: 9999 }} />
                </button> */}

                    {/* clear filters button */}
                    <button
                      className="btn btn-link button-primary-color p-0 me-3"
                      id="stage-1-graph-filter-reset-btn"
                      onClick={handleGraphResetFilters}
                      style={{ transition: 'color 0.2s ease', color: 'app-secondary-color' }}
                      // onMouseEnter={(e) => e.target.style.color = '#007bff'}  
                      // onMouseLeave={(e) => e.target.style.color = 'inherit'}
                      data-tooltip-id="stage-1-graph-filter-reset-btn-tooltip"
                      data-tooltip-content="Clear Filters"
                      data-tooltip-place="top"
                    >
                      <FontAwesomeIcon icon={faTrash} size="md" />
                      <ReactTooltip id="stage-1-graph-filter-reset-btn-tooltip" style={{ zIndex: 9999 }} />
                    </button>
                  </>
                )}
                <button
                  className="btn btn-link text-dark p-0"
                  id="stage-1-graph-filter-close-btn"
                  onClick={toggleGraphFilterSidebar}
                  style={{ transition: 'color 0.2s ease' }}
                  // onMouseEnter={(e) => e.target.style.color = '#ff4d4d'}
                  //onMouseLeave={(e) => e.target.style.color = 'inherit'}
                  data-tooltip-id="stage-1-graph-filter-close-btn-tooltip"
                  data-tooltip-content="Close"
                  data-tooltip-place="top"
                >
                  <FontAwesomeIcon icon={faTimes} size="lg" />
                  <ReactTooltip id="stage-1-graph-filter-close-btn-tooltip" style={{ zIndex: 9999 }} />
                </button>
              </div>
            </div>
            <div className="px-2 mx-3">
              {numericFields && Object.entries(numericFields).map(([field, { min, max }]) => {
                const marks = [
                  { value: min, label: `${min}` },
                  { value: max, label: `${max}` },
                ];
                return (
                  <div key={field} className="my-3">
                    <label className="fw-bold d-block text-muted text-center">{field}</label>
                    <Slider
                      className="p-1 graph-filter-range-slider"
                      // defaultValue={[min, max]}
                      value={[
                        stage1Level2Filter.find(f => f.parameterName1 === field)?.value1 ?? min,
                        stage1Level2Filter.find(f => f.parameterName1 === field)?.value2 ?? max,
                      ]}
                      onChange={(e, newValue) => handleSliderChange(field, newValue)}
                      min={min}
                      max={max}
                      step={0.0001}
                      valueLabelDisplay="auto"
                      marks={marks}
                      valueLabelFormat={(value) => `${value}`}
                    />
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Modals */}
      <ModalComponent
        id="stage-1-confirm-large-data-fetch-modal"
        size="md"
        show={confirmLargeDataFetchModal}
        handleClose={handleLargeDataModal}
        modalContent={LargeDataFetchModalContent}
        modalCSSClass={"overflow-hidden"}
      />
      <ModalComponent
        id="stage-1-confirm-tooltip-image-fetch-modal"
        size="md"
        show={confirmTooltipImageDataFetchModal}
        handleClose={() => setConfirmTooltipImageDataFetchModal(false)}
        modalContent={TooltipImageModalContent}
        modalCSSClass={"overflow-hidden"}
      />

    </div>
  );
};

export default LayoutGraphDataStage1;