 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: Parameters.js  
 * Description: This file is responsible to select and show tech data. 
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

import React, { useEffect, useState } from "react";
import AccordianComponent from "../../../utils/Accordian/AccordianComponent";
import { useTechFileContext } from "../../../providers/TechFileProvider/TechFileContext";
import TableComponent from "./ParameterTableComponent";
import useTechFileParameterHidingRuleHook from ".././../../../Hooks/techFileParameterHidingRuleHook/techFileParameterHidingRuleHook";

const Parameters = () => {

  const {techFileData} = useTechFileContext();
  const [sections,setSections] = useState([]);

  const {shouldParameterBeHidden} = useTechFileParameterHidingRuleHook();

  /* type of tableComponent props const tableContent = {
    tableHeader: [],
    tableData: layerMapTableContent,
    tableState: tableState,
    tableEditable: false,
  }; */

  useEffect(()=>{
    let sectionsData = [];
    //creating section to be rendered in accordian for parameter tab
    // checking if FileContent has some data or it is null & handling situation
    if(techFileData?.data?.FileContent === null){
      setSections(null);
    }else{
    // if file content is not null setting data accordingly
     techFileData?.data?.FileContent?.forEach((techParameterData) => {
      //permututation is not to be included in parameters tab so excluding it 
      //finding techparameter data which are ui visible
      const UIVisibleInternalParametersCount = techParameterData?.data?.filter((internalParameter)=>internalParameter?.uiVisible && !shouldParameterBeHidden(internalParameter))
      if(techParameterData?.uiVisible && Array.isArray(techParameterData?.data)  && techParameterData?.displayName !== "Permutation" && UIVisibleInternalParametersCount?.length > 0){ 
        const tableContentProps = {
          tableHeader: techParameterData?.header !== null ? techParameterData?.header : [], // if header is passed then handling header display else setting as null so that no data is displayed
          tableData: techParameterData?.data,
          tableParameterName: techParameterData?.name,
          tableEditable: techParameterData?.parameterSupport,
          tableSupportsVariation: techParameterData?.supportsVariations,
          tableParameterDisplayName : techParameterData?.displayName,
        }      
        sectionsData.push({title: techParameterData?.displayName, content:<TableComponent tableContent={tableContentProps} />});
      }
    });
    setSections(sectionsData);
  }

  //disblaing since i dont require shouldParameterBeHidden check to be run everytime
  // eslint-disable-next-line react-hooks/exhaustive-deps
  },[techFileData])

  return <AccordianComponent sections={sections} />;
};

export default Parameters;
