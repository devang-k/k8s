
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: LoginPage.js  
 * Description: This file is responsible to login the users 
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
import { useNavigate } from "react-router-dom";
import axiosInstance from "../../server/axiosInterceptor";
import "./LoginPage.css";
import Logo from "../../Assets/Images/Logo.svg";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faEye, faEyeSlash, faCircleInfo } from "@fortawesome/free-solid-svg-icons";
import Button from "react-bootstrap/Button";
import { useEffect } from "react";
import About from "../About/About";

const LoginPage = () => {
  const navigate = useNavigate();
  const [data, setData] = useState({ Username: "", Password: "" });
  const [isLoading, setIsLoading] = useState(false);
  const [passwordType, setPasswordType] = useState("password");
  const [passwordIcon, setPasswordIcon] = useState(faEyeSlash);
  const [error, setError] = useState("");
  const [viewAboutModal, setViewAboutModal] = useState(false);

  useEffect(() => {
    //this useeffect will run and check if user has accesstoken already then user won't be going back to login page instead it will always be on home page  
    const accessToken = localStorage.getItem('access-token');
    accessToken && navigate('/home')

  }, [navigate]);

  const handleToggle = () => {
    setPasswordType((prevType) =>
      prevType === "password" ? "text" : "password"
    );
    setPasswordIcon((prevIcon) =>
      prevIcon === faEyeSlash ? faEye : faEyeSlash
    );
  };

  const handleChange = ({ target: { id, value } }) => {
    setData((prevData) => ({ ...prevData, [id]: value }));
    setError(""); // Clear error on input change
  };

  const validateForm = () => {
    if (!data.Username.trim()) {
      setError("Username is required");
      return false;
    }

    if (!data.Password) {
      setError("Password is required");
      return false;
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsLoading(true);
    setError(""); // Clear error before submission

    try {
      const response = await axiosInstance.post("user/login/", data);
      if (response?.data?.status === 200) {

        localStorage.setItem("isAdmin", response?.data?.token?.isAdmin)
        localStorage.setItem("access-token", response?.data?.token?.access);
        localStorage.setItem("refresh-token", response?.data?.token?.refresh);
        localStorage.setItem("username", data?.Username); // Storing username in localStorage

        setData({ Username: "", Password: "" });

        navigate("home");
      } else {
        setError(response?.data?.message || "Login failed.");
      }
    } catch (err) {
      console.error(err?.response?.data?.message || "An error occurred");
      setError(
        err?.response?.data?.message || "An error occurred. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleShowAboutModal = () => {
    setViewAboutModal(true);
  };


  const handleCloseAboutModal = () => {
    setViewAboutModal(false);
  };

  return (
    <div
      id="login-page"
      className="container-fluid vh-100 d-flex justify-content-center align-items-center bg-light p-0 m-0"
    >
      <div className="col-12 row">
        <div className="col-12 col-md-4 app-primary-button-color m-auto login-container p-5">
          <div className="text-center">
            <img src={Logo} alt="logo" className="img-fluid mb-3" />
          </div>
          <form onSubmit={handleSubmit} className="rounded">
            <div className="mb-3">
              <label htmlFor="Username" className="form-label text-white">
                Username
              </label>
              <input
                type="text"
                className="form-control shadow-none p-2 m-0 border-0 col-10 bg-light text-dark"
                id="Username"
                placeholder="Enter your username"
                value={data.Username}
                onChange={handleChange}
                required
                maxLength={10}
                disabled={isLoading}
              />
            </div>
            <div className="mb-3">
              <label htmlFor="Password" className="form-label text-white">
                Password
              </label>
              <div className="input-group row m-0 p-0">
                <input
                  type={passwordType}
                  className="form-control shadow-none p-2 m-0 border-0 col-10 bg-light text-dark"
                  id="Password"
                  placeholder="Enter your password"
                  value={data.Password}
                  onChange={handleChange}
                  required
                  maxLength={30}
                  disabled={isLoading}
                />
                <button
                  type="button"
                  className="border-start-0 btn btn-light m-0 px-2 col-2 p-0"
                  id="user-password-visiblity-button"
                  onClick={handleToggle}
                  aria-label="Toggle password visibility"
                >
                  <FontAwesomeIcon icon={passwordIcon} />
                </button>
              </div>
            </div>
            <div className="error-text error-message-container mb-2">
              {error && (
                <div className="d-block text-left fw-bold mb-3">
                  {error}
                </div>
              )}
            </div>
            <div className="d-grid">
              <Button
                type="submit"
                id="user-login-button"
                size="lg"
                disabled={isLoading}
                className="shadow-none login-button border-0"
              >
                {isLoading ? "Signing in…" : "Login"}
              </Button>
            </div>
          </form>
          <div className="d-flex justify-content-end align-items-center" style={{ width: '100%' }}>
            {/* About section will open the modal */}
            <FontAwesomeIcon
              icon={faCircleInfo}
              style={{ fontSize: '20px', top:"1.5rem" , left:"1.7rem" }}
              className="text-white position-relative cursor_pointer"
              onClick={handleShowAboutModal}
            />
          </div>
        </div>
      </div>
      {/* Pass modal state and close handler to About component */}
      <About showAboutModel={viewAboutModal} handleCloseModel={handleCloseAboutModal} />
    </div>
  );
};

export default LoginPage;
