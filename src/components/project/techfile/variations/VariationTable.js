
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: VariationTable.js  
 * Description: This file is table component to show variations data in table 
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
import BootstrapTable from "react-bootstrap/Table";
import { useTechFileContext } from "../../../providers/TechFileProvider/TechFileContext";
import Form from 'react-bootstrap/Form'

const VariationTable = ({ tableContent }) => {

    const { tableHeader, tableData, tableParameterName, metaDataByParamName } = tableContent;
    const { techFileData, setTechFileData, setIsTechDataChanged, techParameterValueError, setTechParameterValueError } = useTechFileContext();
    const [colSpanLength, setColSpanLength] = useState(1);

    const handleInputChange = useCallback((updatedValue, dataUpdating, field, itemAdded) => {
        //converting updated value to number
        const updatedVal = updatedValue;

        // Clone techFileData to avoid mutating original state
        const updatedTechFileData = JSON.parse(JSON.stringify(techFileData));

        // Find the permutation object and update its specific row/parameter
        const updatedFileContent = updatedTechFileData?.data?.FileContent?.map((item) => {
            if (item?.name === "permutation") {
                // Loop through the data inside permutation to find the correct row
                const updatedPermutationData = item?.data?.map((itemInner) => {
                    //check which accordian is updating
                    //first to check if parameter is something other than other
                    if (tableParameterName !== 'Design Rules') {
                        //checking value in techfile json attribute name
                        let attributeNameUpdatingInTechJSON = Array.isArray(itemInner?.displayName) ? itemInner?.displayName[0] : itemInner?.displayName;
                        //checking the attribute value to get row that is to be updated in techjson
                        if (attributeNameUpdatingInTechJSON === dataUpdating[0]) {
                            // Update the specific part of the value object (start, end, step)
                            return {
                                ...itemInner,
                                value: {
                                    ...itemInner.value,
                                    [field]: updatedVal
                                }
                            };
                        }

                    } else {
                        //handle the else part to handle item other
                        //compare with name key in techfile json

                        //checking the value parameter name at place 1 
                        if (field === null && itemInner?.options !== null) {
                            // Handle case when checkbox is turned ON or OFF
                            if (updatedValue) {

                                // Ensure that the value is an array, and add the new item if it's not already present
                                // checking if item updating & value we are reading is same
                                if (itemInner?.displayName === dataUpdating?.[0]) {
                                    let updatedValueArray = Array.isArray(itemInner.value) ? [...itemInner.value] : [];

                                    if (!updatedValueArray?.includes(itemAdded)) {
                                        updatedValueArray?.push(itemAdded);
                                    }

                                    return {
                                        ...itemInner,
                                        value: updatedValueArray
                                    };
                                }
                            } else if (!updatedValue) {

                                // Remove the itemAdded from the array if it exists
                                //it updates array only item that is being updated
                                if (itemInner?.displayName === dataUpdating?.[0]) {
                                    let updatedValueArray = Array.isArray(itemInner?.value) && itemInner?.value?.filter(val => val !== itemAdded);

                                    return {
                                        ...itemInner,
                                        value: updatedValueArray
                                    };
                                }
                            }
                        }
                        else if (itemInner?.displayName === dataUpdating[0].toString()) {
                            // Update the specific part of the value object (start, end, step)
                            return {
                                ...itemInner,
                                value: {
                                    ...itemInner?.value,
                                    [field]: updatedVal
                                }
                            };
                        }

                    }

                    return itemInner; // Return unchanged row if not updating
                });
                return {
                    ...item,
                    data: updatedPermutationData
                };
            }
            return item;
        });

        // Update the context value using setTechFileData
        setTechFileData(prevState => ({
            ...prevState,
            data: {
                ...prevState.data,
                FileContent: updatedFileContent
            }
        }));
        setIsTechDataChanged(true);
    }, [techFileData, setTechFileData, tableParameterName, setIsTechDataChanged]);

    // below function handles validation on step, start & end values on keyup , commenting below code since removing validation as of now
    // const handleValidationOnVariationInput = (inputValue, variationValueInRow, index, step) => {
    //     // checking validation for step key in variation
    //     if (index === variationValueInRow.length - 1) {
    //         //if value is less than 1 then chaning value to default 1 value
    //         if (inputValue.target.value < step) { inputValue.target.value = step }
    //     }
    // }

    const handleMinValueForInputType = (index, variationValueInRow) => {
        
        //(index=== variationValueInRow?.length-1)?metaDataByParamName[variationValueInRow[0]]?.stepper || 1:((index=== variationValueInRow?.length -2)? variationValueInRow[variationValueInRow?.length-3] +1:0)
        if (index === variationValueInRow?.length - 1) {
            // for step min value
            return metaDataByParamName[variationValueInRow[0]]?.stepper || 1;
        } else if (index === variationValueInRow?.length - 2) {
            //for end min value
            //return variationValueInRow[variationValueInRow?.length - 3] + 1
            //calculating based on percent range received as per business rule
          
           const endPercentage = metaDataByParamName[variationValueInRow[0]]?.endPercentage;
            if(!endPercentage ){
             
                return metaDataByParamName[variationValueInRow[0]]?.minEnd || variationValueInRow[variationValueInRow?.length - 3] + 1;
            }else {
                let minVal = metaDataByParamName[variationValueInRow[0]]?.defaultEndValue - ((metaDataByParamName[variationValueInRow[0]]?.endPercentage/100) * metaDataByParamName[variationValueInRow[0]]?.defaultEndValue);
                return minVal;
                }
        } else if (index === variationValueInRow?.length - 3) {
            const startPercentage =  metaDataByParamName[variationValueInRow[0]]?.startPercentage;
    
            if(!startPercentage){
                return metaDataByParamName[variationValueInRow[0]]?.minStart;
            }else{
            // for start min value
            let minStartValue = metaDataByParamName[variationValueInRow[0]]?.defaultStartValue - ((metaDataByParamName[variationValueInRow[0]]?.startPercentage/100) * metaDataByParamName[variationValueInRow[0]]?.defaultStartValue);
            return minStartValue;
            }
        }
    };

    const handleMaxValueForInputType = (index, variationValueInRow) => {
        if (index === variationValueInRow?.length - 2) {    
            //for end max value 
            const endPercentage = metaDataByParamName[variationValueInRow[0]]?.endPercentage;
            if(!endPercentage){
                return metaDataByParamName[variationValueInRow[0]]?.maxEnd || undefined;
            }else{
            let maxEndVal = metaDataByParamName[variationValueInRow[0]]?.defaultEndValue +((metaDataByParamName[variationValueInRow[0]]?.endPercentage/100) * metaDataByParamName[variationValueInRow[0]]?.defaultEndValue);
            return maxEndVal;
            }
        }else if(index === variationValueInRow?.length - 3) {
            //for start max val
            const startPercentage = metaDataByParamName[variationValueInRow[0]]?.startPercentage;
            if(!startPercentage){
                return metaDataByParamName[variationValueInRow[0]]?.maxStart || undefined;
            }else{
            let maxStartVal = metaDataByParamName[variationValueInRow[0]]?.defaultStartValue + ((metaDataByParamName[variationValueInRow[0]]?.startPercentage/100) * metaDataByParamName[variationValueInRow[0]]?.defaultStartValue);
            return maxStartVal;
            }
        }
    }

    useEffect(() => {

        tableData?.variationTableData?.forEach((variationItem) => {
            //based on variationItem this has to be adjusted to slice columns under one roof
            let variationItemLength = variationItem?.length;
            if (tableParameterName === "Min Spacing Rules") {
                setColSpanLength(variationItemLength - 4)
            }
            if (variationItemLength === 5 || variationItem?.includes('placer')) {
                setColSpanLength(variationItemLength - 5);
            } else
                if (variationItemLength === 6 && variationItem?.includes('placer')) {
                    setColSpanLength(variationItemLength - 4)
                }
        });
    }, [tableData, tableParameterName]);

    return (
        <BootstrapTable striped="columns" id={`table-variation-${tableParameterName}`}>
            <thead>
                {tableHeader.length > 1 && <tr>
                    <th colSpan={colSpanLength}>
                        {tableHeader.slice(0, -4).join(", ")}
                    </th>
                    <th>{tableHeader[tableHeader.length - 4]}</th>
                    <th>{tableHeader[tableHeader.length - 3]}</th>
                    <th>{tableHeader[tableHeader.length - 2]}</th>
                    <th>{tableHeader[tableHeader.length - 1]}</th>

                </tr>
                }
            </thead>
            <tbody>
                {tableData?.map((variationValueInRow, rowIndex) => {
                    //below if is executed when value is of type dropdown 
                    // Check if the array contains an object with the key "isOfDropdowntype"
                    if (variationValueInRow[1]?.isOfDropDownType) {
                        return (
                            <tr key={`key-row-variation-${rowIndex}`}>
                                {variationValueInRow?.map((item, index) => {
                                    if (index === 0) {
                                        return (
                                            <td key={`key-${index}`}>
                                                {item}   {/* Render the value directly */}
                                            </td>
                                        )
                                    }
                                    else if (index === 2 && Object.keys(item)?.includes('defaultValue')) {
                                        return (
                                            <>
                                                {/* check if item default type is boolean then handle by converting it to string so it displays on UI else we display value directly */}
                                                {typeof item?.defaultValue === "boolean" ? (item?.defaultValue === true ? <td key={`key-${index}`}>{"true"}</td> : <td key={`key-${index}`}>{"false"}</td>) :
                                                    <td key={`key-${index}`}>{item?.defaultValue}</td>
                                                }
                                            </>
                                        )
                                    }
                                    // index 3 has selected value object which is not used for showing on ui
                                    else if (index > 3) {
                                        // here will check if item type is boolean will convert to string or else will directly use item value
                                        return (
                                            <td key={`key-${index}`}>
                                                <Form.Check type="checkbox" aria-label="option 1" label={typeof item === "boolean" ? (item === true ? "true" : "false") : item} id={`checkbox-${item}`} checked={variationValueInRow?.find((item) => item?.selectedValues)?.selectedValues?.includes(item)} onChange={(e) => { handleInputChange(e.target.checked, variationValueInRow, null, item) }} />
                                            </td>
                                        )
                                    }

                                    else {
                                        return null; // Prevent rendering unnecessary items for index 0
                                    }
                                })}
                            </tr>
                        )
                    }
                    // will check if default value is there will handle display here 


                    else {
                        return (
                            <tr key={`key-row-variation-${rowIndex}`}>
                                {variationValueInRow?.map((eachItemInTable, index) => {
                                    // Check if the current item is a number
                                    if (typeof eachItemInTable === 'number') {
                                        //checking if there are some errors on current input
                                        let hasError = false;

                                        hasError = techParameterValueError?.some(
                                            (error) => variationValueInRow[0] === error?.erroredParameterName && index === error?.index
                                        );

                                        return (
                                            <td key={`key-${index}`}>
                                                {index >= variationValueInRow?.length - 3 ? (
                                                    
                                                    <div style={{ display: "flex", flexDirection: "column" }}>
                                                        
                                                        {/* variationValueInRow?.length - 1 -> step value field  , variationValueInRow?.length - 2 -> end value field ,  variationValueInRow?.length - 3 -> start value*/}
                            
                                                        <input
                                                            style={{ width: "100px", border: hasError ? "solid red" : "" }}
                                                            id={`edit-variation-${variationValueInRow[0]}${tableParameterName === 'Min Spacing Rules' ? `-${variationValueInRow[1]}` : ""}-${variationValueInRow?.length - 1 === index ? "step" : variationValueInRow?.length - 2 === index ? "end" : "start"}`} // Use a unique id for each field & in case of minspacing there are two parameters so adding it both in id for unique identification
                                                            type="number"
                                                            min={handleMinValueForInputType(index, variationValueInRow)}
                                                            max={handleMaxValueForInputType(index, variationValueInRow)}
                                                            onWheel={(e) => e.target.blur()}
                                                            onKeyDown={(e) => { 
                                                                const key = e.key;
                                                                const value = parseFloat(e.target.value);
                                                                //const minValue = handleMinValueForInputType(index, variationValueInRow);
                                                                const isStepperFloatAllowed = metaDataByParamName[variationValueInRow[0]]?.stepperFloat;

                                                                if (e.ctrlKey && (e.key === 'a'|| e.key === 'A')) {
                                                                    e.preventDefault();
                                                                    e.target.select();
                                                                }
                                                                
                                                                const allowedKeys = [ "Tab", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Delete","Backspace"];

                                                                if (allowedKeys.includes(key)) return;

                                                                // Allow numbers and dot
                                                                if (!/[0-9.-]$/.test(key)) {
                                                                    e.preventDefault();
                                                                    return;
                                                                }

                                                                if(!isStepperFloatAllowed && key === "."){
                                                                    e.preventDefault();
                                                                    return;
                                                                }

                                                                if (index === variationValueInRow?.length - 1) { // If it's the "step" field
                                                                    const inputValue = e.target.value;
                                                                    //const minStep = metaDataByParamName[variationValueInRow[0]]?.stepper || 1;
                                                                    //const isStepperFloatAllowed = metaDataByParamName[variationValueInRow[0]]?.stepperFloat;
                                                                    // Prevent standalone "0" if minStep >= 0.5
                                                                    // if (inputValue === "" && key === "0" && minStep >= 0.5) {
                                                                    //     e.preventDefault();
                                                                    //     return;
                                                                    // }
                                                                    if(!isStepperFloatAllowed && key === "."){
                                                                        e.preventDefault();
                                                                        return;
                                                                    }
                                                                    // Optional: Prevent multiple dots like "0..5"
                                                                    if (key === "." && inputValue.includes(".")) {
                                                                        e.preventDefault();
                                                                        return;
                                                                    }
                                                                }

                                                               

                                                                //if it is end field or start field adding validation for max range , 
                                                                if(index === variationValueInRow?.length -2 || index === variationValueInRow?.length - 3){  
                                                                    const maxValue = handleMaxValueForInputType(index,variationValueInRow);
                                                                    //if inserted value is greater than maxval dont allow user to insert value
                                                                    if(isNaN(value) || value > maxValue){
                                                                        e.preventDefault();
                                                                        return;
                                                                    }
                                                                }


                                                                //handleValidationOnVariationInput(e, variationValueInRow, index, metaDataByParamName[variationValueInRow[0]]?.stepper)
                                                            }}
                                                            onChange={(e) => {
                                                                const value = parseFloat(e.target.value);
                                                                let field;
                                                                const isStepperFloatAllowed = metaDataByParamName[variationValueInRow[0]]?.stepperFloat;
                                                                // Prevent setting 0 in step field
                                                                // if (index === variationValueInRow?.length - 1 && value === 0) {
                                                                //     return;
                                                                // }

                                                                //allowing user to enter floats value only when entering of float is allowed from business
                                                                if(!isStepperFloatAllowed && e.target.value.includes(".")){
                                                                    e.preventDefault();
                                                                    return;
                                                                }
                                                                
                                                                //if it is end field or start field adding validation for max range , 
                                                                if(index === variationValueInRow?.length -2 || index === variationValueInRow?.length - 3){     
                                                                    const maxValue = handleMaxValueForInputType(index,variationValueInRow);
                                                                    //if inserted value is greater than maxval dont allow user to insert value
                                                                    if(isNaN(value) || value > maxValue){
                                                                        e.preventDefault();
                                                                        return;
                                                                    }
                                                                }

                                                            
                                                                // Allow clearing the input
                                                                if (value === "") {
                                                                    handleInputChange("", variationValueInRow, field);
                                                                    return;
                                                                }

                                                                // Assign field based on the index position
                                                                if (index === variationValueInRow?.length - 1) {
                                                                    field = 'step';
                                                                    //if (value <= 0 || ) {
                                                                    if(value < metaDataByParamName[variationValueInRow[0]]?.stepper){
                                                                        //adding element to error when errored
                                                                        const alreadyErrored = techParameterValueError?.some((errorItems) => tableParameterName === errorItems?.tableParameterName && errorItems?.index === index && errorItems?.rowIndex === rowIndex);
                                                                        !alreadyErrored && setTechParameterValueError((prevItems) => [...prevItems, { rowIndex, index, erroredParameterName: variationValueInRow[0], tableParameterName, message: `Value should be greater than ${metaDataByParamName[variationValueInRow[0]]?.stepper}` },]);

                                                                    } else {
                                                                        //filtering out element from errored array to remove error if is is fixed now
                                                                        setTechParameterValueError((prev) => {
                                                                            const filteredErrors = prev.filter((err) => {
                                                                                return tableParameterName !== err.tableParameterName || err.index !== index || err.rowIndex !== rowIndex;
                                                                            });

                                                                            return filteredErrors;
                                                                        }
                                                                        );
                                                                    }
                                                                } else if (index === variationValueInRow?.length - 2) {
                                                                    field = 'end';
                                                                    const minEndValue = handleMinValueForInputType(index,variationValueInRow);
                                                                    const maxEndValue = handleMaxValueForInputType(index,variationValueInRow);
                                                                    const minStartValue = handleMinValueForInputType(index - 1, variationValueInRow);
                                                                    
                                                                    // Validate that end is greater than start
                                                                    const startValue = variationValueInRow[variationValueInRow?.length - 3];
                                                                    // adding error message if end is less than min range of end value or less than equal to start value
                            
                                                                    if(value < minEndValue || value <= startValue){
                                                                         //adding element to error when errored
                                                                         const alreadyErrored = techParameterValueError?.some((errorItems) => tableParameterName === errorItems?.tableParameterName && errorItems?.index === index && errorItems?.rowIndex === rowIndex);
                                                                         !alreadyErrored && setTechParameterValueError((prevItems) => [...prevItems, { rowIndex, index, erroredParameterName: variationValueInRow[0], tableParameterName, message: `Value should be in the valid range from ${minEndValue} to ${maxEndValue} & Greater than start value ` },]);
                                                                    }
                             
                                                                    else if (value > startValue && value >= minEndValue) {

                                                                        //will find if start has error on it for same rowindex and element parameter
                                                                        //filtering out element from errored array to remove error if is is fixed now
                                                                        let endFilteredErrors;
                                                                        setTechParameterValueError((prev) => {
                                                                            endFilteredErrors = prev.filter((err) => {
                                                                                return tableParameterName !== err.tableParameterName || err.index !== index || err.rowIndex !== rowIndex;
                                                                            });
                                                                            return endFilteredErrors;
                                                                        }
                                                                        );

                                                                        const startHasError = endFilteredErrors?.some(
                                                                            (error) => tableParameterName === error?.tableParameterName && variationValueInRow[0] === error?.erroredParameterName && error?.rowIndex === rowIndex && error?.index !== index
                                                                        )
                                                                        if (startHasError && startValue >= minStartValue) {

                                                                            //filtering out error since condition is meet 
                                                                            setTechParameterValueError((prev) => {
                                                                                const filteredErrors = prev?.filter((err) => {
                                                                                    if (tableParameterName === err?.tableParameterName) {
                                                                                        //if error is on same accordians
                                                                                        return variationValueInRow[0] !== err?.erroredParameterName && err?.rowIndex !== rowIndex 
                                                                                    } else {
                                                                                        //if error is on different accordians
                                                                                        return variationValueInRow[0] !== err?.erroredParameterName
                                                                                    }

                                                                                });

                                                                                return filteredErrors;
                                                                            })
                                                                        }
                                                                    }
                                                                } else if (index === variationValueInRow?.length - 3) {
                                                                    field = 'start';
                                                                    // Validate that end is greater than start
                                                                    let minStartValue = handleMinValueForInputType(index,variationValueInRow);
                                                                    let maxStartValue = handleMaxValueForInputType(index,variationValueInRow);
                                                                    const minEndValue = handleMinValueForInputType(index + 1, variationValueInRow);
                                                                    const endValueInHTML = variationValueInRow[variationValueInRow?.length - 2];
                                                                    if(value < minStartValue || endValueInHTML<=value){
                                                                       
                                                                         //adding element to error when errored
                                                                           //adding element to error when errored
                                                                        const alreadyErrored = techParameterValueError?.some((errorItems) => tableParameterName === errorItems?.tableParameterName && errorItems?.index === index && errorItems?.rowIndex === rowIndex);
                                                                        !alreadyErrored && setTechParameterValueError((prevItems) => [...prevItems, { rowIndex, index, erroredParameterName: variationValueInRow[0], tableParameterName, message: `Value should be in the valid range from ${minStartValue} to ${maxStartValue} & Less than end value ` },]);
                                                                    }
                                                               
                                                                    else if (value >= minStartValue) {
                                                                      
                                                                        //will find if end has error on it for same rowindex and element parameter
                                                                        //filtering out element from errored array to remove error if is is fixed now
                                                                        let startFilteredErrors;
                                                                        setTechParameterValueError((prev) => {
                                                                            startFilteredErrors = prev.filter((err) => {
                                                                                return tableParameterName !== err.tableParameterName || err.index !== index || err.rowIndex !== rowIndex;
                                                                            });
                                                                            return startFilteredErrors;
                                                                        }
                                                                        );

                                                                        //will check if end value has some error of current updation & if it matches the condition or not 

                                                                        const endHasError = startFilteredErrors?.some((error) =>
                                                                            tableParameterName === error?.tableParameterName && variationValueInRow[0] === error?.erroredParameterName && rowIndex === error?.rowIndex
                                                                        )
                                                                       
                                                                        if (endHasError && endValueInHTML >= minEndValue ) {

                                                                            //filtering out error since condition of end being larger is meet 
                                                                            setTechParameterValueError((prev) => {
                                                                                const filteredErrorVal = prev.filter((errorVal) => {
                                                                                    if (tableParameterName === errorVal?.tableParameterName) {
                                                                                        //if it is under same accordian 
                                                                                        return variationValueInRow[0] !== errorVal?.erroredParameterName && rowIndex !== errorVal?.rowIndex 
                                                                                    } else {
                                                                                        //if it is under different accordian
                                                                                        return variationValueInRow[0] !== errorVal?.erroredParameterName;
                                                                                    }
                                                                                })
                                                                                return filteredErrorVal;
                                                                            })
                                                                        }

                                                                    }

                                                                }
                                                                // Call the handler with the correct parameters
                                                                handleInputChange(Number(e.target.value), variationValueInRow, field);
                                                            }}
                                                            step={metaDataByParamName[variationValueInRow[0]]?.stepper || 1}//StepperValue
                                                            value={eachItemInTable} // Set the value of input to the current table data
                                                        />
                                                        {/* if there are error on input field displaying below it  */}

                                                        {techParameterValueError?.length > 0 &&
                                                            techParameterValueError
                                                                ?.filter(error => {
                                                                    return variationValueInRow[0] === error?.erroredParameterName && error?.index === index
                                                                })
                                                                ?.map((errorItem) => (<span style={{ color: "red" }}>{errorItem?.message}</span>))
                                                        }
                                                    </div>
                                                ) : (
                                                    // For non-editable columns, display the value as is
                                                    eachItemInTable
                                                )}
                                            </td>
                                        );
                                    }
                                    //handling display of default value
                                    else if (typeof eachItemInTable === 'object' && eachItemInTable?.defaultValue) {
                                        // Object.values(eachItemInTable)?.map((defaultVal) => {
                                        return (

                                            <td key={`key-${index}`}>{eachItemInTable?.defaultValue?.join(', ')}</td>
                                        )
                                        // })
                                    }
                                    else {

                                        // Handle non-number elements, if necessary
                                        return (
                                            <td key={`key-${index}`}>
                                                {eachItemInTable}
                                            </td>
                                        );
                                    }
                                })}
                            </tr>
                        )
                    }
                    //  })
                })}
            </tbody>
        </BootstrapTable>
    );
};

export default VariationTable;
