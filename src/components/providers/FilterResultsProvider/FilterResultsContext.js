 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: EditProjectContext.js  
 * Description: This file is responsible to save edited project data in context. 
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

import { createContext, useContext } from 'react';

export const FilterResultsContext = createContext({
    stage1FilterSelectedCells:[],
    setStage1SelectedFilterCells:()=>null,
    stage1SelectedFilterParameters:[],
    setStage1SelectedFilterParameters:()=>null,
    stage1IsAllCellSelectedForFilter: true, 
    setStage1IsAllCellSelectedForFilter : () => null,
    techVariationFilterSelectedParameter:{}, 
    setTechVariationFilterSelectedParameter:()=>null,
    filterRequestParameter:{},
    isStage1FilterApplied: true,
    setIsStage1FilterApplied:()=>null,
    isStage2FilterApplied: true,
    setIsStage2FilterApplied:()=> null,
    setFilterRequestParameter:()=>null,
    stage1TotalPexDataFilters: {},
    setStage1TotalPexDataFilters: () => null,
    stage1Level2Filter:[],
    setStage1Level2Filter:()=>null,
    stage2TotalPexDataFilters: {},
    setStage2TotalPexDataFilters: () => null,
    stage2Level2Filter:[],
    setStage2Level2Filter:()=>null,
    clearFilterResultsContext:()=>null,
    isFilterApplied:false, 
    setIsFilterApplied:()=> null,
    stage1GdsCartData:null, 
    setStage1GdsCartData:()=> null,
    stage2GdsCartData: null,
    setStage2GdsCartData: ()=> null,
    isGraphFilterCleared: false,
    setIsGraphFilterCleared: () => null,
    selectedDownloadOption: 3, // 3-> to make download all default
    setSelectedDownloadOption: ()=> null,
    stage1FilteredLevel2Cells : null , 
    setStage1FilteredLevel2Cells:()=>null,
    stage2FilteredLevel2Cells : null, 
    setStage2FilteredLevel2Cells : ()=>null,
    isStage1Level2FilterApplied :false, 
    setIsStage1Level2FilterApplied :() => null,
    isStage2Level2FilterApplied : false, 
    setIsStage2Level2FilterApplied : () => null,
    stage1GraphSelectedGdsCells : false,
    setStage1GraphSelectedGdsCells : () => null,
    stage2GraphSelectedGdsCells : false,
    setStage2GraphSelectedGdsCells : () => null,
})

export const useFilterResultsContext = () => {
    return useContext(FilterResultsContext);
};

