 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: ProjectWithStage1ResultListModalBody.js  
 * Description: This file is modal body content page to which shows project with stage 1 result 
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

import React, { useState } from "react";

export const ProjectWithStage1ResultListModalBody = ({ projectListWithStage1Result, handleStateSetForProjectSelection }) => {

    const [selectedProjectName, setSelectedProjectName] = useState("");
    //below project handles project selections row functionality
    const handleProjectRowSelection = (projectNameSelected, currentSelectedProjectId, currentSelectedNetListFileName, currentSelectedTechFileName, data) => {
        setSelectedProjectName(projectNameSelected);
        handleStateSetForProjectSelection(true, currentSelectedProjectId, projectNameSelected, currentSelectedNetListFileName, currentSelectedTechFileName, data);
    };

    // Convert UTC date to IST
    const convertToIST = (utcDateString) => {
        const date = new Date(utcDateString);
        const formatter = new Intl.DateTimeFormat('en-IN', {
            timeZone: 'Asia/Kolkata',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        return formatter.format(date);
    };

    return (
        <>
            {/* Check if projectListWithStage1Result is valid and has data */}

            {projectListWithStage1Result?.data?.length > 0 ? (
                <div className="row">
                    <ul
                        className="list-group"
                    >
                        <li
                            className="list-group-item border rounded mb-2 bg-light sticky-top me-0 pe-3"
                            style={{ zIndex: 1 }}
                            id={"header-projectwithstage1result-table"}
                        >
                            <div className="d-flex ">
                                <div className="fw-bold w-100">
                                    <label className="form-check-label ">
                                        Project Name
                                    </label>
                                </div>
                                <div className="fw-bold w-100">
                                    <label className="form-check-label ">
                                        Last Touched Time (UTC)
                                    </label>
                                </div>
                                <div className="fw-bold w-50 text-start">
                                    <label className="form-check-label">
                                        Created By
                                    </label>
                                </div>
                                <div className="fw-bold w-50 text-start">
                                    <label className="form-check-label ">
                                        Modified By
                                    </label>
                                </div>
                            </div>
                        </li>
                        {projectListWithStage1Result?.data?.map((data) => (
                            <li
                                key={data.project_name}
                                className={`list-group-item d-flex justify-content-between align-items-center py-2 border rounded mb-2 ${selectedProjectName === data.project_name
                                    ? "app-primary-button-color border-0  text-white"
                                    : "bg-light"
                                    }`}
                                onClick={() => { handleProjectRowSelection(data?.project_name, data?.id, data?.netlist_metadata?.fileName, data?.tech_metadata?.fileName, data) }}
                                style={{ cursor: "pointer" }}
                            >
                                <div className="w-75 text-start text-truncate">
                                    {data.project_name}
                                </div>
                                <div className="w-75 text-center">
                                    {/* Convert the last_touched_date to IST */}
                                    {convertToIST(data.last_touched_date)}</div>
                                <div className="w-50 text-center">{data.created_date}</div>
                                <div className="w-50 text-center">{data.modified_date}</div>
                            </li>
                        ))}
                    </ul>
                </div>
            ) : (
                <div className="row">
                    <span className="text-center align-content-center pt-5">  {projectListWithStage1Result?.message || "No projects available"}</span>
                </div>
            )
            }
        </>
    )

}