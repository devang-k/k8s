
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: AdminNetlist.js  
 * Description: This file is responsible to manage netlist file at admin level 
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
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faPlus } from "@fortawesome/free-solid-svg-icons";
import { Button } from "react-bootstrap";
import ListOfNetlistFile from "./ListOfNetlistFile";
import ModalComponent from "../../../components/utils/Modal/ModalComponent";
import UploadNetlistFileModal from "./UploadNetlistFileModal";
import { uploadUserNetlistFile } from "../../AdminServer/AdminServer";
import { toast, ToastContainer } from "react-toastify";
import { Tooltip as ReactTooltip } from 'react-tooltip'


const AdminNetlist = () => {
  const [uploadNetlistFileModal, setUploadNetlistFileModal] = useState(false);
  const [selectedNetlistFileFromLocal, setSelectedNetlistFileFromLocal] = useState(null);
  const [handleNetlistData, setHandleNetlistData] = useState(null);
  const [showErrorNetlistMessage, setShowErrorNetlistMessage] = useState([]);

  // below function handles uploading netlist file
  const handleUploadNetlistFile = async (event) => {
    event.preventDefault();
    const formData = new FormData();
    formData.append("upload", selectedNetlistFileFromLocal);
    try {
      const uploadNetlistFileRes = await uploadUserNetlistFile(formData);
      if (uploadNetlistFileRes?.status === true) {
        setUploadNetlistFileModal(false);
        handleNetlistData();
        setSelectedNetlistFileFromLocal(null);
        setShowErrorNetlistMessage([]);
        toast.success(uploadNetlistFileRes?.message, { autoClose: 10000 });
      } else {
        // Only show error messages in modal 
        if (
          uploadNetlistFileRes?.status_code === 203 &&
          Array.isArray(uploadNetlistFileRes?.message)
        ) {
          setShowErrorNetlistMessage(uploadNetlistFileRes?.message);
        } else {
          setShowErrorNetlistMessage([]);
          toast.error(uploadNetlistFileRes?.message);
        }

        setSelectedNetlistFileFromLocal(null);
      }
    } catch (error) {
      console.error("Error while uploading the netlist file.", error);
      setShowErrorNetlistMessage([]);
    }
  };

  // below function is set the netlist file which user selected
  const handleNetlistFileChange = (event) => {
    const file = event?.target?.files[0];
    setSelectedNetlistFileFromLocal(file);
    setShowErrorNetlistMessage([]);
  };

  // below function handles the cancel button on modal
  const handleUploadNetlistFileCancel = () => {
    setUploadNetlistFileModal(false);
    setSelectedNetlistFileFromLocal(null);
    setShowErrorNetlistMessage([]);
  };

  // upload netlist file modal data 
  const uploadNetlistFileModalContent = {
    title: "Choose Netlist File",
    body: (
      <UploadNetlistFileModal
        handleUploadNetlistFile={handleUploadNetlistFile}
        handleNetlistFileChange={handleNetlistFileChange}
      />
    ),
    footer: (
      <div className="d-flex flex-column align-items-center gap-2 w-100">
        {/* Display error list */}
        {showErrorNetlistMessage?.length > 0 && (
          <div className="w-100">
            <div
              style={{
                overflowY: showErrorNetlistMessage?.length > 5 ? "auto" : "visible",
                maxHeight: showErrorNetlistMessage?.length > 5 ? "150px" : "auto",
                paddingLeft: "20px",
                marginBottom: "0",
                textAlign: "left"
              }}
              className="text-danger"
            >
              {showErrorNetlistMessage.map((msg, index) => (
                <div key={index} style={{ marginBottom: "4px" }}>
                  {msg}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="d-flex justify-content-center gap-2 w-100">
          <div className="w-25">
            <Button
              disabled={!selectedNetlistFileFromLocal}
              id="admin-upload-netlist-file-button"
              data-tooltip-id="upload-netlist-file-button-tooltip"
              data-tooltip-content={!selectedNetlistFileFromLocal && "Choose Netlist File to upload"}
              type="submit"
              form="upload-netlist-file-form"
              className={`w-100 ${!selectedNetlistFileFromLocal ? "app-secondary-button-color border-0 cursor_not_allowed" : "app-primary-button-color border-0"}`}
            >
              Upload
            </Button>
            {!selectedNetlistFileFromLocal && <ReactTooltip id="upload-netlist-file-button-tooltip" place="top" style={{ width: "200px", zIndex: 9999 }} />}
          </div>
          <div className="w-25">
            <Button
              id="admin-upload-cancel-netlist-file-button"
              className="app-secondary-button-color border-0 w-100" onClick={handleUploadNetlistFileCancel}>
              Cancel
            </Button>
          </div>
        </div>
      </div>
    ),
  };

  // below function handles upload netlist file modal
  const handleAddNetlistFile = () => {
    setUploadNetlistFileModal(true);
    setShowErrorNetlistMessage([]); 
  };

  return (
    <>
    <ToastContainer
        closeButton={true}
        position="top-center"
        autoClose={false}
        theme="colored"
      />
      <div className="container-fluid m-0 p-0 h-100" style={{ maxHeight: "100%", overflow: "hidden" }}>
        <div className="d-flex flex-column align-items-center justify-content-center m-4">
          <h5>Netlist Files</h5>
          <p>Add and Manage Netlist Files.</p>
          <div className="d-flex justify-content-end w-100">
            <Button
              id="admin-add-netlist-button"
              className="btn btn-md d-flex gap-2 align-items-center app-primary-button-color border-0"
              onClick={handleAddNetlistFile}
            >
              <FontAwesomeIcon icon={faPlus} style={{ fontSize: "18px" }} />
              <span>Add</span>
            </Button>
          </div>
        </div>
        <ListOfNetlistFile setHandleNetlistData={setHandleNetlistData} />
        
      {/* Modal for uploading netlist file*/}
      <ModalComponent
          id={"upload-netlist-file-modal"}
          size="md"
          show={uploadNetlistFileModal}
          handleClose={handleUploadNetlistFileCancel}
          modalContent={uploadNetlistFileModalContent}
          modalCSSClass={"overflow-hidden;"}
        />
      </div>
    </>
  );
};

export default AdminNetlist;
