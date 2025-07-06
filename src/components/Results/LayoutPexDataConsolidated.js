
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: LayoutPexDataConsolidated.js  
 * Description: This file is responsible to show Layout Pex Consolidated Data 
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

const LayoutPexDataConsolidated = ({ gdsData = [] }) => {
    return (
        <div className="d-flex align-items-center justify-content-center">
            <div className="accordion w-100" id={`accordion-pex-data`}>
                {gdsData && gdsData?.PEX_Consolidated?.length > 0 ? (
                    gdsData?.PEX_Consolidated?.map((gds, index) => (
                        <div className="accordion-item" key={index}>
                            {/* react-tooltip to show gds image on hover */}
                            <div
                            >
                                <h2 className="accordion-header" id={`layout-pex-data-accordion-${gds?.name}`}>
                                    <button
                                        className="accordion-button collapsed"
                                        id={`layout-pex-btn-${gds?.name}`}
                                        type="button"
                                        data-bs-toggle="collapse"
                                        data-bs-target={`#gds-pex-data-body-${gds?.name}`}
                                        aria-expanded="false"
                                        aria-controls={`gds-pex-data-${index}`}
                                    >
                                        {gds?.name}
                                    </button>
                                </h2>
                            </div>
                            <Tooltip id={`tooltip-${gds?.name}`} style={{ zIndex: 9999, padding: "1px" }} />
                            <div
                                id={`gds-pex-data-body-${gds?.name}`}
                                className="accordion-collapse collapse"
                                aria-labelledby={`heading-${index}`}
                                data-bs-parent="#accordion-pex-data"
                            >
                                <div className="accordion-body">
                                    <div style={{ width: "100%" }}>
                                        {gds?.data && gds?.data?.length > 0 ? (
                                            <div>
                                                {/* Merging all records */}
                                                <DataGrid
                                                    columns={Object.keys(gds?.data[0])?.filter(key => key !== 'LayoutData')?.map((key) => {
                                                            const isNumber = typeof gds?.data[0][key] === 'number';
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
                                                    }
                                                    rows={gds?.data?.map((record, rowIndex) => {
                                                        return {
                                                            id: rowIndex + 1, // Unique ID across all dataItem
                                                            ...Object.fromEntries(
                                                                Object?.entries(record)?.map(([key, value]) => [
                                                                    key,
                                                                    value === null || value === undefined ? '-' : value,
                                                                ])
                                                            )
                                                        };
                                                    })}
                                                    initialState={{
                                                        ...gds.initialState,
                                                        pagination: { paginationModel: { pageSize: 25 } },
                                                    }}
                                                    pageSizeOptions={[25, 50, 75, 100, { value: -1, label: 'All' }]}
                                                    autoHeight
                                                />
                                            </div>
                                        ) : (
                                            <Empty description="No data available" />
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="d-flex justify-content-center align-items-center"
                        style={{ height: "50vh" }}>
                        <Empty />
                    </div>
                )}
            </div>


        </div>
    );
};

export default LayoutPexDataConsolidated;
