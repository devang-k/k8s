import React from "react";
import "primereact/resources/themes/lara-light-blue/theme.css";
import { Table as BootstrapTable } from 'react-bootstrap';
import { useStage2ResultContext } from "../providers/Stage2ResultProvider/Stage2ResultContext";
import { Empty } from "antd";
import Table from "../../components/utils/Table/Table"

const RunResultSummary = ({ stage1RunResultSummaryData, stage2RunResultSummaryData }) => {
  const { isUserOnStage2Page } = useStage2ResultContext();

  // Decide which data to use based on the current page
  const summaryData = isUserOnStage2Page
    ? stage2RunResultSummaryData?.data
    : stage1RunResultSummaryData?.data;


  return (
    <div className="pt-3 p-0 w-100 h-100 overflow-auto">
      {summaryData  ? (
        Object?.keys(summaryData )?.length > 0 ? (
        Object?.entries(summaryData)?.map(([key, value], index) => {
          // Check if displayType is 1
          if (value.displayType === 1) {
            return (
              <div key={index}>
                {value.displayHeaderName && <h5>{value.displayHeaderName}</h5>}
                <BootstrapTable striped bordered size="sm" style={{fontSize:"15px"}}>
                  <tbody>
                    <tr>
                      <td className="w-50" >{value.displayHeaderName}</td>
                      <td className="w-50"  >
                        {Array.isArray(value.value) ? value.value.join(", ") : value.value}
                      </td>
                    </tr>
                  </tbody>
                </BootstrapTable>
              </div>
            );
          } else if (value?.displayType === 2) {
            // Handling displayType 2 data 

            if (value?.value?.length === 0) {
              return null; 
            }
            
            const rowData = value?.value?.map(item => {
              let rowItem = {};
            
              // Loop through each key in the item dynamically
              Object.keys(item).forEach(key => {
                let fieldValue = item[key];
            
                // If the value is an array, join the elements with commas
                if (Array.isArray(fieldValue)) {
                  rowItem[key] = fieldValue?.length > 1 ? fieldValue?.join(", ") : fieldValue[0];
                } else if (fieldValue === false || fieldValue === 0) {
                  rowItem[key] = fieldValue; // If the value is false or 0, pass it as it is
                } else if (typeof fieldValue === "number" && item.unit !== null && item.unit !== undefined) {
                  // If it's a number and the unit is not null or undefined, concatenate the value and the unit
                  rowItem[key] = `${fieldValue} ${item.unit}`;
                } else if (fieldValue === null || fieldValue === undefined) {
                  // If the value is null or undefined, replace it with "-"
                  rowItem[key] = "-";
                } else {
                  // For other cases, just return the value
                  rowItem[key] = fieldValue || "-";
                }
              });
            
              return rowItem;
            });
            return (
              <div className="mb-3" key={index}>
                {value?.displayHeaderName && <h5>{value?.displayHeaderName}</h5>}
                <Table data={rowData} columns={value?.parameterTableHeader} rowsPerPage={20}  />
              </div>
            );
          }
          
          return null;
        })) : (
          (
            <div className="spinner-border d-flex justify-content-center" role="status">
              <span className="sr-only">Loading...</span>
            </div>
          )
        )
      ) : (
        <div className="d-flex justify-content-center align-items-center" style={{ height: "50vh" }}>
          <Empty />
        </div>
      )}
    </div>
  );
};

export default RunResultSummary;