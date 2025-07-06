
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: ListOfTechFile.js  
 * Description: This file handles the display and management of the list of tech files in the admin panel. 
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

import React, { useState, useCallback, useEffect } from 'react';
import { ToastContainer, toast } from "react-toastify";
import { DataGrid } from '@mui/x-data-grid';
import { Button } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTrash, faPen, faFilePen , faClone } from '@fortawesome/free-solid-svg-icons';
import { Empty } from 'antd';
import { getAdminListData, deleteAdminFile, getUserFileData, modifyUserFileData, renameUserFile , cloneUserFile} from '../../AdminServer/AdminServer';
import { useAdminContext } from '../../../components/providers/AdminProvider/AdminContext';
import { useTechFileContext } from '../../../components/providers/TechFileProvider/TechFileContext';
import { techFileDirType } from '../../../constant';
import ModalComponent from '../../../components/utils/Modal/ModalComponent'
import DeleteTechFileModal from './DeleteTechFileModal';
import ModifyTechFileModal from './ModifyTechFileModal';
import SaveAdminTechFileModalBody from './SaveAdminTechFileModalBody';


const ListOfTechFile = ({ setHandleTechData }) => {
    const { adminTechFileData, setAdminTechFileData, userTechFileContent, setUserTechFileContent } = useAdminContext();
    const {setTechFileData, techFileData} = useTechFileContext();
    const [deleteTechFileModal, setDeleteTechFileModal] = useState(false);
    const [selectedFileNameFromTechFile, setSelectedFileNameFromTechFile] = useState();
    const [paginationModel, setPaginationModel] = useState({
        pageSize: 25,
        page: 0,
    });
    const [modifyTechFileModal, setModifyTechFileModal] = useState(false);
    const [selectedUserName, setSelectedUserName] = useState();
    const [selectedFileId, setSelectedFileId] = useState();
    const [selectedTechFileType, setSelectedTechFileType] = useState();
    const [selectedTimeStamp,setSelectedTimeStamp] = useState();
    const [isLoading, setIsLoading] = useState(false);
    const [totalItems, setTotalItems] = useState(0);
    const [renameTechFileModal, setRenameTechFileModal] = useState(false);
    const [adminTechFileName, setAdminTechFileName] = useState(); 
    const [renameTechFileErrorMessage, setRenameTechFileErrorMessage] = useState();

    //function to normalize file type 
    const normalizeFileType = (fileType, originalFileType) => {
        // Converts display file type (username/"GLOBAL") to API format ("USER"/"GLOBAL")
        return originalFileType === 'USER' ? 'USER' : 'GLOBAL';
    };

    // below function is used to open delete modal
    const handleDeleteTechFile = async (selectedFileName) => {
        setSelectedFileNameFromTechFile(selectedFileName?.name)
        setSelectedFileId(selectedFileName?.fileId);
        setSelectedUserName(selectedFileName?.username);
        setSelectedTechFileType(normalizeFileType(selectedFileName?.filetype, selectedFileName?.originalFileType));
        setSelectedTimeStamp(selectedFileName?.createdDate)
        setDeleteTechFileModal(true);
    };

 // below function handles the rename tech file modal
    const handleRenameTechFile = (selectedFileData) => {
        setRenameTechFileModal(true);
        const fileNameWithoutExtension = selectedFileData?.name.split('.').slice(0, -1).join('.');
        setAdminTechFileName(fileNameWithoutExtension);
        setSelectedFileNameFromTechFile(selectedFileData?.name);
        setSelectedFileId(selectedFileData?.fileId);
        setSelectedUserName(selectedFileData?.username);
        setSelectedTechFileType(normalizeFileType(selectedFileData?.filetype, selectedFileData?.originalFileType));
    };

    // function below delete the techfile from list
    const handleTechFileDeleteButton = async () => {
        try {
            const deleteAdminFileReq = {
                FileId: selectedFileId,
                FileName: selectedFileNameFromTechFile,
                DirType: techFileDirType,
                FileType: selectedTechFileType,
                TimeStamp: selectedTimeStamp,
                USERNAME: selectedUserName
            };
            const techFileDeleteRes = await deleteAdminFile(deleteAdminFileReq);
            if (techFileDeleteRes?.status === true) {
                setDeleteTechFileModal(false);
                handleAdminTechData();
                toast.success(`${selectedFileNameFromTechFile} deleted successfully`, { autoClose: 10000 });
            }
            else {
                toast.error(techFileDeleteRes?.message)
            }
        }
        catch (error) {
            toast.error("Error While Deleting the Tech file",error)
            console.error("Error While Deleting the Tech file")
        }
    }
    // below function is used to modify the techfile
    const handleModifyTechFile = async (selectedFile) => {
        try {
            const userFileDataReq = {
                FileId: selectedFile?.fileId,
                FileName: selectedFile?.name,
                DirType: techFileDirType,
                FileType: normalizeFileType(selectedFile?.filetype, selectedFile?.originalFileType),
                USERNAME: selectedFile?.username
            };
            const techFileDataRes = await getUserFileData(userFileDataReq);
            if (techFileDataRes?.data?.status === true) {
                // if it is user selected tech file will be storing techdata in techcontext for showing table to user
                // if(selectedFile?.filetype === userFile){
                    setTechFileData(techFileDataRes?.data)
                // }
                setModifyTechFileModal(true);
                setSelectedFileNameFromTechFile(selectedFile?.name)
                setSelectedFileId(selectedFile?.fileId);
                setSelectedUserName(selectedFile?.username);
                setSelectedTimeStamp(selectedFile?.createdDate);
                setSelectedTechFileType(normalizeFileType(selectedFile?.filetype, selectedFile?.originalFileType));
                const decodedData = techFileDataRes?.data?.data && atob(techFileDataRes?.data?.data);
                setUserTechFileContent(decodedData);
            }
            else {
                toast.error(techFileDataRes?.message);
            }
        }
        catch (error) {
            console.error("Error while Modifying the tech file", error)
        }
    }

    // below function is used to save the modified techfile
    const handleSaveTechFile = async () => {
       // let techFileContent = selectedTechFileType === 'USER' ? techFileData?.data?.FileContent: btoa(userTechFileContent);
       let techFileContent = techFileData?.data?.FileContent;
       try {
            const modifyUserFileDataReq = {
                FileId: selectedFileId,
                FileName: selectedFileNameFromTechFile,
                DirType: techFileDirType,
                FileType: selectedTechFileType,
                USERNAME: selectedUserName,
                FileContents: techFileContent ,
            }
            const modifyTechFileRes = await modifyUserFileData(modifyUserFileDataReq);
            if (modifyTechFileRes?.data?.status === true) {
                setModifyTechFileModal(false);
                toast.success(`${selectedFileNameFromTechFile} ${modifyTechFileRes?.data?.message}`, { autoClose: 10000 });
            }
            else {
                toast.error(modifyTechFileRes?.message);
            }
        }
        catch (error) {
            toast.error("Error while saving tech file", error)
            console.error("Error while saving tech file", error)
        }
    }

    // below function is used to rename the tech file
    const handleRenameAdminTechFile = async () => {
        try {
            const renameAdminTechFileReq = {
                FileId: selectedFileId,
                FileName: selectedFileNameFromTechFile,
                DirType: techFileDirType,
                FileType: selectedTechFileType,
                USERNAME: selectedUserName,
                NewFileName: adminTechFileName
            };

            const renameAdminTechFileRes = await renameUserFile(renameAdminTechFileReq);

            if (renameAdminTechFileRes?.status_code === 200) {
                setRenameTechFileModal(false);
                handleAdminTechData();
                setRenameTechFileErrorMessage();
                toast.success(renameAdminTechFileRes?.message, { autoClose: 10000 });
            } else {
                setRenameTechFileErrorMessage(renameAdminTechFileRes);
            }
        } catch (error) {
            console.error("Error while renaming the tech file", error);
            toast.error("Error while renaming the tech file");
        }
    };

    // below function handles the cancel button on rename tech file modal
    const handleCancelRenameAdminTechFile = () => {
        setRenameTechFileModal(false);
        setRenameTechFileErrorMessage();
    };

    // Delete Modal Data 
    const deleteTechFileMessage = {
        title: "Confirm delete",
        body: <DeleteTechFileModal selectedFileNameFromTechFile={selectedFileNameFromTechFile} />,
        footer: (<>
            <Button  id="admin-tech-file-no-button" onClick={() => setDeleteTechFileModal(false)} className="app-secondary-button-color border-0 w-25">No</Button>
            <Button  id="admin-tech-file-delete-button" onClick={handleTechFileDeleteButton} className="w-25 delete-button-color border-0">Delete</Button>
        </>)
    }

    // Modify Modal Data
    const modifyTechFileContent = {
        title: (
            <div style={{ wordBreak: 'break-word' }}>
                Edit {selectedFileNameFromTechFile}
            </div>
        ),
        body: <ModifyTechFileModal  selectedTechFileType={selectedTechFileType} userTechFileContent={userTechFileContent} setUserTechFileContent={setUserTechFileContent} />,
        footer: (
            <>
              { techFileData?.data?.FileContent !==null && (  <Button    className='app-primary-button-color border-0 w-25' onClick={handleSaveTechFile}>Save</Button>)}
                <Button  className='w-25 app-secondary-button-color border-0' onClick={() => setModifyTechFileModal(false)}>Cancel</Button>
            </>
        )
    }

    // modal content for rename tech file
    const renameTechFileContent = {
        title: "Enter New Tech File Name:",
        body: <SaveAdminTechFileModalBody
            adminTechFileName={adminTechFileName}
            setAdminTechFileName={setAdminTechFileName}
            renameTechFileErrorMessage={renameTechFileErrorMessage}
        />,
        footer: (
            <>
                <Button className={adminTechFileName ? 'app-primary-button-color border-0 w-25' : 'app-secondary-button-color border-0 w-25 cursor_not_allowed'} disabled={!adminTechFileName} id="save-admin-tech-file" onClick={handleRenameAdminTechFile}>Save</Button>
                <Button className='app-secondary-button-color border-0 w-25' id="cancel-admin-tech-file" onClick={handleCancelRenameAdminTechFile}>Cancel</Button>
            </>
        )
    };

    const columns = [
        { field: 'name', headerName: 'Tech File Name', flex: 3 },
        {
            field: 'filetype',
            headerName: 'File Type',
            flex: 1,
            renderCell: (params) => params.value 
        },
        { field: 'createdDate', headerName: 'Created Date (UTC)', flex: 2 },
        {
            field: 'action', headerName: 'Action', flex: 1.1, renderCell: (params) => (
                <div className="d-flex align-items-center">
                    <Button
                        id="admin-edit-tech-button"
                        title='Edit Techfile'
                        variant="link"
                        onClick={() => handleModifyTechFile(params?.row)}>
                        <FontAwesomeIcon icon={faFilePen} className={`admin-button`} />
                    </Button>
                    <Button
                        id="admin-delete-tech-button"
                        title='Delete Techfile'
                        variant="link"
                        onClick={() => handleDeleteTechFile(params?.row)}
                    >
                        <FontAwesomeIcon icon={faTrash} className={`admin-button`} />
                    </Button>
                    <Button
                        id="rename-admin-tech-file"
                        title='Rename Techfile'
                        variant="link"
                        onClick={() => handleRenameTechFile(params?.row)}
                    >
                        <FontAwesomeIcon icon={faPen} className="admin-button" />
                    </Button>
                   
                    <Button
                        id="clone-admin-tech-file"
                        title='Clone Techfile'
                        variant="link"
                        onClick={() => handleCloneTechFile(params?.row)}
                    >
                        <FontAwesomeIcon icon={faClone} className="admin-button" />
                    </Button>
                </div>
            )
        },
    ];

    // below function call the API and loads the tech file data
    const handleAdminTechData = useCallback(async () => {
        try {
            const adminListDataReq = {
                "Filetype": techFileDirType,
                "page": paginationModel.page,
                "pageSize": paginationModel.pageSize,
            }
           
            const adminTechDataRes = await getAdminListData(adminListDataReq);
            if (adminTechDataRes?.status === true) {
                setTotalItems(adminTechDataRes?.data?.TotalItems)
                setAdminTechFileData(adminTechDataRes?.data?.Items);
                setIsLoading(false);
            }
            else {
                toast.error(adminTechDataRes?.message);
                setAdminTechFileData();
                setIsLoading(true);
            }
        } catch (error) {
            toast.error('Error fetching data:', error)
            console.error('Error fetching data:', error);
        }
    }, [setAdminTechFileData, paginationModel, setTotalItems]);

    // below use effect loads the data once 
    useEffect(() => {
        handleAdminTechData();
        setHandleTechData(() => handleAdminTechData);
    }, [handleAdminTechData, setHandleTechData, paginationModel]);


    //below function clone the techfile data
    const handleCloneTechFile = async (selectedFileData) => {

        try {
            const cloneTechRequest = {
                FileId: selectedFileData?.fileId
            };

            const cloneTechRes = await cloneUserFile(cloneTechRequest);

            if (cloneTechRes?.status === true) {
                toast.success(cloneTechRes?.message || "File cloned successfully!", { autoClose: 10000 });
                handleAdminTechData();
            } else {
                toast.error(cloneTechRes?.message || "Error while cloning tech file");
            }
        } catch (error) {
            toast.error("Error while cloning tech file");
            console.error("Error while cloning tech file:", error);
        }
    };



    return (
        <>
            <ToastContainer
                closeButton={true}
                position="top-center"
                autoClose={false}
                theme="colored"
            />
            <div className="d-flex justify-content-center h-100">
                <div
                    style={{
                        height: 'calc(93vh - 200px)',
                        width: '95%',
                        overflowY: 'auto',
                    }}
                >
                    {adminTechFileData?.length > 0 ?
                        (
                            <DataGrid
                                columns={columns}
                                rows={adminTechFileData?.map((data) => ({
                                    id: data?.FileId,
                                    name: data?.FileName,
                                    filetype: data?.FileType === 'USER' ? data?.USERNAME : 'GLOBAL',
                                    originalFileType: data?.FileType, // Keep original data
                                    createdDate: data?.TimeStamp,
                                    fileId: data?.FileId,
                                    username: data?.USERNAME,
                                }))}
                                paginationModel={paginationModel}
                                onPaginationModelChange={setPaginationModel}
                                rowsPerPageOptions={[25, 50, 75, 100]}
                                paginationMode="server"
                                rowCount={totalItems}
                                loading={isLoading}
                                sx={{
                                    '& .MuiDataGrid-columnHeaders': {
                                        color: '#1b5376',
                                    },
                                    '& .MuiDataGrid-columnHeaderTitle': {
                                        fontWeight: 'bold',
                                    }
                                }}
                            />
                        ) : isLoading ? (
                            <div className="d-flex justify-content-center align-items-center h-100">
                                <h2 className="text-gray-600"><Empty description={"No Tech Data Found"} /></h2>
                            </div>
                        ) : (
                            <div className='d-flex justify-content-center align-items-center h-100'>
                                <div className="spinner-border" role="status">
                                    <span className="sr-only">Loading...</span>
                                </div>
                            </div>
                        )}

                </div>
            </div>
            {/* modal for deleting techfile from list */}
            <ModalComponent
                id="admin-delete-tech-modal"
                size="md"
                show={deleteTechFileModal}
                handleClose={() => setDeleteTechFileModal(false)}
                modalContent={deleteTechFileMessage}
                modalCSSClass={"overflow-hidden;"}
                modalTitleCSSClass={{ color: '#910303' }}
            />
            {/* Modal for modifying user netlist file content */}
            <ModalComponent
                id="admin-modify-tech-modal"
                show={modifyTechFileModal}
                handleClose={() => setModifyTechFileModal(false)}
                modalContent={modifyTechFileContent}
                bodyClassName={"h-75"}
            />
            {/* Modal for renaming tech file */}
            <ModalComponent
                id="rename-tech-file-modal"
                show={renameTechFileModal}
                handleClose={handleCancelRenameAdminTechFile}
                modalContent={renameTechFileContent}
                modalCSSClass={"overflow-hidden;"}
                size="md"
            />
        </>
    )
}

export default ListOfTechFile