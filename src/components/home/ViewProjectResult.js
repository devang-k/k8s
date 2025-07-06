
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: ViewProjectResult.js  
 * Description: This file is responsible to show view project result. 
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

import React, { useState } from 'react'
import Circuit from "../../Assets/Images/networkwired.svg";
import Diagram from "../../Assets/Images/microchip.svg";
import { projectTypeLookup } from '../../constant';

const ViewProjectResult = ({ viewProjectResultList, handleViewProjectModalSelectedInModal, setSelectedFileNameFromListOfSavedProject }) => {
  const [selectedViewProjectName, setSelectedViewProjectName] = useState("")

  const handleViewProjectFileName = (fileSelected, version) => {
    setSelectedFileNameFromListOfSavedProject(fileSelected)
    setSelectedViewProjectName(fileSelected)
    handleViewProjectModalSelectedInModal(true, version);
  }
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
    <div>
      <div className="row">
        <ul className="list-group">
          <li
            className="list-group-item border rounded mb-2 bg-light sticky-top me-0 pe-3"
            style={{ zIndex: 1 }}
          >
            <div className="d-flex justify-content-between " >
              <label className="form-check-label fw-bold">Project Name</label>
              <label className="form-check-label fw-bold">Last Touched Time (UTC)</label>
              <label className="form-check-label fw-bold">Project Type</label>
              <label className="form-check-label fw-bold">Feature</label>
            </div>
          </li>
          {viewProjectResultList && viewProjectResultList?.length > 0 ? (
            viewProjectResultList?.map((data) => (
              <li
                key={data.project_name}
                className={`list-group-item d-flex justify-content-between align-items-center py-2 border rounded mb-2 text-truncate ${selectedViewProjectName === data?.project_name
                  ? "app-primary-button-color border-0 text-white"
                  : "bg-light"
                  }`}
                style={{ cursor: "pointer" }}
                onClick={() => { handleViewProjectFileName(data?.project_name, data?.version) }}
              >
                <div className="w-75 text-start text-truncate">
                  {data?.project_name}
                </div>
                <div className="w-75 text-start text-truncate">
                  {/* Convert the last_touched_date to IST */}
                  {convertToIST(data?.last_touched_date)}
                </div>
                <div className="w-50 text-start text-truncate">
                  {projectTypeLookup[data?.project_type]}
                </div>
                <div className='w-25 text-end'>
                  {data.action === 1 && <img src={Circuit} alt="Circuit" width={30} height={30} />}
                  {data.action === 2 && <img src={Diagram} alt="Diagram" width={30} height={30} />}
                  {data.action === 3 && (
                    <div>
                      <img src={Circuit} alt="Circuit" width={30} height={30} style={{ marginRight: "10px" }} />
                      <img src={Diagram} alt="Diagram" width={30} height={30} />
                    </div>
                  )}
                </div>
              </li>
            ))
          ) : (
            <div className="row">
              <span className="text-center align-content-center pt-5">  {viewProjectResultList?.message || "No Projects to display, create at least one project using the create project option to view/edit project."}</span>
            </div>
          )}
        </ul>
      </div>
    </div>
  )
}

export default ViewProjectResult
