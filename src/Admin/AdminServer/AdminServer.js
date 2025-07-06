
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: AdminServer.js  
 * Description: This file handles all backend API calls related to admin level for the project and interactions with external services. 
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

// all admin related api call is handled here
import axiosInstance from "../../server/axiosInterceptor"
import { pageNumber, userPageSize } from "../../constant";

// below function will fetch the list of user netlist file
export const getAdminListData = async ( getAdminListReq) => {
  try {
    const fetchAdminNetlistDataRes = await axiosInstance.post("administrator/getlist/", getAdminListReq)
    return fetchAdminNetlistDataRes?.data;
  }
  catch (error) {
    console.error("Error while fetching the netlist project", error);
    return error?.response?.data;
  }
}

// below function delete the netlist file and techfile from list
export const deleteAdminFile = async (deleteAdminFileReq) => {
  try {
    const userNetlistFileDeleteRes = await axiosInstance.delete("administrator/delete/file/", { data: deleteAdminFileReq } )
    return userNetlistFileDeleteRes?.data
  }
  catch (error) {
    console.error("Error while deleting the netlist file");
    return error?.response?.data;
  }
}

// below function will upload the netlist file
export const uploadUserNetlistFile = async (uploadNetlistFileReq) => {
  try {
    const getUserNetlistFileUpload = await axiosInstance.post(
      "administrator/netlist/upload/",
      uploadNetlistFileReq,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return getUserNetlistFileUpload?.data;
  } catch (error) {
    console.error("Error while uploading the netlist file");
    return error?.response?.data;
  }
};

// below function will modify user netlist file and tech file
export const modifyUserFileData = async (modifyUserFileDataReq) => {
  try {
    const modifyUserFileDataRes = axiosInstance.put("administrator/modify/file/",modifyUserFileDataReq)
    return modifyUserFileDataRes;
  }
  catch (error) {
    console.error("Error while editing the netlist file")
    return error?.response?.data;
  }
}

// below function will fetch the list of user tech file
export const uploadUserTechFile = async (uploadTechFileReq) => {
    try {
        const getUserTechFileUpload = await axiosInstance.post(
            "administrator/tech/upload/",
            uploadTechFileReq,
            {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            }
        );
        return getUserTechFileUpload?.data;
    } catch (error) {
        console.error("Error while uploading the tech file");
        return error?.response?.data;
    }
}


// below function will fetch the list of user data
export const getUserData = async (userDataListReq) => {
  try {
      const fetchUserDataRes = await axiosInstance.post("/profile/list/", userDataListReq || {page: pageNumber, pageSize:userPageSize})
      return fetchUserDataRes?.data;
  }
  catch (error) {
      console.error("Error while fetching the user data project", error);
      return error?.data;
  }
}

/**
* Updates the active status Enable and Disable user.
* Sends a PATCH request to update the user's active status (true or false) in the backend.
*/
export const updateUserDataStatus = async (userId, newStatus) => {
  try {
      // Send a PATCH request with the new status (true or false)
      const response = await axiosInstance.patch(`/profile/modify/${userId}/`, { isActive: newStatus });
      return response?.data;
  } catch (error) {
      console.error("Error while updating the user data:", error);
      return error?.response?.data || error?.message;
  }
};

/**
* Updates a user's data.
* Sends a PATCH request to update the user's data in the backend.
*/
export const updateUserData = async (userId, updatedUserData) => {
try {
    const response = await axiosInstance.patch(`/profile/modify/${userId}/`, updatedUserData);
    return response?.data;
} catch (error) {
    console.error("Error while updating the user data:", error);
    return error?.response?.data || error?.message;
}
};

/**
* Resets a user's password.
* Sends a PATCH request to reset the user's password in the backend.
*/
export const resetUserPassword = async (userId, passwordData) => {
  try {
      const response = await axiosInstance.patch(`/profile/modify/${userId}/`, passwordData);
      return response?.data;
  } catch (error) {
      console.error("Error while updating the user data:", error);
      return error?.response?.data || error?.message;
  }
  };

  
/**
* Retrieves a user's data.
* Sends a PATCH request to obtain the user's data from the backend.
*/
export const retriveUserData = async (userId) => {
try {
    const response = await axiosInstance.patch(`/profile/modify/${userId}/`);
    return response?.data;
} catch (error) {
    console.error("Error while updating the user data:", error);
    return error?.response?.data || error?.message;
}
};

/**
* Sends a POST request to create a new user in the backend.
*/
export const createUserData = async (newUserData) => {
try {
    const response = await axiosInstance.post(`/profile/create/`, newUserData);
    return response?.data;
} catch (error) {
    console.error("Error while updating the user data:", error);
    return error?.response?.data || error?.message;
}
};

/**
* Sends a PATCH request to delete a user from the backend.
*/
export const deleteUserData = async (userId, deleteUserReq) => {
try {
    // Send a PATCH request with the new status (true or false)
    const response = await axiosInstance.patch(`/profile/modify/${userId}/`, { isDeleted: deleteUserReq });
    return response?.data;
} catch (error) {
    console.error("Error while updating the user data:", error);
    return error?.response?.data || error?.message;
}
};

export const getUserFileData = async (userFileDataReq) => {
  try {
    const getUserFileDataRes = axiosInstance.post("administrator/getdata/",userFileDataReq);
    return getUserFileDataRes;
  }
  catch (error) {
    console.error("Error While getting user file data", error)
    return error?.response?.data;
  }
}

// below function will rename netlist file and tech file
export const renameUserFile = async (renameUserFileReq) => {
  try {
    const renameUserFileRes = await axiosInstance.post("administrator/rename/file/", renameUserFileReq);
    return renameUserFileRes?.data;
  }
  catch (error) {
    console.error("Error while renaming the file", error);
    return error?.response?.data;
  }
}

// below function will clone netlist file and tech file
export const cloneUserFile = async (cloneUserFileReq) => {
  try {
    const cloneUserRes = await axiosInstance.post("/administrator/clone/file/", cloneUserFileReq);
    return cloneUserRes?.data;
  } catch (error) {
    console.error("Error while cloning the file", error);
    return error?.response?.data;
  }
};