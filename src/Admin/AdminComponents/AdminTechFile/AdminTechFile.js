 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: AdminTechFile.js  
 * Description: This file is responsible to manage tech file at admin level 
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
import ListOfTechFile from "./ListOfTechFile";
import ModalComponent from "../../../components/utils/Modal/ModalComponent";
import UploadTechFileModal from "./UploadTechFileModal";
import { uploadUserTechFile } from "../../AdminServer/AdminServer";
import { toast, ToastContainer } from "react-toastify";
import { Tooltip as ReactTooltip } from 'react-tooltip'


const AdminTechFile = () => {
    const [uploadTechFileModal, setUploadTechFileModal] = useState(false);
    const [selectedTechFileFromLocal, setSelectedTechFileFromLocal] = useState(null);
    const [handleTechData, setHandleTechData] = useState(null);

    // below function handles uploading tech file
    const handleUploadTechFile = async (event) => {
        event.preventDefault();
        const formData = new FormData();
        formData.append("upload", selectedTechFileFromLocal);
        try {
            const uploadTechFileRes = await uploadUserTechFile(formData);
            if (uploadTechFileRes?.status === true) {
                setUploadTechFileModal(false);
                handleTechData();
                setSelectedTechFileFromLocal(null);
                toast.success(uploadTechFileRes?.message, { autoClose: 10000, toastId: "toaster-upload" });
            } else {
                toast.error(uploadTechFileRes?.message);
                setSelectedTechFileFromLocal(null);
            }
        } catch (error) {
            console.error("Error while uploading the Tech file.", error);
        }
    };

    // below function is set the tech file which user selected
    const handleTechFileChange = (event) => {
        const file = event?.target?.files[0];
        setSelectedTechFileFromLocal(file);
    };

    // below function handles the cancel button on modal
    const handleUploadTechFileCancel = () => {
        setUploadTechFileModal(false);
        setSelectedTechFileFromLocal(null);
    };

    // upload tech file modal data 
    const uploadTechFileModalContent = {
        title: "Choose Tech File",
        body: (
            <UploadTechFileModal
                handleUploadTechFile={handleUploadTechFile}
                handleTechFileChange={handleTechFileChange}
            />
        ),
        footer: (
            <>
                <div className="d-flex justify-content-center gap-2">
                    <div className="w-25">
                        <Button
                            disabled={!selectedTechFileFromLocal}
                            id="admin-upload-Tech-file-button"
                            data-tooltip-id="upload-Tech-file-button-tooltip"
                            data-tooltip-content={!selectedTechFileFromLocal && "Choose Tech File to upload"}
                            type="submit"
                            form="upload-tech-file-form"
                            className={`w-100 ${!selectedTechFileFromLocal ? "app-secondary-button-color border-0 cursor_not_allowed" : "app-primary-button-color border-0"}`}
                        >
                            Upload
                        </Button>
                        {!selectedTechFileFromLocal && <ReactTooltip id="upload-tech-file-button-tooltip" place="top" style={{ width: "200px", zIndex: 9999 }} />}
                    </div>
                    <div className="w-25">
                        <Button
                            id="admin-upload-cancel-tech-file-button"
                            className="w-100 app-secondary-button-color border-0" onClick={handleUploadTechFileCancel}>
                            Cancel
                        </Button>
                    </div>
                </div>
            </>
        ),
    };

    // below function handles upload tech file modal
    const handleAddTechFile = () => {
        setUploadTechFileModal(true);
    };

    return (
        <>
            <ToastContainer
                containerId="upload-toaster"
                closeButton={true}
                position="top-center"
                autoClose={false}
                theme="colored"
            />
            <div className="container-fluid m-0 p-0 h-100" style={{ maxHeight: "100%", overflow: "hidden" }}>
                <div className="d-flex flex-column align-items-center justify-content-center m-4">
                    <h5>Tech Files</h5>
                    <p>Add and Manage Tech Files</p>
                    <div className="d-flex justify-content-end w-100">
                        <Button
                            id="admin-add-tech-button"
                            className="btn btn-md d-flex gap-2 align-items-center app-primary-button-color border-0"
                            onClick={handleAddTechFile}
                        >
                            <FontAwesomeIcon icon={faPlus} style={{ fontSize: "18px"}} />
                            <span>Add</span>
                        </Button>
                    </div>
                </div>
                <ListOfTechFile setHandleTechData={setHandleTechData} />

                {/* Modal for uploading tech file*/}
                <ModalComponent
                    id={"upload-tech-file-modal"}
                    size="md"
                    show={uploadTechFileModal}
                    handleClose={handleUploadTechFileCancel}
                    modalContent={uploadTechFileModalContent}
                    modalCSSClass={"overflow-hidden;"}
                />
            </div>
        </>
    );
};

export default AdminTechFile;
