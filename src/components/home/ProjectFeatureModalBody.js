 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: ProjectFeatureModalBody.js  
 * Description: This file is responsible to show project feature modal content. 
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

import React from 'react';
import Circuit from "../../Assets/Images/networkwired.svg";
import Diagram from "../../Assets/Images/microchip.svg";
import { useCreateProjectContext } from '../providers/CreateProjectProvider/CreateProjectContext';
import { normalProjectType } from '../../constant';

const ProjectFeatureModalBody = ({ checkedItems, handleCheckboxChange }) => {

  const {typeOfSelectedProject} = useCreateProjectContext();
  
  return (

    <div className="container">
      <div className="row">
        <p className='invalid-feedback d-flex justify-content-center'>Selected feature(s) on this screen cannot be modified once the project is saved </p>
        <div className={`${typeOfSelectedProject === normalProjectType ? 'col-md-6' : 'col-md-10 mx-auto'}`}>
          <div className="card bg-transparent border-2 py-4 flex-grow-1">
            <label htmlFor="layoutGeneration" className="card-body py-5" style={{ cursor: 'pointer' }}>
              <div className="d-flex flex-column align-items-center text-center">
                <input
                  className="form-check-input position-absolute"
                  type="checkbox"
                  id="layoutGeneration"
                  name="layoutGeneration"
                  checked={checkedItems.layoutGeneration}
                  onChange={handleCheckboxChange}
                  style={{ top: '25px', left: '25px', zIndex: 1 }}
                />
                <img src={Circuit} alt="Layout Generation" className="img-fluid mb-3" style={{ maxWidth: '80px' }} />
                <span className="fw-bold text-muted">Layout Generation</span>
                <p className="card-text text-muted">
                  Create possible layouts for your cells based on netlist and PDK.
                </p>
              </div>
            </label>
          </div>
        </div>
        {(typeOfSelectedProject === normalProjectType) && (<div className="col-md-6">
          <div className="card bg-transparent border-2 py-4">
            <label htmlFor="layoutHyperexpressivity" className="card-body py-5" style={{ cursor: 'pointer' }}>
              <div className="d-flex flex-column align-items-center text-center">
                <input
                  className="form-check-input position-absolute"
                  type="checkbox"
                  id="layoutHyperexpressivity"
                  name="layoutHyperexpressivity"
                  checked={checkedItems.layoutHyperexpressivity}
                  onChange={handleCheckboxChange}
                  style={{ top: '25px', left: '25px', zIndex: 1 }}
                />
                <img src={Diagram} alt="Layout Hyperexpressivity" className="img-fluid mb-3" style={{ maxWidth: '80px' }} />
                <span className="fw-bold text-muted">Layout Hyperexpressivity</span>
                <p className="card-text text-muted">
                  Create electronically valid cell permutations from your cells layout.
                </p>
              </div>
            </label>
          </div>
        </div>)}
      </div>
    </div>

  );
};

export default ProjectFeatureModalBody;
