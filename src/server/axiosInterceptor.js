 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: axiosInterceptor.js  
 * Description: This file configures and sets up Axios interceptors to handle request and response transformations globally. 
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

import axios from 'axios'
import {hostName} from '../constant';

const axiosInstance = axios.create({
  baseURL: `${hostName}`, //replace with your BaseURL
  headers: {
    'Content-Type': 'application/json', // change according header type accordingly
  },
});

  axiosInstance.interceptors.request.use(
  (config) => {
  
    const accessToken = localStorage.getItem('access-token'); // get stored access token
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`; // set in header
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

axiosInstance.interceptors.response.use(
  
  (response) => {
    return response;
  },
  async (error) => {

    const originalRequest = error.config;

    if (error.response.status === 401) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh-token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${hostName}/token/refresh/`, {"refresh":refreshToken});
          // don't use axious instance that already configured for refresh token api call
    
          const newAccessToken = response.data.access;
          localStorage.setItem('access-token', newAccessToken);  //set new access token
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return axios(originalRequest); //recall Api with new token
        } catch (error) {
          // Handle token refresh failure
          // mostly logout the user and re-authenticate by login again
          localStorage.removeItem('access-token');
          localStorage.removeItem('refresh-token');
          window.location.href = '/';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default axiosInstance