 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: DeleteUser.js  
 * Description: This file is responsible to delete user at admin page 
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
import { deleteUserData } from "../../AdminServer/AdminServer";  // Adjust path if needed

export const deleteUser = async (userId, handleUserData, closeModal) => {
    try {
        // Passing true to delete the user 
        const response = await deleteUserData(userId, true); // Pass newStatus to the backend
        if (response?.status === true) {
            closeModal();
            handleUserData(); // Refresh data after status change
            toast.success(response?.message, {autoClose: 10000});
        } else {
            toast.error(response?.message || "Failed to delete user.");
        }
    } catch (error) {
        console.error("Error deleteing user:", error);
        toast.error("Failed to delete user. Please try again.");
    }
};
