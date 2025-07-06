 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: CreateProjectTypeSelectionModalBody.js  
 * Description: This file is responsible to show and handle create project type modal content 
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

import React,{useState} from 'react'
import { RLBasedPOCProject, TwoHunderedPlusTransistorProject } from '../../constant';


const CreateProjectTypeSelectionModalBody = ({ handleProjectCreationTypeSelection}) => {

  const [projectTypeSelected,setProjectTypeSelected] = useState(0);
  const handleProjectTypeSelection = (isProjectTypeSelected,selectedType) => {
    handleProjectCreationTypeSelection(isProjectTypeSelected,selectedType);
  }

  return (
    <div className='pt-2'>
      <div className="row">
        <ul className="list-group">
          <li
            className={`list-group-item d-flex justify-content-between align-items-center py-2 border rounded mb-2 text-truncate ${projectTypeSelected === RLBasedPOCProject
              ? "app-primary-button-color border-0 text-white"
              : "bg-light"
              }`}
            style={{ zIndex: 1 ,cursor:"pointer"}}
            onClick={() => { handleProjectTypeSelection(true,RLBasedPOCProject);setProjectTypeSelected(RLBasedPOCProject) }}
          >
            <div className="d-flex justify-content-between ">
              <label className="form-check-label fw-bold">RL Based POC Project</label>
            </div>
          </li>
          <li
            className={`list-group-item d-flex justify-content-between align-items-center py-2 border rounded mb-2 text-truncate ${projectTypeSelected === TwoHunderedPlusTransistorProject
              ? "app-primary-button-color border-0 text-white"
              : "bg-light"
              }`}
            style={{ zIndex: 1 ,cursor: "pointer"}}
            onClick={() => { handleProjectTypeSelection(true,TwoHunderedPlusTransistorProject) ;setProjectTypeSelected(TwoHunderedPlusTransistorProject)}}
          >
            <div className="d-flex justify-content-between ">
              <label className="form-check-label fw-bold">Multiheight, 200+ Transistor POC Project</label>
            </div>
          </li>
        </ul>
      </div>
    </div>
  )
}

export default CreateProjectTypeSelectionModalBody;