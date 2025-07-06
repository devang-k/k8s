
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: Profile.js  
 * Description: This file is responsible to manage user's profile information. 
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

import React, { useEffect, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faUser } from "@fortawesome/free-solid-svg-icons";
import { getDetailsOfUser } from "../../server/server";
import { useResetContextData } from "../../Hooks/ResetContextHook";
import ModalComponent from "../utils/Modal/ModalComponent";
import Button from "react-bootstrap/Button";
import { faEye, faEyeSlash, faUnlock } from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from "react-router-dom";
import { changeUserPassword } from "../../server/server";
import { Tooltip as ReactTooltip } from 'react-tooltip'
import { Form } from 'react-bootstrap';
import Footer from "../Footer/Footer";


const ProfilePage = () => {
    const navigate = useNavigate();
    const resetContext = useResetContextData();
    const [userDetails, setUserDetails] = useState(null);
    const [loading, setLoading] = useState(true);
    const [changePasswordModal, setChangePasswordModal] = useState(false);
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [oldPasswordType, setOldPasswordType] = useState('password');
    const [newPasswordType, setNewPasswordType] = useState('password');
    const [confirmPasswordType, setConfirmPasswordType] = useState('password');
    const [formErrors, setFormErrors] = useState({
        passwordMismatch: false,
        passwordLengthError: false,
        generalError: '',
    });

    useEffect(() => {
        const fetchUserDetails = async () => {
            try {
                const details = await getDetailsOfUser();
                setUserDetails(details);
            } catch (err) {
                console.error(err?.message);
            } finally {
                setLoading(false);
            }
        };
        fetchUserDetails();
    }, []);

    const { username, name, email, is_admin, is_active, log_level } = userDetails?.data || {};

    // below function refresh all the context data
    useEffect(() => {
        resetContext();
    }, [resetContext]);

    const handlePasswordToggle = (field) => {
        if (field === 'old') {
            setOldPasswordType((prev) => prev === 'password' ? 'text' : 'password');
        } else if (field === 'new') {
            setNewPasswordType((prev) => prev === 'password' ? 'text' : 'password');
        } else {
            setConfirmPasswordType((prev) => prev === 'password' ? 'text' : 'password');
        }
    };

    // Reset the form
    const resetForm = () => {
        setOldPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setFormErrors({ passwordMismatch: false, generalError: '' });
    };

    // Form submission handler
    const handleSubmit = async (e) => {
        e.preventDefault();
        setFormErrors({ ...formErrors, generalError: '' });

        if (e.target.checkValidity()) {
            if (newPassword !== confirmPassword) {
                setFormErrors({ ...formErrors, passwordMismatch: true });
                return;
            }

            try {
                const response = await changeUserPassword(oldPassword, newPassword);

                if (response?.status) {
                    setChangePasswordModal(false);

                    localStorage.clear();
                    navigate('/');
                } else {
                    setFormErrors({ generalError: response?.message });
                }
            } catch (error) {
                console.error("Error updating password:", error);

            }
        } else {
            setFormErrors({ ...formErrors, generalError: "Please fill out all required fields correctly." });
        }
    };

    const changePasswordModalContent = {
        title: "Reset Password",
        body: (
            <Form onSubmit={handleSubmit}>
                <div className="mb-2">
                    <div className="col-md-12 mb-3">
                        <Form.Group>
                            <Form.Label>Old Password</Form.Label>
                            <div className="input-group">
                                <Form.Control
                                    id="user-old-password"
                                    className='form-control shadow-none'
                                    type={oldPasswordType}
                                    placeholder="Enter password"
                                    value={oldPassword}
                                    onChange={(e) => setOldPassword(e.target.value)}
                                    required
                                />
                                <Button variant="light" onClick={() => handlePasswordToggle('old')}>
                                    <FontAwesomeIcon icon={oldPasswordType === 'password' ? faEyeSlash : faEye} />
                                </Button>
                            </div>
                        </Form.Group>
                    </div>
                </div>
                <div className="row">
                    <div className="col-md-6 mb-3">
                        <Form.Group>
                            <Form.Label>New Password</Form.Label>
                            <div className="input-group">
                                <Form.Control
                                    id="user-new-password"
                                    className='form-control shadow-none'
                                    type={newPasswordType}
                                    placeholder="Enter password"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    required
                                />
                                <Button variant="light" onClick={() => handlePasswordToggle('new')}>
                                    <FontAwesomeIcon icon={newPasswordType === 'password' ? faEyeSlash : faEye} />
                                </Button>
                            </div>
                        </Form.Group>
                    </div>
                    <div className="col-md-6 mb-3">
                        <Form.Group>
                            <Form.Label>Confirm New Password</Form.Label>
                            <div className="input-group">
                                <Form.Control
                                    id="user-confirm-new-password"
                                    className='form-control shadow-none'
                                    type={confirmPasswordType}
                                    placeholder="Re-enter password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    required
                                />
                                <Button className='shadow-none border-0' style={{ backgroundColor: "#ffffff", color: "#000000" }} onClick={() => handlePasswordToggle('confirm')}>
                                    <FontAwesomeIcon icon={confirmPasswordType === 'password' ? faEyeSlash : faEye} />
                                </Button>
                            </div>
                            {formErrors.passwordMismatch && (
                                <Form.Text style={{ color: "#b22222" }}>
                                    Passwords do not match.
                                </Form.Text>
                            )}
                        </Form.Group>
                    </div>
                </div>
                <span id="error invalid-feedback fw-bold" style={{ fontSize: "12px", color: "#b22222" }}>
                    {formErrors.generalError}
                </span>
                <div className="d-flex justify-content-end mt-4">
                    <Button
                        onClick={() => {
                            resetForm();
                            setChangePasswordModal(false);
                        }}
                        className="me-3 app-secondary-button-color border-0"
                    >
                        Cancel
                    </Button>
                    <Button
                        type="submit"
                        className="app-primary-button-color border-0"
                        disabled={!oldPassword || !newPassword || !confirmPassword || newPassword !== confirmPassword}
                    >
                        Save Password
                    </Button>
                </div>
            </Form>
        ),
        footer: null
    };

    return (
        <>
            {loading ? ( // If data is still fetching
                <div
                    className="d-flex justify-content-center align-items-center"
                    style={{ height: "100vh", backgroundColor: "#f8f9fa" }}
                >
                    <div className="spinner-border text-primary" role="status">
                        <span className="sr-only">Loading...</span>
                    </div>
                </div>
            ) : (
                <div className="container-fluid py-5" id="background-img">
                    <div className="row justify-content-center">
                        <div className="col-md-10 col-lg-8">
                            <div className="card shadow">
                                <div className="row g-0">
                                    <div
                                        className="col-md-4 d-flex flex-column align-items-center justify-content-center app-primary-button-color"
                                        style={{
                                            padding: "45px",
                                        }}
                                    >
                                        <FontAwesomeIcon
                                            id="profile-icon"
                                            icon={faUser}
                                                className="fa-4x p-3 text-white fa-8x"
                                        />
                                        <h5 className="text-white">{username}</h5>
                                        {/* Show "Admin" label if the user is an admin */}
                                        {is_admin && <p className="text-white">Admin</p>}
                                    </div>
                                    <div className="col-md-8">
                                        <div className="card-body ">
                                            <div className="mb-4 mt-1">
                                                <div className="d-flex justify-content-between">
                                                <h4 className="border-bottom pb-2">User Profile</h4>
                                               
                                                <FontAwesomeIcon className="m-2 text-dark" icon={faUnlock}    
                                                data-tooltip-id="change-password-button-tooltip"
                                                  data-tooltip-content={"Change Password"}
                                                   onClick={() => setChangePasswordModal(true)}/>
                                                <ReactTooltip id="change-password-button-tooltip" place="top" style={{ width: "160px", zIndex: 9999, display:"flex", justifyContent:"center" }} />
                                        </div>
                                                <div className="row">
                                                    <div className="col-md-6">
                                                        <h6 className="text-muted">Name</h6>
                                                        <p id="profile-name">{name || "N/A"}</p>
                                                    </div>
                                                    <div className="col-md-6">
                                                        <h6 className="text-muted">Email</h6>
                                                        <p id="profile-email">{email || "N/A"}</p>
                                                    </div>
                                                    <div className="col-md-6">
                                                        <h6 className="text-muted">Is Admin</h6>
                                                        <p id="profile-isadmin">{is_admin ? "Yes" : "No"}</p>
                                                    </div>
                                                    <div className="col-md-6">
                                                        <h6 className="text-muted">Is Active</h6>
                                                        <p id="profile-isactive">{is_active ? "Yes" : "No"}</p>
                                                    </div>
                                                        <div className="col-md-6 flex-grow-1">
                                                            <h6 className="text-muted">Logging Level</h6>
                                                            {/* nullish coalescing operator : it specifically handles null and undefined while preserving other falsy values like 0 */}
                                                            <p id="profile-logging-level">{log_level ?? "N/A"}</p> 
                                                        </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
            <Footer/>
            <ModalComponent
                id="project-running-modal"
                size="md"
                show={changePasswordModal}
                handleClose={() => setChangePasswordModal(false)}
                modalContent={changePasswordModalContent}
                modalCSSClass={"overflow-hidden"}
            />
        </>
    );
};

export default ProfilePage;
