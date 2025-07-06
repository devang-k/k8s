
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: About.js  
 * Description: This file is responsible to displays versions of application 
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

import React, { useState, useEffect } from 'react';
import { Button } from 'react-bootstrap';
import { version, applicationTitle } from '../../constant';
import ModalComponent from '../utils/Modal/ModalComponent';
import { getVersionInfo } from '../../server/server';

const About = ({ showAboutModel, handleCloseModel }) => {
    const [versionInfo, setVersionInfo] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const currentYear = new Date().getFullYear(); // fetch current year to maintain it 


    useEffect(() => {
        if (showAboutModel) {
            fetchVersionInfo();
        }
    }, [showAboutModel]);

    const fetchVersionInfo = async () => {
        setLoading(true);
        setError("");
        try {
            const response = await getVersionInfo();
            setVersionInfo(response.data);
        } catch (err) {
            console.error("Failed to fetch version info:", err);
            setError("Failed to load version information.");
        } finally {
            setLoading(false);
        }
    };

    const modalContent = {
        title: 'SiVista',
        body: (
            <div>
                {loading ? (
                    <div className="text-center">
                        <div className="spinner-border text-primary" role="status">
                            <span className="visually-hidden">Loading...</span>
                        </div>
                    </div>
                ) : error ? (
                    <div className="alert alert-danger" role="alert">
                        {error}
                    </div>
                ) : versionInfo ? (
                    <div>
                        <div className="d-flex justify-content-center" style={{ marginBottom: '-16px' }}>
                            <h6>{applicationTitle}</h6>
                        </div>
                        <hr style={{ borderColor: 'white' }} />
                        <div className="d-flex justify-content-between align-items-center mb-2">
                            <span className="text-muted">Front-end version</span>
                            <span className="fw-bold">{version || 'N/A'}</span>
                        </div>

                        <div className="d-flex justify-content-between align-items-center mb-2">
                            <span className="text-muted">API Server version</span>
                            <span className="fw-bold">{versionInfo?.API_Server_Version || 'N/A'}</span>
                        </div>
                        <div className="d-flex justify-content-between align-items-center mb-2">
                            <span className="text-muted">GRPC Server version</span>
                            <span className="fw-bold">{versionInfo?.SiVista_core_version || 'N/A'}</span>
                        </div>
                        <div className="d-flex justify-content-between align-items-center mb-2">
                            <span className="text-muted">Lib Utils version</span>
                            <span className="fw-bold">{versionInfo?.Lib_utils_version || 'N/A'}</span>
                        </div>
                        <div className="text-center text-muted small ">
                            Copyright © {currentYear}
                           <p className='text-center fw-bold mt-1 mb-0'>Disclaimer:</p> 
                            <p className='text-start mb-0 '>
                             By using this software, you acknowledge and agree to the terms and conditions outlined in the accompanying documentation and/or end-user license agreement (EULA). All trademarks, service marks, and product names are the property of their respective owners.
                             </p>
                        </div>
                    </div>
                ) : null}
            </div>
        ),
        footer: (
            <div className="w-100 d-flex justify-content-center">
                <Button onClick={handleCloseModel} className="app-secondary-button-color border-0 w-50">
                    Close
                </Button>
            </div>
        ),
    };

    return (
        <ModalComponent
            id="about-modal"
            size="sm"
            show={showAboutModel}
            handleClose={handleCloseModel}
            modalContent={modalContent}
            bodyClassName="p-1"
            modalCSSClass="overflow-hidden"
        />
    );
};

export default About;

