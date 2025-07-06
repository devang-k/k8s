 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: toggleUserActiveStatus.js  
 * Description: This file is responsible to manage user active status at admin page 
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

import { toast } from "react-toastify";
import { updateUserDataStatus } from "../../AdminServer/AdminServer";  // Adjust path if needed

export const toggleUserActiveStatus = async (userId, newStatus, handleUserData, closeModal) => {
    try {
        const response = await updateUserDataStatus(userId, newStatus); // Pass newStatus to the backend
        if (response?.status === true) {
            closeModal();
            handleUserData(); // Refresh data after status change
            toast.success(response?.message, {autoClose: 10000});
        } else {
            toast.error(response?.message || "Failed to update user status.");
        }
    } catch (error) {
        console.error("Error updating user status:", error);
        toast.error("Failed to update user status. Please try again.");
    }
};
