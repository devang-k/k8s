 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: ResetPassword.js  
 * Description: This file is responsible to reset user password at admin page 
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

import React, { useState} from 'react';
import { Form, Button } from 'react-bootstrap';
import { toast } from 'react-toastify';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEye, faEyeSlash } from '@fortawesome/free-solid-svg-icons';
import { resetUserPassword } from '../../AdminServer/AdminServer';

const ResetPassword = ({ setPasswordChangeModal, selectedUserId }) => {
    const [formData, setFormData] = useState({
        password: '',
    });
    // State for password visibility toggle
    const [passwordType, setPasswordType] = useState('password');
    const [reConfirmPasswordType, setReConfirmPasswordType] = useState('password');
    const [passwordIcon, setPasswordIcon] = useState(faEyeSlash);
    const [reConfirmPasswordIcon, setReConfirmPasswordIcon] = useState(faEyeSlash);

    const [formErrors, setFormErrors] = useState({
        passwordMismatch: false,
        generalError: ''
    });
    // Reset the form
    const resetForm = () => {
        setFormData({
            password: '',
        });
        setFormErrors({ passwordMismatch: false, generalError: '' });
    };

    // Handle password change
    const handleChange = (e) => {
        const { name, value } = e?.target;
        setFormData({
            ...formData,
            [name]: value,
        });
        if (name === 'reConfirmPassword') {
            setFormErrors((prevState) => ({
                ...prevState,
                passwordMismatch: value !== formData?.password
            }));
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
                const response = await resetUserPassword(selectedUserId, userData);

                if (response?.status) {
                    setPasswordChangeModal(false);
                    resetForm();
                    toast.success(response?.message || 'Password updated successfully!', { autoClose: 10000 });
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

    return (
        <Form onSubmit={handleSubmit}>
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
            <div className="d-flex justify-content-end mt-4">
                <Button
                    id="update-user-cancel-button app-secondary-button-color border-0"
                    onClick={() => {
                        setPasswordChangeModal(false);
                        resetForm(); // resetForm
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
                    Update Password
                </Button>
            </div>
        </Form>
    );
};

export default ResetPassword;
