
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: ViewUsersData.js  
 * Description: This file is responsible to view users at admin page. 
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

import React, { useEffect, useState } from 'react';
import { DataGrid } from '@mui/x-data-grid';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTrash, faTrashArrowUp, faEyeSlash, faEye, faPen, faUnlock } from '@fortawesome/free-solid-svg-icons';
import { Button, Spinner } from 'react-bootstrap';
import ModalComponent from '../../../components/utils/Modal/ModalComponent';
import { toggleUserActiveStatus } from './toggleUserActiveStatus';
import { deleteUser } from './DeleteUser';
import { Empty } from 'antd';
import EditUserForm from './EditUserForm';
import ResetPassword from './ResetPassword';
import { adminPageSize } from '../../../constant';
import { deleteUserData } from "../../AdminServer/AdminServer";
import { toast } from "react-toastify";
import { useManageUserContext } from '../../../components/providers/ManageUserProvider/ManageUserContext';

const ViewUsersData = ({ userData, isLoading, handleUserData }) => {
    const {  totalUsersCount } = useManageUserContext();
    const [userToggleActiveModal, setUserToggleActiveModal] = useState(false);
    const [userDeleteModal, setUserDeleteModal] = useState(false);
    const [updateUserModal, setUpdateUserModal] = useState(false);
    const [passwordChangeModal, setPasswordChangeModal] = useState(false);
    const [selectedUserId, setSelectedUserId] = useState();
    const [paginationModel, setPaginationModel] = useState({
        pageSize: adminPageSize,
        page: 0,
    });
    const [deletedUserList, setDeletedUserList] = useState(null);
    const loggedInUsername = localStorage.getItem("username");
   


    const handleUpdateUser = (userId) => {
        setUpdateUserModal(true);
        setSelectedUserId(userId);
    };

    const handleUserToggleActive = (userId) => {
        setUserToggleActiveModal(true);
        setSelectedUserId(userId);
    };

    const handlePasswordChange = (userId) => {
        setPasswordChangeModal(true);
        setSelectedUserId(userId);
    };

    const handleDeleteUserData = (userId) => {
        setUserDeleteModal(true);
        setSelectedUserId(userId);
    };

    // below function handles to restore the user if the user is deleted
    const handleUnDeleteUserData = async (userId) => {
        try {
            // Passing false to restore the user 
            const response = await deleteUserData(userId, false);
            if (response?.status === true) {
                handleUserData(); // Refresh data after status change
                toast.success(response?.message, { autoClose: 10000 });
            } else {
                toast.error(response?.message || "Failed to delete user.");
            }
        } catch (error) {
            console.error("Error Restoring user:", error);
            toast.error("Failed to Restore user. Please try again.");
        }
    }

    const handleUserToggleActiveButton = () => {
        const newStatus = !selectedUser?.is_active;
        toggleUserActiveStatus(selectedUserId, newStatus, handleUserData, () => setUserToggleActiveModal(false));
    };

    const handleDeleteUserDataButton = () => {
        deleteUser(selectedUserId, handleUserData, () => setUserDeleteModal(false));
    };

    // below useEffect make array of which user is deleted from the list 
    useEffect(() => {
        const deletedItems = userData?.filter(item => item?.is_deleted === true)?.map(item => ({
            username: item?.username
        }));
        setDeletedUserList(deletedItems)
    }, [userData])

    useEffect(() => {
        handleUserData(paginationModel?.page, paginationModel?.pageSize);
    }, [handleUserData,paginationModel?.page, paginationModel?.pageSize]);

    const columns = [
        { field: 'name', headerName: 'Name', flex: 3 },
        { field: 'username', headerName: 'User Name', flex: 3 },
        { field: 'email', headerName: 'Email', flex: 3 },
        {
            field: 'is_active',
            headerName: 'Is Active',
            flex: 3,
            renderCell: (params) => (
                <span>{params?.row?.is_active ? "Yes" : "No"}</span>
            ),
        },
        { field: 'is_admin', headerName: 'Is Admin', flex: 3 },
        {
            field: "log_level", headerName: 'Logging Level', flex: 3},
        {
            field: 'action',
            headerName: 'Action',
            flex: 3,
            renderCell: (params) => {
                // Check if the username exists in the unDeleteUserData array
                const isDeleteDisabled = deletedUserList?.some(user => user?.username === params?.row?.username);
                const isLoggedInUser = String(params?.row?.username).toLocaleLowerCase() === String(loggedInUsername).toLocaleLowerCase();

                const canEdit = (!isLoggedInUser && (params?.row?.can_edit ?? true)) ? true : false;
                const canDelete = (!isLoggedInUser && (params?.row?.can_delete ?? true)) ? true : false;
                const canDisable = (!isLoggedInUser && (params?.row?.can_disable ?? true)) ? true : false;

                return (
                    <div className="d-flex justify-content-center gap-2 align-items-center">
                        {!isDeleteDisabled ? (
                            <>
                                {/* Edit Button */}
                                <Button
                                    className={`app-primary-text-color p-0 ${canEdit ? '' : 'invisible'}`}
                                    id="manage-user-edit-button"
                                    title='Update User Data'
                                    variant='link'
                                    onClick={() => handleUpdateUser(params?.row?.id)}
                                    style={{ width: '32px', height: '32px' }}
                                >
                                    <FontAwesomeIcon icon={faPen} className="admin-button" />
                                </Button>

                                {/* Enable/Disable Button */}
                                <Button
                                    className={`app-primary-text-color p-0 ${canDisable ? '' : 'invisible'}`}
                                    id="manage-user-toggle-active-button"
                                    title={params?.row?.is_active ? "Disable User" : "Enable User"}
                                    variant="link"
                                    onClick={() => handleUserToggleActive(params?.row?.id)}
                                    style={{ width: '32px', height: '32px' }}
                                >
                                    <FontAwesomeIcon
                                        icon={params?.row?.is_active ? faEyeSlash : faEye}
                                        className={`admin-button`}
                                    />
                                </Button>

                                {/* Reset Password Button*/}
                                <Button
                                    className="p-0"
                                    id="manage-user-password-reset-button"
                                    title='Reset Password'
                                    variant="link"
                                    onClick={() => handlePasswordChange(params?.row?.id)}
                                    style={{ width: '32px', height: '32px' }}
                                >
                                    <FontAwesomeIcon icon={faUnlock} className={`admin-button`} />
                                </Button>

                                {/* Delete Button */}
                                <Button
                                    className={`p-0 ${canDelete ? '' : 'invisible'}`}
                                    id="manage-user-delete-button"
                                    title='Delete User'
                                    variant="link"
                                    onClick={() => handleDeleteUserData(params?.row?.id)}
                                    style={{ width: '32px', height: '32px' }}
                                >
                                    <FontAwesomeIcon
                                        icon={faTrash}
                                        className={`admin-button`}
                                    />
                                </Button>
                            </>
                        ) : (
                            <Button
                                style={{
                                    width: '160px',
                                }}
                                id="manage-user-undelete-button"
                                title='Restore User'
                                variant="link"
                                onClick={() => handleUnDeleteUserData(params?.row?.id)}
                            >
                                <FontAwesomeIcon
                                    icon={faTrashArrowUp}
                                    className={`admin-button`}
                                />
                            </Button>
                        )}
                    </div>
                );
            },
        },
    ];


    const userDataRows = userData?.map((user) => ({
        id: user?.id,
        username: user?.username,
        name: user?.name,
        email: user?.email,
        is_active: user?.is_active,
        is_admin: user?.is_staff ? "Yes" : "No",
        log_level: user?.log_level ?? "N/A",

    }));
    

    const selectedUser = userDataRows?.find((user) => user?.id === selectedUserId);

    const userToggleActiveMessage = {
        title: selectedUser?.is_active ? "Confirm Disable User" : "Confirm Enable User",
        body: (
            <span>
                Are you sure you want to {selectedUser?.is_active ? "disable" : "enable"} user <strong>{selectedUser?.username}</strong>?
            </span>
        ),
        footer: (
            <>
                <Button  onClick={() => setUserToggleActiveModal(false)} className="w-25 app-secondary-button-color border-0 no-hover-effect">No</Button>
                <Button  onClick={handleUserToggleActiveButton} className={`w-25 text-white ${selectedUser?.is_active ? "delete-button-color border-0" : "app-primary-button-color border-0"}  no-hover-effect`}>
                    {selectedUser?.is_active ? "Disable" : "Enable"}
                </Button>
            </>
        )
    };

    const deleteUserMessage = {
        title: "Confirm Deletion",
        body: (
            <span>
                Are you sure you want to delete user <strong>{selectedUser?.username}</strong>?
            </span>
        ),
        footer: (
            <>
                <Button onClick={() => setUserDeleteModal(false)} className=" app-secondary-button-color border-0 w-25 no-hover-effect">No</Button>
                <Button  onClick={handleDeleteUserDataButton} className="w-25 delete-button-color border-0 no-hover-effect">
                    Delete
                </Button>
            </>
        )
    };

    const passwordChangeMessage = {
        title: "Reset Password",
        body: (
            <ResetPassword setPasswordChangeModal={setPasswordChangeModal} selectedUserId={selectedUserId} />
        ),
        footer: null
    };

    const userUpdateMessage = {
        title: "Update User Data",
        body: (
            <EditUserForm refreshUserData={handleUserData} setUpdateUserModal={setUpdateUserModal} selectedUserId={selectedUserId} />
        ),
        footer: null
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
                    {isLoading ? ( // Show the spinner while loading
                        <div className="d-flex justify-content-center align-items-center h-100">
                            <Spinner animation="border" variant="primary" />
                        </div>
                    ) : userDataRows?.length === 0 ? ( // If not loading and no data, show Empty
                        <div className="d-flex justify-content-center align-items-center h-100">
                            <h2 className="text-gray-600"><Empty description={"No User Data Found"} /></h2>
                        </div>
                    ) : ( // If data exists, show the DataGrid
                        <DataGrid
                            rows={userDataRows}
                            columns={columns}
                            paginationModel={paginationModel}
                            onPaginationModelChange={setPaginationModel}
                            pageSizeOptions={[25, 50, 75, 100]}
                             rowCount={totalUsersCount}
                            paginationMode='server'
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
                    )}
                </div>
            </div>
            {/* Active/Disable User Modal */}
            <ModalComponent
                id="admin-modify-user-data-modal"
                size="md"
                show={updateUserModal}
                handleClose={() => setUpdateUserModal(false)}
                modalContent={userUpdateMessage}
                modalCSSClass={"overflow-hidden;"}
            />

            {/* Active/Disable User Modal */}
            <ModalComponent
                id="admin-toggle-active-status-modal"
                size="md"
                show={userToggleActiveModal}
                handleClose={() => setUserToggleActiveModal(false)}
                modalContent={userToggleActiveMessage}
                modalCSSClass={"overflow-hidden;"}
                modalTitleCSSClass={{ color: selectedUser?.is_active ? '#910303' : '' }}
            />
            {/* Active/Disable User Modal */}
            <ModalComponent
                id="admin-password-reset-modal"
                size="md"
                show={passwordChangeModal}
                handleClose={() => setPasswordChangeModal(false)}
                modalContent={passwordChangeMessage}
                modalCSSClass={"overflow-hidden;"}
            />
            {/* Delete User Modal */}
            <ModalComponent
                id="admin-delete-user-modal"
                size="md"
                show={userDeleteModal}
                handleClose={() => setUserDeleteModal(false)}
                modalContent={deleteUserMessage}
                modalCSSClass={"overflow-hidden;"}
                modalTitleCSSClass={{ color: '#910303' }}
            />
        </>
    );
};

export default ViewUsersData;
