 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: LayoutPexData.js  
 * Description: This file is responsible to show Layout Pex Data 
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

import React from "react";
import { DataGrid } from "@mui/x-data-grid";
import { Tooltip } from "react-tooltip";
import { Empty } from "antd";
import { useStage1ResultContext } from "../providers/Stage1ResultProvider/Stage1ResultContext.js";
import { useStage2ResultContext } from "../providers/Stage2ResultProvider/Stage2ResultContext.js";

const LayoutPexData = ({ gdsData = [], actionSelected, loadingRef, loadingMore }) => {
  const { selectedGdsItems, setSelectedGdsItems } = useStage1ResultContext();
  const { isUserOnStage2Page } = useStage2ResultContext();
  // Function to handle checkbox change
  const handleCheckboxChange = (itemName) => {
    if (selectedGdsItems?.includes(itemName)) {
      // Remove item from selected items
      setSelectedGdsItems(
        selectedGdsItems?.filter((item) => item !== itemName)
      );
    } else {
      // Add item to selected items
      setSelectedGdsItems([...selectedGdsItems, itemName]);
    }
  };
  return (
    <div>
    {loadingRef?.current && !loadingMore && (
      <div className="d-flex justify-content-center align-items-center" style={{ height: "100%" }}>
        <div className="spinner-border" role="status">
          <span className="sr-only">Loading...</span>
        </div>
      </div>
    )}
    <div className="d-flex align-items-center justify-content-center">
      <div className="accordion w-100" id={`accordion-pex-data`}>
        {gdsData?.items?.map((gds, index) => (
          <div className="accordion-item" key={index}>
            {/* react-tooltip  to show gds image on hover*/}
            <div
              data-tooltip-id={`tooltip-${gds?.name}`}
              data-tooltip-html={`<img src="${gds?.src}" style="width: 200px;" /></div>`}
              data-tooltip-place="bottom"
            >
              <h2
                className="accordion-header"
                id={`layout-pex-data-accordion-${gds?.name}`}
              >
                <button
                  className="accordion-button collapsed"
                  id={`layout-pex-btn-${gds?.name}`}
                  type="button"
                  data-bs-toggle="collapse"
                  data-bs-target={`#gds-pex-data-body-${gds?.name}`}
                  aria-expanded="false"
                  aria-controls={`gds-pex-data-${index}`}
                >
                  {(actionSelected === 2 || actionSelected === 3) && (
                    <>
                      {!isUserOnStage2Page && (
                        <div className="form-check">
                          <input
                            className="form-check-input border-2 cursor_pointer"
                            type="checkbox"
                            value={gds.name}
                            id={`gds-pex-data-checkbox-${gds?.name}`}
                            checked={selectedGdsItems?.includes(gds?.name)}
                            onChange={() => handleCheckboxChange(gds?.name)}
                          />
                        </div>
                      )}
                    </>
                  )}
                  {gds?.name}
                </button>
              </h2>
            </div>
            <Tooltip
              id={`tooltip-${gds?.name}`}
              style={{ zIndex: 9999, padding: "1px" }}
            />
            <div
              id={`gds-pex-data-body-${gds?.name}`}
              className="accordion-collapse collapse"
              aria-labelledby={`heading-${index}`}
              data-bs-parent="#accordion-pex-data"
            >
              <div className="accordion-body">
                <div style={{ width: "100%" }}>
                  {gds?.pexData && gds?.pexData?.length > 0 && (
                    <DataGrid
                      columns={[
                        ...Object.keys(gds?.pexData[0])?.map((key) => {
                          const isNumber = typeof gds?.pexData[0][key] === 'number';
                          return {
                            field: key,
                            headerName: key,
                            width: 150,
                            type: isNumber ? 'number' : 'string',
                            valueFormatter: (params) => {
                              return params?.value;
                            },
                          };
                        })
                      ]}
                      rows={gds?.pexData?.map((data, rowIndex) => ({
                        id: rowIndex + 1, // Auto-incrementing ID
                        ...Object.fromEntries(
                          Object?.entries(data)?.map(([key, value]) => [
                            key,
                            value === null ? "-" : value,
                          ])
                        ),
                      }))}
                      // pagination
                      pageSizeOptions={[5, 10, 25]}
                      pageSize={5}
                      rowsPerPageOptions={[5, 10, 25]}
                      autoHeight
                    />
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
    {loadingMore && (
        <div className="d-flex justify-content-center align-items-center">
          <div className="spinner-border" role="status">
            <span className="sr-only">Loading more...</span>
          </div>
        </div>
      )}
      {!loadingRef?.current && gdsData?.length === 0 && (
        <div
          className="d-flex justify-content-center align-items-center"
          style={{ height: "50vh" }}
        >
          <Empty />
        </div>
      )}
    </div>
  );
};

export default LayoutPexData;
