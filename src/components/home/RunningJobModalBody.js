
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: RunningJobModalBody.js  
 * Description: This file contains running jobs modal body contains 
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

import React, { useState } from 'react';
import Button from 'react-bootstrap/Button';
import Circuit from "../../Assets/Images/networkwired.svg";
import Diagram from "../../Assets/Images/microchip.svg";
import moment from 'moment';
import { useRunProjectContext } from '../providers/RunProjectProvider/RunProjectContext';
import { getListOfRunningJob } from '../../server/server';

const RunningJobListModal = ({ listOfRunningJobsData, handleRunningJobViewButton }) => {

  const [isShowAllChecked, setIsShowAllChecked] = useState(false); // maintains the checked state for show all jobs checked
  const { setListOfRunningJobsData } = useRunProjectContext();
  // Function to get relative time
  const getUpdatedTime = (time) => {
    return moment(time).fromNow();
  };

  // function to handle state change of checked radio button
  const handleShowAllJobsCheckboxChange = async (checkedVal) => {
    setIsShowAllChecked(checkedVal);
    if (checkedVal === true) {
      const listOfRunningJobsUpdated = await getListOfRunningJob(true);
      setListOfRunningJobsData(listOfRunningJobsUpdated)
    } else {
      const listOfRunningJobsUpdated = await getListOfRunningJob(false);
      setListOfRunningJobsData(listOfRunningJobsUpdated)
    }

  };



  return (
    <div>
      <input
        className="form-check-input position-absolute"
        type="checkbox"
        id="showAllJobsCheckbox"
        name="Show All Jobs"
        checked={isShowAllChecked}
        onChange={(e) => { handleShowAllJobsCheckboxChange(e.target.checked) }}
        style={{ top: '4px', left: '25px', bottom: "4px", zIndex: 1 }}
      />
      <label htmlFor='showAllJobsCheckbox' style={{ cursor: 'pointer', paddingTop: "3.5px", paddingLeft: "30px", paddingBottom: "8px" }}>Show All Jobs</label>
      {listOfRunningJobsData?.status && listOfRunningJobsData?.data !== null ? (
        <div className="row">
          <ul className="list-group">
            <li
              className="list-group-item border rounded mb-2 bg-light sticky-top me-0 pe-3"
              style={{ zIndex: 1 }}
              id="header-running-jobs-table"
            >
              <div className="d-flex">
                <div className="fw-bold w-50 text-start">
                  <label className="form-check-label">Project Name</label>
                </div>
                <div className="fw-bold w-25 text-center" >
                  <label className="form-check-label">Status</label>
                </div>
                <div className="fw-bold w-50 text-center">
                  <label className="form-check-label">Last Updated</label>
                </div>
                <div className="fw-bold w-25 text-center">
                  <label className="form-check-label">Feature</label>
                </div>
                {listOfRunningJobsData?.data?.some((jobsItem) => jobsItem?.status === 'RUNNING') && <div className="fw-bold w-50 text-start">
                  <label className="form-check-label"></label>
                </div>
                }
              </div>
            </li>
            {listOfRunningJobsData?.data?.length > 0 &&
              listOfRunningJobsData?.data?.map((job) => (
                <li
                  key={job?.id}
                  className="list-group-item d-flex justify-content-between align-items-center py-2 border rounded mb-2"
                  id={`running-job-list-item-${job?.project?.project_name}`}
                >
                  <div
                    className="w-50 text-truncate"
                    style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                  >
                    {job?.project?.project_name}
                  </div>
                  <div className="w-25 text-center" id={`running-job-status-${job?.project?.project_name}`}>{job?.status}</div>
                  <div className="w-50 text-center">{getUpdatedTime(job?.created_date)}</div>
                  <div className="w-25 text-center">
                    {job?.action === 1 && <img src={Circuit} alt="Circuit" width={30} height={30} />}
                    {job?.action === 2 && <img src={Diagram} alt="Diagram" width={30} height={30} />}
                    {job?.action === 3 && (
                      <div>
                        <img src={Circuit} alt="Circuit" width={30} height={30} style={{ marginRight: "10px" }} />
                        <img src={Diagram} alt="Diagram" width={30} height={30} />
                      </div>
                    )}
                  </div>
                  {(job?.status === 'RUNNING' ) &&( <div className="w-50 text-end">
                    <Button onClick={() => handleRunningJobViewButton(job?.id)} id="running-project-cancel-btn" className='app-primary-button-color border-0'>
                      View
                    </Button>
                  </div>) 
                  }
                  {/* below handles button space for non runnning jobs with atleast one running job */}
                  {(isShowAllChecked && job?.status !== 'RUNNING'&& listOfRunningJobsData?.data?.some((jobsItem) => jobsItem?.status === 'RUNNING')) && <div className="w-50 text-end"></div>}
                </li>
              ))}
          </ul>
        </div>
      ) : (
        <div className="row">
          {/*to do: commenting the below message, require backend change*/}
          {/* {listOfRunningJobsData?.response?.data?.message} */}
          <span className='text-center align-content-center pt-5'>
            No Running Jobs Found.
          </span>
        </div>
      )}
    </div>
  );
};

export default RunningJobListModal;
