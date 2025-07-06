
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: ParameterTableComponent.js  
 * Description: This file is parameter table component to show tech data. 
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

import React, { useCallback } from "react";
import BootstrapTable from "react-bootstrap/Table";
import { useTechFileContext } from "../../../providers/TechFileProvider/TechFileContext";
import Dropdown from 'react-bootstrap/Dropdown';
import DropdownButton from 'react-bootstrap/DropdownButton';
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faInfoCircle } from "@fortawesome/free-solid-svg-icons";
import useTechFileParameterHidingRuleHook from ".././../../../Hooks/techFileParameterHidingRuleHook/techFileParameterHidingRuleHook";

const TableComponent = ({ tableContent }) => {

  const { tableHeader, tableData, tableParameterName, tableEditable, tableSupportsVariation, tableParameterDisplayName } = tableContent;
  const { techFileData, setTechFileData, setIsTechDataChanged,techParameterValueError,setTechParameterValueError } = useTechFileContext();

  const {shouldParameterBeHidden} = useTechFileParameterHidingRuleHook();

  const handleInputChange = useCallback((value, indexOfUpdatedData) => {
    let updatedValue;
    //handling conversion of string to boolean for type 5
    if (value === 'True' || value === 'False') {
      // coverting string to boolean
      if (value === 'True') {
        updatedValue = true;
      } else if (value === 'False') {
        updatedValue = false;
      }
    } else {
      updatedValue = value;
    }

    //finding object in techfile
    const updatedTechFileData = techFileData?.data?.FileContent?.map((item,updatedIndex) => {
      if (item.name === tableParameterName) {
        //if value matches updating item in techfiledata context value
        const updatedItem = item?.data?.map((itemData, index) => {
          if (indexOfUpdatedData === index) {
            return {
              key: index,
              ...itemData,
              val: updatedValue

            }
          }
          return itemData;
        })
        return {
          key:updatedIndex,
          ...item,
          data: updatedItem
        }

      }
      return item;
    });

    setIsTechDataChanged(true);
    setTechFileData((prevState) => { return ({ ...prevState, data: { FileContent: updatedTechFileData } }) });

  }, [techFileData, setTechFileData, tableParameterName, setIsTechDataChanged]);


  //below function for handling checkbox(parameter) select unselect  
  const handleCheckBox = (checkedDataValue, isDataChecked) => {
    const updatedTechData = { ...techFileData }; // Copying the current techData from context
    let userCheckedBoxKey = Object.values(checkedDataValue?.keyDisplayName);//userchecked box key value
    // Iterating through the file content to find the parameter that matches `tableParameterName`
    updatedTechData?.data?.FileContent?.forEach((parameter) => {

      //updating value in permutation object
      if (parameter?.name === 'permutation') {
        if (!isDataChecked) {
          let selectedParameterItemToBeAddedInPermutation;
          //add to permutation object user selected parameter
          if (tableParameterName === 'other') {
            //if parameter selected is of type other
            if (checkedDataValue?.options !== null) {
              //handling data for user selected value in other is of type where there are multiple options
              selectedParameterItemToBeAddedInPermutation = {
                name: checkedDataValue?.key?.key1,
                displayName: checkedDataValue?.keyDisplayName?.displayNameKey1,
                attribute: checkedDataValue?.key?.hasOwnProperty('key2') ? [checkedDataValue?.key?.key1 ,checkedDataValue?.key?.key2]: checkedDataValue?.key?.key1 ,// will,
                parameterName: tableParameterName,
                value: checkedDataValue?.options,
                defaultValue: [checkedDataValue?.val],
                options: checkedDataValue?.options || null,
                parameterDisplayName: tableParameterDisplayName,
                negativeEndAllowed:checkedDataValue?.negativeEndAllowed,
                negativeStartAllowed:checkedDataValue?.negativeStartAllowed,
                stepper:checkedDataValue?.stepper,
                stepperFloat:checkedDataValue?.stepperFloat,
                defaultStartValue:checkedDataValue?.defaultStartValue,
                defaultEndValue:checkedDataValue?.defaultEndValue,
                minStart: checkedDataValue?.minStart,
                maxStart: checkedDataValue?.maxStart,
                minEnd: checkedDataValue?.minEnd,
                maxEnd: checkedDataValue?.maxEnd,
                startPercentage: checkedDataValue?.startPercentage,
                endPercentage: checkedDataValue?.endPercentage
              }
            } else {
              //handling addition in permutation for other parameter whose key is not 1
              selectedParameterItemToBeAddedInPermutation = {
                name: checkedDataValue?.key?.key1,
                displayName: checkedDataValue?.keyDisplayName?.displayNameKey1,
                attribute: checkedDataValue?.key?.hasOwnProperty('key2') ? [checkedDataValue?.key?.key1 ,checkedDataValue?.key?.key2]: checkedDataValue?.key?.key1 ,// will,
                parameterName: tableParameterName,
                value: {
                  start: checkedDataValue?.defaultStartValue || 1,
                  end: checkedDataValue?.defaultEndValue ||  2,// end value is always greater than start
                  step: checkedDataValue?.stepper
                },
                defaultValue: [checkedDataValue?.val],
                options: checkedDataValue?.options || null,
                parameterDisplayName: tableParameterDisplayName,
                negativeEndAllowed:checkedDataValue?.negativeEndAllowed,
                negativeStartAllowed:checkedDataValue?.negativeStartAllowed,
                stepper:checkedDataValue?.stepper,
                stepperFloat:checkedDataValue?.stepperFloat,
                defaultStartValue:checkedDataValue?.defaultStartValue,
                defaultEndValue:checkedDataValue?.defaultEndValue,
                minStart: checkedDataValue?.minStart,
                maxStart: checkedDataValue?.maxStart,
                minEnd: checkedDataValue?.minEnd,
                maxEnd: checkedDataValue?.maxEnd,
                startPercentage: checkedDataValue?.startPercentage,
                endPercentage: checkedDataValue?.endPercentage
              }
            }
          } else {
            //if parameter selected is of type other than other
            selectedParameterItemToBeAddedInPermutation = {
              name: tableParameterName,
              attribute: checkedDataValue?.key?.hasOwnProperty('key2') ? [checkedDataValue?.key?.key1 ,checkedDataValue?.key?.key2]: checkedDataValue?.key?.key1 ,// will, // keeping attribute name same as key instead of displayName
              displayName: userCheckedBoxKey.length > 1 ? userCheckedBoxKey : userCheckedBoxKey[0],
              parameterName: tableParameterName,
              value: {
                start: checkedDataValue?.defaultStartValue,
                end: checkedDataValue?.defaultEndValue || 2,// end value is always greater than start
                step: checkedDataValue?.stepper
              },
              defaultValue: [checkedDataValue?.val],
              options: checkedDataValue?.options || null,
              parameterDisplayName: tableParameterDisplayName,
              negativeEndAllowed:checkedDataValue?.negativeEndAllowed,
              negativeStartAllowed:checkedDataValue?.negativeStartAllowed,
              stepper:checkedDataValue?.stepper,
              stepperFloat:checkedDataValue?.stepperFloat,
              defaultStartValue:checkedDataValue?.defaultStartValue,
              defaultEndValue:checkedDataValue?.defaultEndValue,
              minStart: checkedDataValue?.minStart,
              maxStart: checkedDataValue?.maxStart,
              minEnd: checkedDataValue?.minEnd,
              maxEnd: checkedDataValue?.maxEnd,
              startPercentage: checkedDataValue?.startPercentage,
              endPercentage: checkedDataValue?.endPercentage
            }
          }
          parameter?.data?.push(selectedParameterItemToBeAddedInPermutation)
        } else {
          if (tableParameterName === 'other') {
            //removing parameter from permutation if it is of type other
            parameter.data = parameter?.data?.filter((data) => {
              // Filter out the matching parameter based on `name` and `attribute`
              return !(data?.parameterName === tableParameterName && data?.displayName?.toString() === userCheckedBoxKey.toString());
            });
          } else {
            //removing parameter from pemrutation if it is not of type other
            //remove from permutation object user selected parameter

            parameter.data = parameter?.data?.filter((data) => {
              // Filter out the matching parameter based on `name` and `attribute`
              return !(data?.name === tableParameterName && data?.displayName?.toString() === userCheckedBoxKey.toString());
            });
          }
        }
      }

      //updating checkbox value
      if (parameter?.name === tableParameterName) {
     
        // If we find the matching parameter, iterate over its data to find the matching row
        parameter.data = parameter?.data?.map((row,paramererIndex) => {
          let keyInTechDataJSON = Object.values(row?.keyDisplayName).toString();
          //removing checkbox based on user selection
          if (keyInTechDataJSON === userCheckedBoxKey?.toString()) {
            // Toggling the isSelected value based on the checkbox
            return {...row, isSelected: !isDataChecked };
          }
          return row; // Returning the row unchanged if it doesn't match
        });
      }
    });
    // Updating the techFileData context with the modified data
    setIsTechDataChanged(true);
    setTechFileData(updatedTechData);
    /*handling sceanrio where incase error is there on parameter intially selected for variations 
          & user removes it to be selected from variations then removing that parameter from errored json 
          as well to maintain fresh flow of parameter selection & cleanup previous configs on parameter **/
          if(userCheckedBoxKey.length >0 ){
          const newErroredTechParamValues = techParameterValueError?.filter((erroredParam)=>{
         
           return erroredParam?.erroredParameterName !== userCheckedBoxKey?.[0]
          });
          setTechParameterValueError(newErroredTechParamValues);
       }
  };


  const renderCellContent = (rowElementValue, rowIndex, colIndex) => {
    return (

      <input
        id="edit-parameter"
        type="number"
        onChange={(e) => handleInputChange(Number(e.target.value), rowIndex, colIndex)}
        onKeyDown={(e) =>  {
          if (e.ctrlKey && (e.key === 'a'|| e.key === 'A')) {
          e.preventDefault();
          e.target.select();
        }
      }}
        value={rowElementValue?.val}
        min={0}
      />
    )
  };

  return (
    <BootstrapTable striped="columns" id={`table-parameter-${tableParameterName}`}>
      <thead>
        {/* uncomment below code once we work on selectAll button for tables page */}
        {/* {tableEditable && (

          <th>
            {/* handling selectall field for parameter 
              <input
                    id="checkbox-parameter-selection"
                    type="checkbox"
                    checked={false}
                    onChange={(e) => {}}
              />
              <label>
                SelectAll
              </label>
          </th>
        )} **/}
        {tableHeader?.length > 1 && <tr>
          {tableHeader?.map((header, index) => (
            <th key={index}>{header}</th>
          ))}
        </tr>}
      </thead>
      <tbody>
        {tableData?.map((parameterValueInRow, rowIndex) => (
          <>
          
          {/* below parameter is displayed in UI only if it is uivisible and parameterhidingrule is null or parameterhiding rule does not math */}
            {((parameterValueInRow?.uiVisible && parameterValueInRow?.parameterHidingRule === null) || (parameterValueInRow?.uiVisible && !shouldParameterBeHidden(parameterValueInRow)) ) && (
              <tr key={rowIndex}>
                {tableEditable ? (
                  <>
                    {(tableSupportsVariation && parameterValueInRow?.supportsVariations) ? (
                      <td >
                        <input
                          id={parameterValueInRow?.keyDisplayName?.displayNameKey2 ? `checkbox-parameter-selection-${parameterValueInRow?.keyDisplayName?.displayNameKey1}-${parameterValueInRow?.keyDisplayName?.displayNameKey2}` : `checkbox-parameter-selection-${parameterValueInRow?.keyDisplayName?.displayNameKey1}`}
                          type="checkbox"
                          checked={parameterValueInRow?.isSelected}
                          onChange={(e) => handleCheckBox(parameterValueInRow, parameterValueInRow?.isSelected)}
                        />
                      </td>
                    ) : (<td></td>)}
                    {Object.values(parameterValueInRow?.keyDisplayName || {})?.map((value, index, array) => (
                      <td key={`key-${index}`}>{value}
                        {/* below td displys info icon on hover of which shows information realted to tech parameter */}
                        {parameterValueInRow?.description !== null && (index === array.length - 1 && ( // Check if it's the last element
                          <span style={{ cursor: 'pointer', marginLeft: '12px' }} title={parameterValueInRow?.description}>
                            <FontAwesomeIcon icon={faInfoCircle} style={{ size: 'xs', cursor: "pointer", color: "#bbbcbe" }} />
                          </span>
                        ))}
                      </td>
                    ))}


                    {/* Editable inputs based on the type of parameter */}
                    {!parameterValueInRow?.isSelected ? (
                      <>
                        {/* type 1 is value is of integer , float, exponential */}
                        {parameterValueInRow?.type === 1 && (
                          <td>
                            <div style={{ display: 'flex', alignItems: 'center' }}>
                              <input
                                id={parameterValueInRow?.keyDisplayName?.displayNameKey2 ? `edit-parameter-${parameterValueInRow?.keyDisplayName?.displayNameKey1}-${parameterValueInRow?.keyDisplayName?.displayNameKey2}` : `edit-parameter-${parameterValueInRow?.keyDisplayName?.displayNameKey1}`}
                                type="number"
                                onChange={(e) => handleInputChange(Number(e.target.value), rowIndex)}
                                onKeyDown={(e) =>  {
                                  if (e.ctrlKey && (e.key === 'a'|| e.key === 'A')) {
                                  e.preventDefault();
                                  e.target.select();
                                }
                              }}
                                value={parameterValueInRow?.val}
                                min={0}
                              />
                              {/* displaying unit of value */}
                              {parameterValueInRow?.unit !== null && <span id="unit-of-parameter" style={{ marginLeft: "8px" }}>{parameterValueInRow?.unit}</span>}
                            </div>
                          </td>
                        )}
                        {/* type 2 is value is of type array */}
                        {parameterValueInRow?.type === 2 &&
                          parameterValueInRow?.val?.map((cellDataValue, colIndex) => (
                            <td key={`key-value-${colIndex}`} >
                              <div style={{ display: 'flex', alignItems: 'center' }}>
                                {renderCellContent(cellDataValue, rowIndex, colIndex)}
                                {/* displaying unit of value */}
                                {parameterValueInRow?.unit !== null && <span id="unit-of-parameter" style={{ marginLeft: "8px" }}>{parameterValueInRow?.unit}</span>}
                              </div>
                            </td>
                          ))}
                        {/* if options is null then just string is displayed */}
                        {(parameterValueInRow?.type === 3 && parameterValueInRow?.options === null) && (
                          <td>
                            <div style={{ display: 'flex', alignItems: 'center' }}>
                              <input
                                id={parameterValueInRow?.keyDisplayName?.displayNameKey2 ? `edit-parameter-${parameterValueInRow?.keyDisplayName?.displayNameKey1}-${parameterValueInRow?.keyDisplayName?.displayNameKey2}` : `edit-parameter-${parameterValueInRow?.keyDisplayName?.displayNameKey1}`}
                                type="text"
                                onChange={(e) => handleInputChange(e.target.value, rowIndex)}
                                value={parameterValueInRow?.val}
                              />
                              {/* displaying unit of value */}
                              {parameterValueInRow?.unit !== null && <span id="unit-of-parameter" style={{ marginLeft: "8px" }}>{parameterValueInRow?.unit}</span>}
                            </div>
                          </td>
                        )}
                        {/* if option is not null then dropdown option is given to user */}
                        {(parameterValueInRow?.type === 3 && parameterValueInRow?.options !== null) && (
                          <td id={parameterValueInRow?.keyDisplayName?.displayNameKey2 ? `dropdown-button-type3-${parameterValueInRow?.keyDisplayName?.displayNameKey1}-${parameterValueInRow?.keyDisplayName?.displayNameKey2}` : `dropdown-button-type3-${parameterValueInRow?.keyDisplayName?.displayNameKey1}`}>
                            <div style={{ display: 'flex', alignItems: 'center' }}>
                              <DropdownButton
                                id={`dropdown-button-drop-type3`}
                                variant="secondary"
                                title={parameterValueInRow?.val}
                                size="sm"
                                onSelect={(eventKey) => handleInputChange(eventKey, rowIndex)}
                              >
                                {parameterValueInRow?.displayNameOptions?.map((displayName, index) => (
                                  <Dropdown.Item
                                    eventKey={parameterValueInRow?.options?.[index]}
                                    key={`dropdown-type3-${displayName}`}
                                    id={`dropdown-item-type3-${displayName}`}
                                  >
                                    {displayName}
                                  </Dropdown.Item>
                                ))}
                              </DropdownButton>
                              {/* <DropdownButton
                          id={`dropdown-button-drop-type3`}
                          variant="secondary"
                          title={parameterValueInRow?.val}
                          size="sm"
                          onSelect={(eventKey) => handleInputChange(eventKey, rowIndex)}
                        >
                          {parameterValueInRow?.displayNameOptions?.map((optionItem) => (
                            <Dropdown.Item eventKey={optionItem} key={`dropdown-${optionItem}`} id={`dropdown-item-type3-${optionItem}`}>{optionItem}</Dropdown.Item>
                          ))}
                        </DropdownButton> */}
                              {/* displaying unit of value */}
                              {parameterValueInRow?.unit !== null && <span id="unit-of-parameter" style={{ marginLeft: "8px" }}>{parameterValueInRow?.unit}</span>}
                            </div>
                          </td>
                        )}
                        {/* value is of type 5 i.e boolean & it has option to select */}
                        {(parameterValueInRow?.type === 5 && parameterValueInRow?.options !== null) && (
                          <td id={parameterValueInRow?.keyDisplayName?.displayNameKey2 ? `dropdown-button-type5-${parameterValueInRow?.keyDisplayName?.displayNameKey1}-${parameterValueInRow?.keyDisplayName?.displayNameKey2}` : `dropdown-button-type5-${parameterValueInRow?.keyDisplayName?.displayNameKey1}`}>
                            <div style={{ display: 'flex', alignItems: 'center' }}>
                              <DropdownButton
                                id={`dropdown-button-drop-type5`}
                                variant="secondary"
                                title={parameterValueInRow?.val.toString()}
                                size="sm"
                                onSelect={(eventKey) => handleInputChange(eventKey, rowIndex)}
                              >
                                {parameterValueInRow?.displayNameOptions?.map((optionItem) => (
                                  <Dropdown.Item eventKey={optionItem} key={`dropdown-type5-${optionItem}`} id={`dropdown-item-type5-${optionItem}`}>{optionItem.toString()}</Dropdown.Item>
                                ))}
                              </DropdownButton>
                              {/* displaying unit of value */}
                              {parameterValueInRow?.unit !== null && <span id="unit-of-parameter" style={{ marginLeft: "8px" }}>{parameterValueInRow?.unit}</span>}
                            </div>
                          </td>
                        )}
                      </>
                    ) : (
                      <>
                        {/*handling display of just data when user wants this field to be editable from variations , i.e user selects checbox and field becomes uneditable */}
                        {parameterValueInRow?.type === 5 ? ((parameterValueInRow?.val === true) ? <td>{'true'}</td> : <td>{'false'}</td>) : (<td>{parameterValueInRow?.val}
                          {/* displaying unit of value */}
                          {parameterValueInRow?.unit !== null && <span id="unit-of-parameter" style={{ marginLeft: "8px" }}>{parameterValueInRow?.unit}</span>}
                        </td>)}

                      </>
                    )}
                  </>
                ) : (
                  <>
                    {/* Non-editable mode */}
                    {/* Display the `key` and `val` properties if they exist */}

                    {Object.values(parameterValueInRow?.keyDisplayName || {})?.map((value, index, array) => (
                      <td key={`key-${index}`}>{value}
                        {/* below td displys info icon on hover of which shows information realted to tech parameter */}
                        {parameterValueInRow?.description !== null && (index === array.length - 1 && ( // Check if it's the last element
                          <span style={{ cursor: 'pointer', marginLeft: '12px' }} title={parameterValueInRow?.description}>
                            <FontAwesomeIcon icon={faInfoCircle} style={{ size: 'xs', cursor: "pointer", color: "#bbbcbe" }} />
                          </span>
                        ))}
                      </td>
                    ))}

                    {Array.isArray(parameterValueInRow?.val) ? parameterValueInRow?.val?.map((value, colIndex) => (
                      <td key={`val-${colIndex}`}>{value}
                        <div style={{ display: 'flex', alignItems: 'center' }}>
                          {/* displaying unit of value */}
                          {parameterValueInRow?.unit !== null && <span id="unit-of-parameter" style={{ marginLeft: "8px" }}>{parameterValueInRow?.unit}</span>}
                        </div>
                      </td>
                    )) :
                      <td>{parameterValueInRow?.val}
                        <div style={{ display: 'flex', alignItems: 'center' }}>
                          {/* displaying unit of value */}
                          {parameterValueInRow?.unit !== null && <span id="unit-of-parameter" style={{ marginLeft: "8px" }}>{parameterValueInRow?.unit}</span>}
                        </div>
                      </td>}

                  </>
                )}
              </tr>
            )}
          </>
        ))}
      </tbody>
    </BootstrapTable>
  );
};

export default TableComponent;
