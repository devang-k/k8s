
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: EditUserForm.js  
 * Description: This file is responsible to edit user at admin page 
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

import React, { useState, useEffect, useCallback } from 'react';
import { Form, Button } from 'react-bootstrap';
import { toast } from 'react-toastify';
import { updateUserData, retriveUserData } from '../../AdminServer/AdminServer';
import { useManageUserContext } from '../../../components/providers/ManageUserProvider/ManageUserContext';

const EditUserForm = ({ refreshUserData, setUpdateUserModal, selectedUserId }) => {
    const { loggingLevelOptions } = useManageUserContext();
    const [formData, setFormData] = useState({
        name: '',
        username: '',
        email: '',
        isAdmin: false,
        isActive: false,
        logLevel: 0,
    });
    const [changedFields, setChangedFields] = useState({}); // Track changed fields

    // Reset the form
    const resetForm = () => {
        setFormData({
            name: '',
            username: '',
            email: '',
            isAdmin: false,
            isActive: true,
        });
        setChangedFields({}); // Reset changed fields
    };

    const [formErrors, setFormErrors] = useState({
        generalError: ''
    });

    const handleRetriveUserData = useCallback(async () => {
        try {
            const getRetriveUserDataRes = await retriveUserData(selectedUserId);
            if (getRetriveUserDataRes?.status === true && getRetriveUserDataRes?.data) {
                const userData = getRetriveUserDataRes?.data;

                setFormData({
                    name: userData?.name || '',
                    username: userData?.username || '',
                    email: userData?.email || '',
                    isAdmin: userData?.is_staff || false,
                    isActive: userData?.is_active || false,
                    logLevel: userData?.log_level || 0
                });
                setChangedFields({}); // Reset changed fields on data fetch
            } else {
                resetForm();
                toast.error(getRetriveUserDataRes?.message);
            }
        } catch (error) {
            console.error('Error Fetching user data:', error);
            toast.error("Error fetching data. Please try again.");
        }
    }, [selectedUserId]);

    useEffect(() => {
        handleRetriveUserData();
    }, [handleRetriveUserData]);


    const handleChange = (e) => {
        const { name, value } = e?.target;

        // Update form data
        let newValue;
        if (name === 'isAdmin' || name === 'isActive') {
            newValue = value === 'true';
        } else if (name === 'logLevel') {
            newValue = parseInt(value);
        } else {
            newValue = value;
        }
        setFormData((prev) => ({
            ...prev,
            [name]: newValue,
        }));

        // Track changes only if the value differs from the initial value
        setChangedFields((prev) => {
            if (formData[name] !== newValue) {
                return { ...prev, [name]: newValue };
            } else {
                const updated = { ...prev };
                delete updated[name]; // Remove field if it matches initial value
                return updated;
            }
        });
    };

    const handleSubmit = async (e) => {
        e?.preventDefault();

        try {
            //closing modal if any value is not changed
            if (Object?.keys(changedFields)?.length === 0) {
                setUpdateUserModal(false);
                resetForm();
                toast.success('User data is already up to date.', { autoClose: 10000 });
                return;
            }

            const response = await updateUserData(selectedUserId, changedFields);
            if (response?.status === true) {
                if (refreshUserData) {
                    refreshUserData();
                }
                setUpdateUserModal(false);
                resetForm();
                toast.success(response?.message || 'User updated successfully!', { autoClose: 10000 });
            } else {
                setFormErrors({ ...formErrors, generalError: response?.message || "Failed to update user." });
            }
        } catch (error) {
            console.error('Error updating user:', error);
            toast.error('Failed to update user. Please try again.');
        }
    };

    return (
        <Form onSubmit={handleSubmit}>
            <div className="row">
                <div className="col-md-6 mb-3">
                    <Form.Group>
                        <Form.Label>Name</Form.Label>
                        <Form.Control
                            id="update-user-name"
                            className="form-control shadow-none"
                            type="text"
                            name="name"
                            autoFocus
                            placeholder="Enter name"
                            value={formData?.name}
                            onChange={handleChange}
                            required
                        />
                    </Form.Group>
                </div>
                <div className="col-md-6 mb-3">
                    <Form.Group>
                        <Form.Label>Username</Form.Label>
                        <Form.Control
                            id="update-user-username"
                            className="form-control shadow-none"
                            type="text"
                            name="username"
                            placeholder="Enter username"
                            value={formData?.username}
                            onChange={handleChange}
                            required
                        />
                    </Form.Group>
                </div>
            </div>
            <div className="row">
                <div className="col-md-6 mb-3">
                    <Form.Group>
                        <Form.Label>Email</Form.Label>
                        <Form.Control
                            id="update-user-email"
                            className="form-control shadow-none"
                            type="email"
                            name="email"
                            placeholder="Enter email"
                            value={formData?.email}
                            onChange={handleChange}
                            required
                        />
                    </Form.Group>
                </div>
                <div className="col-md-6 mb-3">
                    <Form.Group>
                        <Form.Label>Admin Access</Form.Label>
                        <Form.Select
                            id="update-user-is-admin"
                            className="form-select shadow-none"
                            name="isAdmin"
                            value={formData?.isAdmin.toString()}
                            onChange={handleChange}
                            required
                        >
                            <option value="false">No</option>
                            <option value="true">Yes</option>
                        </Form.Select>
                    </Form.Group>
                </div>
                <div className="col-md-6 mb-3">
                    <Form.Group>
                        <Form.Label>Is Active</Form.Label>
                        <Form.Select
                            id="update-user-is-active"
                            name="isActive"
                            className="form-select shadow-none"
                            value={formData?.isActive.toString()}
                            onChange={handleChange}
                            required
                        >
                            <option value="false">No</option>
                            <option value="true">Yes</option>
                        </Form.Select>
                    </Form.Group>
                </div>
                <div className="col-md-6 mb-3">
                    <Form.Group>
                        <Form.Label>Logging Level</Form.Label>
                        <Form.Select
                            id="update-user-log-level"
                            name="logLevel"
                            className="form-select shadow-none"
                            value={formData?.logLevel}
                            onChange={handleChange}
                            required
                        >
                            {loggingLevelOptions?.map((option) => (
                                <option key={option?.key} value={option?.key}>
                                    {option?.value}
                                </option>
                            ))}
                        </Form.Select>
                    </Form.Group>
                </div>
            </div>
            <span id="error invalid-feedback fw-bold" style={{ fontSize: "12px", color: "#b22222" }}>
                {formErrors?.generalError}
            </span>
            <div className="d-flex justify-content-end mt-4">
                <Button
                    id="update-user-cancel-button"
                    onClick={() => {
                        setUpdateUserModal(false);
                        resetForm();
                    }}
                    className="me-3 app-secondary-button-color border-0"
                >
                    Cancel
                </Button>
                <Button
                    className='app-primary-button-color border-0'
                    id="update-user-submit-button"
                    type="submit"
                >
                    Update User Data
                </Button>
            </div>
        </Form>
    );
};

export default EditUserForm;
