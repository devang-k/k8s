
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: CreateProjectModalBody.js  
 * Description: This file is responsible to show and handle create project modal content 
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
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faPlus, faFileLines } from "@fortawesome/free-solid-svg-icons";
import { Tooltip } from "react-tooltip";
import { useCreateProjectContext } from "../providers/CreateProjectProvider/CreateProjectContext";

const CreateProjectModalBody = ({
  projectName,
  setProjectName,
  projectNameError,
  setProjectNameError,
  handleCreateNewProjectClick,
  handleCreatePOCProjectType,
}) => {
  const { inPreviousThroughHyperExpressivityProjectCreation } = useCreateProjectContext();
  const isPOCProjectEnabled = process.env.REACT_APP_ENABLE_POC_BUTTON === "true" // environment variables are always passed as strings, so we need to convert the string value "true" or "false" to an actual boolean .

  const handleInputChange = (e) => {
    let inputValue = e.target.value.trimStart();
    inputValue = inputValue.replace(/\s+$/, " ");

    setProjectName(inputValue);

    if (inputValue.length < 2 || inputValue.length > 100) {
      setProjectNameError("Project name must be between 2 and 100 characters.");
    } else {
      setProjectNameError("");
    }
  };

  const isCreateNewProjectDisabled = !projectName || projectNameError;

  return (
    <>
      <div className="w-100">
        <div className="form-group">
          <label htmlFor="projectName" className="col-form-label">
            Project Name:
          </label>
          <input
            id="projectName"
            name="projectName"
            type="text"
            className="form-control p-2 m-0 border-0 bg-light text-dark"
            value={projectName}
            maxLength={100}
            minLength={2}
            placeholder="Enter project name"
            onChange={handleInputChange}
          />
          <div className="error-msg-container">
            {projectNameError && (
              <small className="text-danger">{projectNameError}</small>
            )}
          </div>
        </div>
        <div className="form-group mt-4">
          <label htmlFor="create-project mt-4" className="col-form-label">
            How do you want to create your new project?
          </label>
          <div className="container">
            <div className="row">
              <div className="col-md-6 mb-4">
                <div className="card bg-transparent border-0">
                  <button
                    className={`py-5 btn ${isCreateNewProjectDisabled || inPreviousThroughHyperExpressivityProjectCreation
                      ? "btn-outline-secondary text-muted disabled cursor_not_allowed"
                      : "create-project-button-border"
                      }`}
                    onClick={handleCreateNewProjectClick}
                    disabled={isCreateNewProjectDisabled || inPreviousThroughHyperExpressivityProjectCreation}
                    data-tooltip-id="create-project-tooltip"
                    data-tooltip-content="Project Name is required to proceed ahead."
                    data-tooltip-place="top"
                  >
                    <FontAwesomeIcon
                      icon={faPlus}
                      className="mb-2 create-project-button-text"
                      style={{ fontSize: "48px" }}
                    />
                    <br />
                    <span className="fw-bold create-project-button-text" >Create New Project</span>
                  </button>
                  {isCreateNewProjectDisabled && (
                    <Tooltip id="create-project-tooltip" />
                  )}
                </div>
              </div>
              <div className="col-md-6 mb-4">
                <div className="card bg-transparent border-0">
                  <button
                    className={`py-5 btn ${!isPOCProjectEnabled || isCreateNewProjectDisabled || inPreviousThroughHyperExpressivityProjectCreation
                      ? "create-project-button-disable-border text-muted disabled cursor_not_allowed"
                      : "create-project-button-border"
                      }`}
                    disabled={!isPOCProjectEnabled || isCreateNewProjectDisabled || inPreviousThroughHyperExpressivityProjectCreation}
                    data-tooltip-id="create-project-tooltip"
                    data-tooltip-content="Project Name is required to proceed ahead."
                    data-tooltip-place="top"
                    onClick={handleCreatePOCProjectType}
                  >
                    <FontAwesomeIcon
                      icon={faFileLines}
                      className="mb-2 create-project-button-text"
                      style={{ fontSize: "48px" }}
                    />
                    <br />
                    <span className="fw-bold create-project-button-text">Create POC Project</span>
                  </button>
                  {isCreateNewProjectDisabled && (
                    <Tooltip id="create-project-tooltip" />
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default CreateProjectModalBody;
