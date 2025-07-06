
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: ListOfNetlistFile.js  
 * Description: This file is responsible to list all netlist files at admin level 
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

import React, { useCallback, useEffect, useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTrash, faPen, faFilePen, faClone } from '@fortawesome/free-solid-svg-icons';
import { Empty } from 'antd';
import { getAdminListData, deleteAdminFile, modifyUserFileData, getUserFileData, renameUserFile, cloneUserFile } from '../../AdminServer/AdminServer';
import { DataGrid } from '@mui/x-data-grid';
import { Button } from 'react-bootstrap';
import { toast } from "react-toastify";
import { useAdminContext } from '../../../components/providers/AdminProvider/AdminContext';
import { netlistDirType } from '../../../constant';
import ModalComponent from '../../../components/utils/Modal/ModalComponent';
import ModifyNetlistFileModal from './ModifyNetlistFileModal';
import DeleteNetlistFileModal from './DeleteNetlistFileModal';
import { checkValidationNetlist } from '../../../server/server';
import SaveAdminNetlistFileModalBody from './SaveAdminNetlistFileModalBody';


const ListOfNetlistFile = ({ setHandleNetlistData }) => {
  const { adminNetlistFileData, setAdminNetlistFileData, userNetlistFileContent, setUserNetlistFileContent, defultNetlistContent,
    setDefaultNetlistContent } = useAdminContext();
  const [deleteNetlistFileModal, setDeleteNetlistFileModal] = useState(false);
  const [selectedNetlistFileName, setSelectedNetlistFileName] = useState();
  const [paginationModel, setPaginationModel] = useState({
    pageSize: 25,
    page: 0,
  });
  const [modifyNetlistFileModal, setModifyNetlistFileModal] = useState(false);
  const [selectedUserName, setSelectedUserName] = useState();
  const [selectedFileId, setSelectedFileId] = useState();
  const [selectedNetlistFileType, setSelectedNetlistFileType] = useState();
  const [selectedTimeStamp, setSelectedTimeStamp] = useState();
  const [isLoading, setIsLoading] = useState(false);
  const [totalItems, setTotalItems] = useState(0);
  const [validationError, setValidationError] = useState('');
  const [renameNetlistModal, setRenameNetlistModal] = useState(false);
  const [adminNetlistFileName, setAdminNetlistFileName] = useState();
  const [renameNetlistFileErrorMessage, setRenameNetlistFileErrorMessage] = useState();


  //function to normalize file type 
  const normalizeFileType = (fileType, originalFileType) => {
    // Converts display file type (username/"GLOBAL") to API format ("USER"/"GLOBAL")
    return originalFileType === 'USER' ? 'USER' : 'GLOBAL';
  };

  // below function is used to open delete modal
  const handleDeleteNetlistFile = async (selectedFileData) => {
    setSelectedFileId(selectedFileData?.fileId);
    setSelectedUserName(selectedFileData?.username);
    setSelectedNetlistFileName(selectedFileData?.name);
    setSelectedTimeStamp(selectedFileData?.createdDate);
    setSelectedNetlistFileType(normalizeFileType(selectedFileData?.filetype, selectedFileData?.originalFileType));
    setDeleteNetlistFileModal(true);
  };

 // below function handles the rename netlist file modal
  const handleRenameNetlistFile = async (selectedFileData) => {
    setRenameNetlistModal(true);
    const fileName = selectedFileData?.name.split('.').slice(0, -1).join('.');
    setAdminNetlistFileName(fileName);
    setSelectedNetlistFileName(selectedFileData?.name);
    setSelectedFileId(selectedFileData?.fileId);
    setSelectedUserName(selectedFileData?.username);
    setSelectedNetlistFileType(normalizeFileType(selectedFileData?.filetype, selectedFileData.originalFileType));

  }
  // below function is used to modify the netlist file
  const handleModifyNetlistFile = async (selectedFile) => {
    try {
      const userFileDataReq = {
        FileId: selectedFile?.fileId,
        FileName: selectedFile?.name,
        DirType: netlistDirType,
        FileType: normalizeFileType(selectedFile?.filetype, selectedFile?.originalFileType),
        USERNAME: selectedFile?.username
      };
      const netlistFileDataRes = await getUserFileData(userFileDataReq);
      if (netlistFileDataRes?.data?.status === true) {
        setSelectedFileId(selectedFile?.fileId);
        setSelectedUserName(selectedFile?.username);
        setSelectedNetlistFileName(selectedFile?.name);
        setSelectedTimeStamp(selectedFile?.createdDate);
        setSelectedNetlistFileType(normalizeFileType(selectedFile?.filetype, selectedFile?.originalFileType));
        const decodedNetlistFileContent = atob(netlistFileDataRes?.data?.data)
        setUserNetlistFileContent(decodedNetlistFileContent);
        setModifyNetlistFileModal(true);
        setDefaultNetlistContent({
          userNetlistFileContent: decodedNetlistFileContent
        }
        )
      }
      else {
        toast.error(netlistFileDataRes?.message)
      }
    }
    catch (error) {
      console.error("Error while getting user data", error);
    }

  };

  // below function is used to save the modified netlist file
  const handleSaveNetlistFile = async () => {
    try {
      setValidationError(''); // Reset validation error

      const validationResponse = await checkValidationNetlist(userNetlistFileContent);  //  validate netlist content

      if (!validationResponse?.status) {
        setValidationError(validationResponse?.message);
        return;
      }

      const modifyUserFileDataReq = {
        FileId: selectedFileId,
        FileName: selectedNetlistFileName,
        DirType: netlistDirType,
        FileType: selectedNetlistFileType,
        USERNAME: selectedUserName,
        FileContents: btoa(userNetlistFileContent)
      }
      const modifyNetlistFileRes = await modifyUserFileData(modifyUserFileDataReq);
      if (modifyNetlistFileRes?.data?.status === true) {
        setModifyNetlistFileModal(false);
        setValidationError(''); // Clear error on successful save
        toast.success(`${selectedNetlistFileName} ${modifyNetlistFileRes?.data?.message}`, { autoClose: 10000 });
      }
      else {
        toast.error(modifyNetlistFileRes?.data?.message);
      }
    } catch (error) {
      setValidationError('Error while modifying the netlist File');
      console.error("Error while modifying the netlist File:", error);
    }
  };


  // below function calls delete endpoint when user 
  const handleNetlistFileDeleteButton = async () => {
    try {
      const deleteAdminFileReq = {
        FileId: selectedFileId,
        FileName: selectedNetlistFileName,
        DirType: netlistDirType,
        FileType: selectedNetlistFileType,
        TimeStamp: selectedTimeStamp,
        USERNAME: selectedUserName
      };
      const netlistFileDeleteRes = await deleteAdminFile(deleteAdminFileReq);
      if (netlistFileDeleteRes?.status === true) {
        setDeleteNetlistFileModal(false);
        handleAdminNetlistData();
        toast.success(`${selectedNetlistFileName} ${netlistFileDeleteRes?.message}`, { autoClose: 10000 })
      }
      else {
        toast.error(netlistFileDeleteRes?.message)
      }
    }
    catch (error) {
      toast.error("Error While Deleting the netlist file")
      console.error("Error While Deleting the netlist file")
    }
  }

// below function is used to rename the netlist file
const handleRenameAdminNetlistFile = async () => {
  try { 
    const renameAdminNetlistFileReq = {
      FileId: selectedFileId,
      FileName: selectedNetlistFileName,
      DirType: netlistDirType,
      FileType: selectedNetlistFileType,
      USERNAME: selectedUserName,
      NewFileName: adminNetlistFileName
    };
    const renameAdminNetlistFileRes = await renameUserFile(renameAdminNetlistFileReq);
    if (renameAdminNetlistFileRes?.status_code === 200) {
      setRenameNetlistModal(false);
      handleAdminNetlistData();
      setRenameNetlistFileErrorMessage();
      toast.success(renameAdminNetlistFileRes?.message, { autoClose: 10000 })
    }
    else {
      setRenameNetlistFileErrorMessage(renameAdminNetlistFileRes)
    }
  }
  catch(Error){
    console.error("Error while renaming the netlist file", Error);
  }
}

// below function is used to cancel the rename netlist file modal
const handleCancelRenameAdminNetlistFile = () => {
  setRenameNetlistModal(false);
  setRenameNetlistFileErrorMessage();
}

  //reset netlistfile content
  const handleResetNetlistFile = useCallback(() => {
    if (defultNetlistContent) {
      setUserNetlistFileContent(defultNetlistContent?.userNetlistFileContent);
    }
    setValidationError(false)

  }, [defultNetlistContent, setUserNetlistFileContent, setValidationError]);


  // Delete Modal Data 
  const deleteNelistFileMessage = {
    title: "Confirm delete",
    body: <DeleteNetlistFileModal selectedNetlistFileName={selectedNetlistFileName} />,
    footer: (<>
      <Button id="admin-netlist-file-no-button" onClick={() => setDeleteNetlistFileModal(false)} className="app-secondary-button-color border-0 w-25">No</Button>
      <Button id="admin-netlist-file-delete-button" onClick={handleNetlistFileDeleteButton} className="w-25 delete-button-color border-0">Delete</Button>
    </>)
  }

  // Modify Modal Data
  const modifyNetlistFileContent = {
    title: (<>
      <div style={{ wordBreak: 'break-word' }}>
        Edit {selectedNetlistFileName}
      </div>
    </>
    ),
    body: <ModifyNetlistFileModal
      userNetlistFileContent={userNetlistFileContent}
      setUserNetlistFileContent={setUserNetlistFileContent}
      validationError={validationError}
      setValidationError={setValidationError}
      handleResetNetlistFile={handleResetNetlistFile}
    />,

    footer: (<>
      <Button className='app-primary-button-color border-0 w-25' id="admin-save-netlist-file-button" onClick={handleSaveNetlistFile}>Save</Button>
      <Button className='app-secondary-button-color border-0 w-25' id="admin-cancel-save-netlist-file-button" onClick={() => {
        setModifyNetlistFileModal(false);
        setValidationError('');
      }} >Cancel</Button>
    </>)
  }

  // modal content for rename netlist file 
  const renameNetlistFileContent = {
    title: "Enter New Netlist File Name:",
    body: <SaveAdminNetlistFileModalBody adminNetlistFileName={adminNetlistFileName} setAdminNetlistFileName={setAdminNetlistFileName} renameNetlistFileErrorMessage={renameNetlistFileErrorMessage} />,
    footer:(
      <>
      <Button className={adminNetlistFileName ? `app-primary-button-color border-0 w-25` : `app-secondary-button-color border-0 w-25 cursor_not_allowed`} disabled={!adminNetlistFileName} id="save-admin-netlist-file" onClick={handleRenameAdminNetlistFile}>Save</Button>
      <Button className='app-secondary-button-color border-0 w-25' id="cancel-admin-netlist-file" onClick={handleCancelRenameAdminNetlistFile}>Cancel</Button>
      </>
    )
  }
  const columns = [
    { field: 'name', headerName: 'Netlist File Name', flex: 3 },
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
            id="admin-edit-netlist-button"
            title='Edit Netlist'
            variant="link"
            onClick={() => handleModifyNetlistFile(params?.row)}>
            <FontAwesomeIcon icon={faFilePen} className={`admin-button`} />
          </Button>
          <Button
            id="admin-delete-netlist-button"
            title='Delete Netlist'
            variant="link"
            onClick={() => handleDeleteNetlistFile(params?.row)}
          >
            <FontAwesomeIcon icon={faTrash} className={`admin-button`} />
          </Button>
          <Button
            id="rename-admin-netlist"
            title='Rename Netlist'
            variant="link"
            onClick={() => handleRenameNetlistFile(params?.row)}
           >
            <FontAwesomeIcon icon={faPen} className={`admin-button`} />
           </Button>
          <Button
            id="clone-admin-netlist"
            title='Clone Netlist'
            variant="link"
            onClick={() => handleCloneNetlistFile(params?.row)}
          >
            <FontAwesomeIcon icon={faClone} className={`admin-button`} />
          </Button>
        </div>
      )
    },
  ];

  // below function call the API and loads the netlist file data
  const handleAdminNetlistData = useCallback(async () => {
    try {
      const adminListDataReq = {
        "Filetype": netlistDirType,
        "page": paginationModel.page,
        "pageSize": paginationModel.pageSize,
      }
      const adminNetlistDataRes = await getAdminListData(adminListDataReq);
      if (adminNetlistDataRes?.status === true) {
        setTotalItems(adminNetlistDataRes?.data?.TotalItems)
        setAdminNetlistFileData(adminNetlistDataRes?.data?.Items);
        setIsLoading(false);
      }
      else {
        toast.error(adminNetlistDataRes?.message);
        setAdminNetlistFileData();
        setIsLoading(true);
      }
    } catch (error) {
      toast.error('Error fetching data:', error);
      console.error('Error fetching data:', error);
    }
  }, [setAdminNetlistFileData, paginationModel, setTotalItems]);

  // below use effect loads the data once 
  useEffect(() => {
    handleAdminNetlistData();
    setHandleNetlistData(() => handleAdminNetlistData);
  }, [handleAdminNetlistData, setHandleNetlistData, paginationModel]);

//below function clone the netlistfile data
  const handleCloneNetlistFile = async (selectedFileData) => {
    
    try {
      const cloneNetlistRequest = {
        FileId: selectedFileData?.fileId,
      };

      const cloneNetlistRes = await cloneUserFile(cloneNetlistRequest);
      
      if (cloneNetlistRes?.status === true) {
        toast.success(cloneNetlistRes?.message || "File cloned successfully!", { autoClose: 10000 });
        handleAdminNetlistData(); 
      } else {
        toast.error(cloneNetlistRes?.message || "Error while cloning netlist file");
      }
    } catch (error) {
      toast.error("Error while cloning netlist file");
      console.error("Error while cloning netlist file:", error);
    }
  };
  
  return (
    <>
      <div className="d-flex justify-content-center h-100">
        <div
          style={{
            height: 'calc(93vh - 200px)',
            width: '95%',
            overflowY: 'auto',
          }}
        >
          {
            adminNetlistFileData?.length > 0 ?
              (
                <DataGrid
                  columns={columns}
                  rows={adminNetlistFileData?.map((data) => ({
                    id: data?.FileId,
                    name: data?.FileName,
                    filetype: data?.FileType === 'USER' ? data?.USERNAME : 'GLOBAL',
                    originalFileType: data?.FileType,
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
                />) : isLoading ? (
                  <div className="d-flex justify-content-center align-items-center h-100">
                    <h2 className="text-gray-600"><Empty description={"No Netlist Data Found"} /></h2>
                  </div>
                ) : (
                <div className='d-flex justify-content-center align-items-center h-100'>
                  <div className="spinner-border" role="status">
                    <span className="sr-only">Loading...</span>
                  </div>
                </div>
              )
          }
        </div>
      </div>
      {/* Modal for getting user confirmation to delete the netlist file or not */}
      <ModalComponent
        id="admin-delete-netlist-modal"
        size="md"
        show={deleteNetlistFileModal}
        handleClose={() => setDeleteNetlistFileModal(false)}
        modalContent={deleteNelistFileMessage}
        modalCSSClass={"overflow-hidden;"}
        modalTitleCSSClass={{ color: '#910303' }}
      />
      {/* Modal for modifying user netlist file content */}
      <ModalComponent
        id="admin-modify-netlist-modal"
        show={modifyNetlistFileModal}
        handleClose={() => { setModifyNetlistFileModal(false); setValidationError('') }}
        modalContent={modifyNetlistFileContent}
      />
      {/* Modal for renaming netlist file */}
      <ModalComponent
      id="rename-netlist-file-modal"
      show={renameNetlistModal}
      handleClose={handleCancelRenameAdminNetlistFile}
      modalContent={renameNetlistFileContent}
      modalCSSClass={"overflow-hidden;"}   
      size="md"
      />
    </>
  );
};

export default ListOfNetlistFile;
