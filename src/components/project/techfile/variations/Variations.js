 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: Variations.js  
 * Description: This file is responsible show variations data 
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
import { useTechFileContext } from "../../../providers/TechFileProvider/TechFileContext";
import AccordionComponent from "../../../utils/Accordian/AccordianComponent";
import VariationTable from "./VariationTable";


const Variations = () => {
  const { techFileData } = useTechFileContext();
  const [variationSections, setVariationSections] = useState([]);
 

  //below use effect for rendering accordian data dynamically

  useEffect(() => {
    let sectionsData = [];
    //creating section to be rendered in accordian for variation tab
    // will check if filecontent has data then only will display accordian else no Content display 
    if(techFileData?.data?.FileContent?.length === 0 || techFileData?.data?.FileContent === null){
    
      setVariationSections(null)
    }else{
    techFileData?.data?.FileContent?.forEach((techParameterData) => {
   
      if (techParameterData?.displayName === "Permutation" && techParameterData?.uiVisible) {
       
        //grouping values based on parameter name 
        const permutationGroupedByParameter = techParameterData?.data?.reduce((acc, parameter) => {
         // const paramName = parameter?.parameterName;
          const paramName = parameter?.parameterDisplayName; // we want display name to be displayed
          if (!acc[paramName]) {
            acc[paramName] = [parameter];
          } else {
            acc[paramName].push(parameter);
          }
          
          return acc;
        }, {});

        //looping through grouped object to create table data
        for (const [key, value] of Object.entries(permutationGroupedByParameter)) {

          let variationTableContentProps;
          //if (key !== 'other') {
          if (key !== 'Design Rules') {
            let metaDataByParamName = {};
            let tableDataValueForKey = value?.map((item) => {
              //handling adding of default value in table data
             // Extract meta data for this parameter
            metaDataByParamName[item?.displayName] = {
              negativeStartAllowed: item?.negativeStartAllowed,
              negativeEndAllowed: item?.negativeEndAllowed,
              stepperFloat: item?.stepperFloat,
              stepper: item?.stepper,
              defaultStartValue:item?.defaultStartValue,
              defaultEndValue:item?.defaultEndValue,
              minStart: item?.minStart,
              maxStart: item?.maxStart,
              minEnd: item?.minEnd,
              maxEnd: item?.maxEnd,
              startPercentage: item?.startPercentage,
              endPercentage: item?.endPercentage
          };
              let variationTableData = Array.isArray(item?.displayName) ? [...item?.displayName] : [item?.displayName];
              variationTableData.push({"defaultValue":item?.defaultValue || [0]})
              variationTableData.push(item?.value?.start);
              variationTableData.push(item?.value?.end);
              variationTableData.push(item?.value?.step);
            //  variationTableData = variationTableData.concat(Object.values(item?.value));
             //return [{ variationTableData : variationTableData , parameterMetaValues}]
       
             return variationTableData
            })

            variationTableContentProps = {
              tableHeader: ["Parameters","DefaultValue","Start","End","Step"],
              tableData: tableDataValueForKey,
              tableParameterName: key,
              metaDataByParamName
            }
            sectionsData.push({ title: key, content: <VariationTable tableContent={variationTableContentProps} /> })

          } else {
            //if parameter is of type other handling data here
            let tableDataValueKeyOther = value?.map((item) => {
              //checking if option is null or not 
              if(item?.options !== null){
                  //if options is null value displayed in variations is from options
                  return [item?.displayName,{"isOfDropDownType":true},{"defaultValue":item?.defaultValue[0] || [0]},{"selectedValues":[...item?.value] ||[]},...item?.options]
              } else if(Array.isArray(item?.value) && item?.options === null) {
                //handling addition of default value to other type parameter whose value is an array & options is null

                return [item?.displayName,{"isOfDropDownType":true},{"defaultValue":item?.defaultValue[0] || [0]},...item?.value]
              }else{
                let variationData = [];
                variationData?.push(item?.displayName);
                variationData.push({"defaultValue":item?.defaultValue});
               
              return variationData.concat(Object.values(item?.value))
               }
            })
            
            variationTableContentProps = {
              tableHeader: ["Parameters","DefaultValue","Start","End","Step"],
              tableData: tableDataValueKeyOther,
              tableParameterName: key
            }
            sectionsData.push({ title: key, content: <VariationTable tableContent={variationTableContentProps} /> })
          }
        }

        setVariationSections(sectionsData);

      }else if(techParameterData?.displayName === "Permutation" && !techParameterData?.uiVisible) {
        // when it is uivisible false it will not display anything in UI
        setVariationSections(null);
      }
    });
  }

  }, [techFileData])
  return <AccordionComponent sections={variationSections}></AccordionComponent>;
};

export default Variations;
