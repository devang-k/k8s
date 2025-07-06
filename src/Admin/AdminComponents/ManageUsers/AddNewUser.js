 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: AddNewUser.js  
 * Description: This file is responsible to add new user at admin page 
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
import { Button, Form } from 'react-bootstrap';
import ModalComponent from '../../../components/utils/Modal/ModalComponent';
import { toast } from "react-toastify";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faEye, faEyeSlash } from '@fortawesome/free-solid-svg-icons';
import { createUserData } from '../../AdminServer/AdminServer';

const AddNewUser = ({ refreshUserData }) => {
    const [showModal, setShowModal] = useState(false);
    const [formData, setFormData] = useState({
        name: '',
        username: '',
        email: '',
        isAdmin: false,
        isActive: true,
        password: '',
        reConfirmPassword: ''
    });

    const [formErrors, setFormErrors] = useState({
        passwordMismatch: false,
        generalError: ''
    });

    // State for password visibility toggle
    const [passwordType, setPasswordType] = useState('password');
    const [reConfirmPasswordType, setReConfirmPasswordType] = useState('password');
    const [passwordIcon, setPasswordIcon] = useState(faEyeSlash);
    const [reConfirmPasswordIcon, setReConfirmPasswordIcon] = useState(faEyeSlash);

    // Handle input changes
    const handleChange = (e) => {
        const { name, value } = e?.target;
        setFormData((prevState) => ({
            ...prevState,
            [name]: name === 'isAdmin' ? value === 'true' : value
        }));

        if (name === 'reConfirmPassword') {
            setFormErrors((prevState) => ({
                ...prevState,
                passwordMismatch: value !== formData?.password
            }));
        }
    };

    // Reset the form
    const resetForm = () => {
        setFormData({
            name: '',
            username: '',
            email: '',
            isAdmin: false,
            isActive: true,
            password: '',
            reConfirmPassword: ''
        });
        setFormErrors({ passwordMismatch: false, generalError: '' });
    };

    // Form submission handler
    const handleSubmit = async (e) => {
        e.preventDefault();
        setFormErrors({ ...formErrors, generalError: '' });

        if (e?.target?.checkValidity()) {
            if (formData?.password !== formData?.reConfirmPassword) {
                setFormErrors({ ...formErrors, passwordMismatch: true });
                return;
            }

            try {
                const { reConfirmPassword, ...userData } = formData;
                const response = await createUserData(userData);

                if (response?.status === true) {
                    setShowModal(false);
                    resetForm();
                    toast.success(response?.message || "User created successfully!", {autoClose: 10000});
                    if (refreshUserData) {
                        refreshUserData(); // Refresh user data after adding a new user
                    }
                } else {
                    setFormErrors({ ...formErrors, generalError: response?.message || "Failed to create user." });
                }
            } catch (error) {
                console.error("Error creating user:", error);
                setFormErrors({ ...formErrors, generalError: "Failed to create user. Please try again." });
            }
        } else {
            setFormErrors({ ...formErrors, generalError: "Please fill out all required fields correctly." });
        }
    };

    // Toggle password visibility
    const handlePasswordToggle = () => {
        setPasswordType(prevType => (prevType === 'password' ? 'text' : 'password'));
        setPasswordIcon(prevIcon => (prevIcon === faEyeSlash ? faEye : faEyeSlash));
    };

    // Toggle re-confirm password visibility
    const handleReConfirmPasswordToggle = () => {
        setReConfirmPasswordType(prevType => (prevType === 'password' ? 'text' : 'password'));
        setReConfirmPasswordIcon(prevIcon => (prevIcon === faEyeSlash ? faEye : faEyeSlash));
    };

    const modalContent = {
        title: "Create New User",
        body: (
            <Form onSubmit={handleSubmit}>
                <div className="row">
                    <div className="col-md-6 mb-3">
                        <Form.Group>
                            <Form.Label>Name</Form.Label>
                            <Form.Control
                                id="new-user-name"
                                className='form-control shadow-none'
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
                                id="new-user-username"
                                className='form-control shadow-none'
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
                                id="new-user-email"
                                className='form-control shadow-none'
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
                                id="new-user-admin-access"
                                className='form-control shadow-none'
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
                </div>
                <div className="row">
                    <div className="col-md-6 mb-3">
                        <Form.Group>
                            <Form.Label>Password</Form.Label>
                            <div className="input-group">
                                <Form.Control
                                    id="new-user-password"
                                    className='form-control shadow-none'
                                    type={passwordType}
                                    name="password"
                                    placeholder="Enter password"
                                    value={formData?.password}
                                    onChange={handleChange}
                                    required
                                />
                                <Button variant="light" onClick={handlePasswordToggle}>
                                    <FontAwesomeIcon icon={passwordIcon} />
                                </Button>
                            </div>
                        </Form.Group>
                    </div>
                    <div className="col-md-6 mb-3">
                        <Form.Group>
                            <Form.Label>Re-confirm Password</Form.Label>
                            <div className="input-group">
                                <Form.Control
                                    id="new-user-reconfirm-password"
                                    className='form-control shadow-none'
                                    type={reConfirmPasswordType}
                                    name="reConfirmPassword"
                                    placeholder="Re-enter password"
                                    value={formData?.reConfirmPassword}
                                    onChange={handleChange}
                                    required
                                />
                                <Button className='shadow-none border-0' style={{ backgroundColor: "#ffffff", color: "#000000" }} onClick={handleReConfirmPasswordToggle}>
                                    <FontAwesomeIcon icon={reConfirmPasswordIcon} />
                                </Button>
                            </div>
                            {formErrors?.passwordMismatch && (
                                <Form.Text style={{ color: "#b22222" }}>
                                    Passwords do not match.
                                </Form.Text>
                            )}
                        </Form.Group>
                    </div>
                </div>
                <span id="error invalid-feedback fw-bold" style={{ fontSize: "12px", color: "#b22222" }}>
                    {formErrors?.generalError}
                </span>
                <div className="text-end mt-4">
                    <Button
                        id="cancel-button "
                        onClick={() => { setShowModal(false); resetForm(); }}
                        className="me-2 app-secondary-button-color border-0"
                    >
                        Cancel
                    </Button>
                    <Button id="submit-button" className="app-primary-button-color border-0" type="submit">
                        Add User
                    </Button>
                </div>
            </Form>
        ),
        footer: null
    };

    return (
        <>
            <div className="d-block justify-content-center align-items-center">
                <Button
                    id="add-new-user-button"
                    className="btn btn-md d-flex gap-2 align-items-center app-primary-button-color border-0"
                    onClick={() => setShowModal(true)}
                >
                    <FontAwesomeIcon icon={faPlus} style={{ fontSize: "18px" }} />
                    <span>Add New User</span>
                </Button>
            </div>

            {/* Modal for Add New User */}
            <ModalComponent
                id="add-new-user-modal"
                size="md"
                show={showModal}
                handleClose={() => { setShowModal(false); resetForm(); }}
                modalContent={modalContent}
            />
        </>
    );
};

export default AddNewUser;
