 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: AdminSettings.js  
 * Description: This file is shows admin dashboard page 
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

import React, { useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import NavBar from '../components/navbar/navbar'
import Footer from '../components/Footer/Footer'
import { useResetContextData } from "../Hooks/ResetContextHook"

function AdminSettings() {
    const resetContext = useResetContextData();

    // below function refresh all the context data
    useEffect(() => {
        resetContext();
    }, [resetContext])

    return (
        <>
            <NavBar />
            <div
                id="dashboard-container"
                className='container-fluid p-0 m-0 border-0'
                style={{ maxHeight: "100%", overflow: "hidden" }}>
                <Outlet />
            </div>
            <Footer />
        </>
    )
}

export default AdminSettings