 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: ManageUsers.js  
 * Description: This file is responsible to manage user at admin page 
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

import React, { useCallback, useState } from 'react';
import ViewUsersData from "./ViewUsersData";
import AddNewUser from "./AddNewUser";
import { ToastContainer, toast } from "react-toastify";
import { getUserData } from '../../AdminServer/AdminServer';
import { useManageUserContext } from '../../../components/providers/ManageUserProvider/ManageUserContext';

const ManageUsers = () => {
  const { userData, setUserData ,setLoggingLevelOptions , totalUsersCount,setTotalUsersCount } = useManageUserContext();
  const [isLoading, setIsLoading] = useState(false);

  const handleUserData = useCallback(async (userPage,userPageSize) => {
    setIsLoading(true);
    try {
      const userDataListReq = {
        page: userPage || 0, 
        pageSize: userPageSize || totalUsersCount
      };
      const getUserDataRes = await getUserData(userDataListReq);
      if (getUserDataRes?.status === true && getUserDataRes?.data?.Items?.length > 0) {
        setUserData(getUserDataRes?.data?.Items);
        setTotalUsersCount(getUserDataRes?.data?.TotalItems);
        setLoggingLevelOptions(getUserDataRes?.data?.logLevels || []);
      } else {
        setUserData([]);
        setLoggingLevelOptions([]);
        toast.error("No user found");
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error("Error fetching data. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }, [setUserData, setLoggingLevelOptions,setTotalUsersCount,totalUsersCount]);


  return (
    <>
      <ToastContainer
        closeButton={true}
        position="top-center"
        autoClose={false}
        closeOnClick
        theme="colored"
      />
      <div className="container-fluid m-0 p-0 h-100" style={{ maxHeight: "100%", overflow: "hidden" }}>
        <div className="d-flex flex-column align-items-center justify-content-center m-4" >
          <h5>Manage Users</h5>
          <p>Add and Manage Users</p>
          <div className="d-flex justify-content-end w-100">
            <AddNewUser refreshUserData={handleUserData} />
          </div>
        </div>
        <ViewUsersData userData={userData} isLoading={isLoading} handleUserData={handleUserData} />
      </div>
    </>
  );
};

export default ManageUsers;
