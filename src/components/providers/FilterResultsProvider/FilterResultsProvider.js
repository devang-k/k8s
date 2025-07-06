 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: EditProjectProvider.js  
 * Description: This file is responsible to share edited project data to other components within the application. 
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

import React, { useMemo, useState,useCallback } from "react";
import { FilterResultsContext } from "./FilterResultsContext";

export const FilterResultsProvider = ({ children }) => {
    const [stage1FilterSelectedCells, setStage1SelectedFilterCells] = useState([]);//handles cells selected by user while filtering 
    const [stage1SelectedFilterParameters, setStage1SelectedFilterParameters] = useState([]);//handles parameters selected by user while filtering
    const [stage1IsAllCellSelectedForFilter, setStage1IsAllCellSelectedForFilter] = useState(true); // it sets for filter level1 if all cells selected for filtering
    const [techVariationFilterSelectedParameter, setTechVariationFilterSelectedParameter] = useState();// it stores value for filters selected for tech variation
    const [ filterRequestParameter,setFilterRequestParameter] = useState(null);// it stores filter request parameter
    const [ isStage1FilterApplied, setIsStage1FilterApplied ] = useState(false);// stores if filter on stage1 is applied
    const [ isStage2FilterApplied, setIsStage2FilterApplied ] = useState(false);// stores if filter on stage2 applied
    const [isFilterApplied, setIsFilterApplied] = useState(false);// will handle state for checking if any filter is applied 
    const [stage1GdsCartData, setStage1GdsCartData] = useState(null);// it stores data for gds added to cart
    const [stage1TotalPexDataFilters, setStage1TotalPexDataFilters ] = useState({}); // it stores total stage 1 Pex Data Filters
    const [stage2TotalPexDataFilters, setStage2TotalPexDataFilters ] = useState({}); // it stores total stage 2 Pex Data Filters
    const [stage1Level2Filter, setStage1Level2Filter] = useState([]);// it stores value for stage 1 level 2 filters
    const [stage2Level2Filter, setStage2Level2Filter] = useState([]);// it stores value for stage 2 level 2 filters
    const [stage2GdsCartData, setStage2GdsCartData] = useState(null);// it stores data for gds added to cart for stage2(hyperexpressivity)
    const [isGraphFilterCleared, setIsGraphFilterCleared] = useState(false); // it tracks that state when graph filter is trggered
    const [selectedDownloadOption , setSelectedDownloadOption] = useState(3);// {1:"Cart", 2:"Filter", 3:"All", 4:"Summary and linkage file"}
    const [stage1FilteredLevel2Cells , setStage1FilteredLevel2Cells] = useState(null);// filtered level 2 cells for stage 1
    const [stage2FilteredLevel2Cells , setStage2FilteredLevel2Cells] = useState(null);// filtered level 2 cells for stage 2
    const [isStage1Level2FilterApplied , setIsStage1Level2FilterApplied] = useState(false); // it sets to true when user applies stage1 level2 filter sync
    const [isStage2Level2FilterApplied , setIsStage2Level2FilterApplied] = useState(false); // it sets to true when user applies satge2 level2 filter sync
    const [stage1GraphSelectedGdsCells, setStage1GraphSelectedGdsCells] = useState(null); // it sets stage 1 gds cells selected in graph
    const [stage2GraphSelectedGdsCells, setStage2GraphSelectedGdsCells] = useState(null); // it sets stage 2 gds cells selected in graph

    // Function to clear all filter data (resets all states) common function which will clear all filters
    const clearFilterResultsContext = useCallback(() => {
        setStage1FilteredLevel2Cells(null);
        setStage2FilteredLevel2Cells(null);
        setStage1SelectedFilterCells([]);
        setStage1SelectedFilterParameters([]);
        setStage1IsAllCellSelectedForFilter(true);
        setTechVariationFilterSelectedParameter();
        setFilterRequestParameter();
        setIsStage1FilterApplied(false);
        setIsStage2FilterApplied(false);
        setIsFilterApplied(false);
        setStage1GdsCartData(null);
        setStage1TotalPexDataFilters({});
        setStage1Level2Filter([]);
        setStage2TotalPexDataFilters({});
        setStage2Level2Filter([]);
        setStage2GdsCartData(null);
        setSelectedDownloadOption(3);
        setIsGraphFilterCleared(false);
        setIsStage1Level2FilterApplied(false);
        setIsStage2Level2FilterApplied(false);
        setStage1GraphSelectedGdsCells(null);
        setStage2GraphSelectedGdsCells(null);
    }, []);

    const value = useMemo(() => {
        return {
            isStage2Level2FilterApplied , 
            setIsStage2Level2FilterApplied,
            stage1FilteredLevel2Cells , 
            setStage1FilteredLevel2Cells,
            stage2FilteredLevel2Cells , 
            setStage2FilteredLevel2Cells,
            selectedDownloadOption, 
            setSelectedDownloadOption,
            stage1FilterSelectedCells,
            setStage1SelectedFilterCells,
            stage1SelectedFilterParameters,
            setStage1SelectedFilterParameters,
            stage1IsAllCellSelectedForFilter, 
            setStage1IsAllCellSelectedForFilter,
            techVariationFilterSelectedParameter, 
            setTechVariationFilterSelectedParameter,
            filterRequestParameter,
            setFilterRequestParameter,
            isStage1FilterApplied, 
            setIsStage1FilterApplied,
            isStage2FilterApplied, 
            setIsStage2FilterApplied,
            isFilterApplied, 
            setIsFilterApplied,
            stage1GdsCartData, 
            setStage1GdsCartData,
            stage1TotalPexDataFilters,
            setStage1TotalPexDataFilters,
            stage1Level2Filter,
            setStage1Level2Filter,
            stage2TotalPexDataFilters,
            setStage2TotalPexDataFilters,
            stage2Level2Filter,
            setStage2Level2Filter,
            stage2GdsCartData,
            setStage2GdsCartData,
            isGraphFilterCleared,
            setIsGraphFilterCleared,
            isStage1Level2FilterApplied,
            setIsStage1Level2FilterApplied,
            stage1GraphSelectedGdsCells,
            setStage1GraphSelectedGdsCells,
            stage2GraphSelectedGdsCells,
            setStage2GraphSelectedGdsCells,
            clearFilterResultsContext // include funciton in context
        }
    }, [
        
        clearFilterResultsContext,
        isStage2Level2FilterApplied , 
        setIsStage2Level2FilterApplied,
        isStage1Level2FilterApplied , 
        setIsStage1Level2FilterApplied,
        stage1FilteredLevel2Cells , 
        setStage1FilteredLevel2Cells,
        stage2FilteredLevel2Cells , 
        setStage2FilteredLevel2Cells,
        selectedDownloadOption , 
        setSelectedDownloadOption,
        stage2GdsCartData,
        setStage2GdsCartData,
        stage1GdsCartData, 
        setStage1GdsCartData,
        isFilterApplied, 
        setIsFilterApplied,
        isStage1FilterApplied, 
        setIsStage1FilterApplied,
        isStage2FilterApplied, 
        setIsStage2FilterApplied,
        stage1FilterSelectedCells,
        setStage1SelectedFilterCells,
        stage1SelectedFilterParameters,
        setStage1SelectedFilterParameters,
        stage1IsAllCellSelectedForFilter, 
        setStage1IsAllCellSelectedForFilter,
        techVariationFilterSelectedParameter, 
        setTechVariationFilterSelectedParameter,
        filterRequestParameter,
        setFilterRequestParameter,
        stage1TotalPexDataFilters,
        setStage1TotalPexDataFilters,
        stage1Level2Filter,
        setStage1Level2Filter,
        stage2TotalPexDataFilters,
        setStage2TotalPexDataFilters,
        stage2Level2Filter,
        setStage2Level2Filter,
        isGraphFilterCleared,
        setIsGraphFilterCleared,
        stage1GraphSelectedGdsCells,
        setStage1GraphSelectedGdsCells,
        stage2GraphSelectedGdsCells,
        setStage2GraphSelectedGdsCells
        ]);

    return (
        <FilterResultsContext.Provider value={value}>{children}</FilterResultsContext.Provider>
    )
}