
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: AdminDashboard.js  
 * Description: This file handles admin dashboard layout structure 
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

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faUserGear, faPenRuler, faFileSignature } from "@fortawesome/free-solid-svg-icons";
import { useNavigate } from "react-router-dom";
import { Button } from "react-bootstrap";

const AdminDashboard = () => {
    const navigate = useNavigate();

    const handleNetlist = () => {
        navigate("/admin-settings/manage-admin-netlist");
    };
    const handleUsers = () => {
        navigate("/admin-settings/manage-users");
    };
    const handleTechFile = () => {
        navigate("/admin-settings/manage-admin-techfile")
    }

    return (
        <div className="d-flex align-items-center justify-content-center" id="background-img" style={{ height: '100%' }}>

            <div className="row text-center py-5 w-100">
                {/* Manage Admin User */}
                <div className="col-12 col-md-4 mb-3">
                    <Button
                        id="admin-user-btn"
                        style={{height:"23rem"}}
                        className="w-100 py-5 app-secondary-color text-dark border rounded-3 align-items-center cursor_pointer"
                        onClick={handleUsers}
                    >
                        <FontAwesomeIcon icon={faUserGear} className="fa-4x mb-3" />
                        <h3 className="text-lg font-semibold mb-1 text-decoration-underline" >Manage Users</h3>
                        <p className="text-gray-600 mb-0">Add and Manage</p>
                        <p>User</p>
                    </Button>
                </div>

                {/* Manage Netlist Files */}
                <div className="col-12 col-md-4 mb-3">
                    <Button
                        id="admin-netlist-btn"
                        style={{height:"23rem"}}
                        className="w-100 py-5 app-secondary-color text-dark border rounded-3 align-items-center cursor_pointer"
                        onClick={handleNetlist}
                    >
                        <FontAwesomeIcon icon={faFileSignature} className="fa-4x mb-3" />
                        <h3 className="text-lg font-semibold mb-1 text-decoration-underline">Manage Netlist Files</h3>
                        <p className="text-gray-600 mb-0">View and Manage</p>
                        <p>Netlist Files</p>
                    </Button>
                </div>

                {/* Manage Tech Files */}
                <div className="col-12 col-md-4 mb-3">
                    <Button
                        id="admin-techfile-btn"
                        style={{height:"23rem"}}
                        className="w-100 py-5 app-secondary-color text-dark border rounded-3 align-items-center cursor_pointer"
                        onClick={handleTechFile}
                    >
                        <FontAwesomeIcon icon={faPenRuler} className="fa-4x mb-3" />
                        <h3 className="text-lg font-semibold mb-1 text-decoration-underline">Manage Tech Files</h3>
                        <p className="text-gray-600 mb-0">View and Manage</p>
                        <p>Tech Files</p>
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default AdminDashboard;
