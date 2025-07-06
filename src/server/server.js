
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: server.js  
 * Description: This file handles all backend API calls for the project and interactions with external services. 
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

// all the api call of project will go here
import axiosInstance from "./axiosInterceptor"
import { pageSize } from '../constant';
import axios from "axios";
import { hostName } from '../constant';


export const blackListTokenApi = async (refreshToken) => {
    try {
        await axiosInstance.post('/user/logout/', { "refresh": refreshToken });
    }
    catch (error) {
        console.error("blacklisting of api failed", error)
    }

}

// below api is for getting techlist file data

/*typeof getTechFileDataReqBody = 
{
        "FileName": string,
        "FileType": string,
    }
 */
export const getTechFileData = async (getTechFileDataReqBody) => {
    try {
        const getTechFileDataRes = await axiosInstance.post('/tech/getdata/', getTechFileDataReqBody);
        return getTechFileDataRes.data;
    }
    catch (error) {
        console.error(error);
        return error.response.data;
    }
}


// below api is for validating project name

/*endpoint project/checkproject/ 
{
"project_name":"project1"
}
 */
export const validateProjectName = async (getProjectData) => {
    try {
        const getProjectDataRes = await axiosInstance.post(
            "/project/checkproject/",
            {
                projectName: getProjectData.projectName,
            }
        );
        return getProjectDataRes.data;
    } catch (error) {
        // Check if the error has a response and log it
        //Returning message other than status code
        if (error.response) {
            console.error("Error while fetching response from /checkproject endpoint.", error.response.data);
            return error.response.data; // Return the response data even if there's an error
        } else {
            console.error("Error while fetching response from /project/checkproject endpoint.", error.message);
        }
    }
};

// below api is for saving project in S3

export const saveProjectInS3 = async (saveProjectReqBody) => {
    try {
        const saveProjectRes = await axiosInstance.post('/project/create/', saveProjectReqBody);
        return saveProjectRes.data;
    }
    catch (error) {
        console.error(error);
        return error.response.data;
    }
}

// below function will fetch the list of netlist files
export const getNetListFiles = async () => {
    try {

        const getTechFileDataRes = await axiosInstance.get(`/netlist/getlist/`);
        return getTechFileDataRes?.data;
    }
    catch (error) {
        console.error(error);
        return error.response.data;
    }
};

// below function will fetch the netlist file data based on filename and type 
export const getNetListData = async (getNetListDataReq) => {
    try {
        const getNetListDataRes = await axiosInstance.post('/netlist/getdata/', getNetListDataReq);
        return getNetListDataRes.data;
    }
    catch (error) {
        console.error(error);
        return error.response.data
    }
}

// below function will fetch the netlist file data based on filename and type
export const getTechFileList = async () => {
    try {
        const getTechFileListRes = await axiosInstance.get("/tech/getlist/");
        return getTechFileListRes?.data;
    } catch (error) {
        console.error(error);
        return error?.response?.data;
    }
};

//below function will call run endpoint which will the current project based on projectid & other parameters

export const runProject = async (runProjectReq) => {
    try {
        const runProjectRes = await axiosInstance.post(
            "/run/project/",
            runProjectReq
        );
        return runProjectRes.data;
    } catch (error) {
        console.error(error);
        return error.response;
    }
};

//below function will get list of all projects

export const getProjectListForUser = async () => {
    //current userid is hard coded for nehab, this endpoint will be updated from backend
    try {
        const getProjectListForUserRes = await axiosInstance.get("/project/list");
        return getProjectListForUserRes.data;
    } catch (error) {
        console.error("Error Fetching user Project List", error);
    }
};
// below endpoint is used for deleting project file from database & S3.
export const deleteRunProjectResult = async (deleteRunProjectReq) => {
    try {
        const response = await axiosInstance.post(
            "/run/clear/result/",
            deleteRunProjectReq
        );
        return response?.data;
    } catch (error) {
        console.error("Error while deleting user project using endpoint/run/clear/result", error);
        return error;
    }
};

/**
 * Fetches stage data from backend api /status/result
 * @returns {object} response data
 * @property {boolean} status - status of the response
 * @property {string} message - error message if status is false
 */
export const fetchStageData = async (currentProjectId, stage, pageNum,filterReq, filterByLayoutReq) => {
    try {
        const response = await axiosInstance.post("stage/result/", {
            projectId: currentProjectId,
            stage: stage,
            page: pageNum,
            pageSize: pageSize,
            filter: filterReq || null,
            filterByLayout: filterByLayoutReq || null
        });
        return response?.data;
    } catch (error) {
        console.error("Error fetching stage result:", error);
        return { status: false, message: error.message };
    }
};


// Fetch base64 image data for a given path
export const fetchImageData = async (imagePath) => {
    try {
        const response = await axiosInstance.post('stage/gdsimg/', { "LayoutData": imagePath });
        return response?.data;
    } catch (error) {
        console.error("Error fetching image data:", error);
        return { status: false, message: error.message };
    }
};


//below endpoint gives the list of projects having stage1 results  under current logged in user 
export const getProjectWithStage1ResultsForUser = async () => {
    try {
        const getProjectWithStage1ResultRes = await axiosInstance.get('/project/stage1_ready/');
        return getProjectWithStage1ResultRes?.data;
    }
    catch (error) {
        console.error("Error fetching Projects having stage1 results for user:", error);
        return error;
    }
}

// below endpoint will give the data of user saved project
export const fetchUserDataFromSavedProject = async (projectId) => {
    try {
        const getUserDataFromSavedProject = await axiosInstance.get(`/project/details/${projectId}/`)
        return getUserDataFromSavedProject?.data;
    }
    catch (error) {
        console.error("Error while fetching user saved project details", error);
        return error;
    }
}

export const editProjectData = async (projectId, editProjectReqJSON) => {
    try {
        const editUserDataFromProject = await axiosInstance.patch(`/project/edit/${projectId}/`, editProjectReqJSON)
        return editUserDataFromProject?.data;
    }
    catch (error) {
        console.error("Error while updating user saved project details", error)
        return error;
    }

}

//below function helps in fetching job details from database
export const getJobDetailsOfJobID = async (jobId) => {
    try {
        const getJobDetailsRes = await axiosInstance.get(`/run/job/${jobId}/`)
        return getJobDetailsRes?.data;
    }
    catch (error) {
        console.error("Error while fetching job details from database", error)
        return error;
    }

}

export const getVersionInfo = async () => {
    try {
        const getVersionInfoRes = await axios.get(`${hostName}/user/about/`);
        return getVersionInfoRes?.data;
    } catch (error) {
        console.error("Error while fetching job details from database", error);
        return error;
    }
};

// below endpoint will give list of running jobs
export const getListOfRunningJob = async (showAllJobs) => {
    try {
        const getListOfRunningJobRes = await axiosInstance.post("/run/list/", { "showAllJobs": showAllJobs })
        return getListOfRunningJobRes?.data;
    }
    catch (error) {
        console.error("Error while fetching list of running job details", error)
        return error;
    }
}
// below endpoint will give user details
export const getDetailsOfUser = async () => {
    try {
        const getdetailsRes = await axiosInstance.get("profile/details/");
        return getdetailsRes?.data;
    } catch (error) {
        console.error("Error while fetching users details", error);
        return error;
    }
};

// below endpoint will download stage results for stage 1 and 2 both
export const downloadStageResults = async (downloadPayload) => {
    try {
        const downloadStageResultsRes = await axiosInstance.post("stage/download/result/", downloadPayload, {
            responseType: 'blob',
        });
        return downloadStageResultsRes;
    } catch (error) {
        console.error("Error while fetching users details", error);
        return error;
    }
};

//below endpoint will manage change user password
export const changeUserPassword = async (oldPassword, newPassword) => {
    try {
        const changeUserPasswordRes = await axiosInstance.post("profile/password/update/", {
            "old_password": oldPassword,
            "password": newPassword
        });
        return changeUserPasswordRes?.data;
    } catch (error) {
        console.error("Error while fetching users password", error);
        return error.response.data;
    }
};

// below endpoint allow user to delete their own project
export const deleteUserProject = async (projectId) => {
    try {
        const deleteUserProjectRes = await axiosInstance.delete(`project/delete/${projectId}/`)
        return deleteUserProjectRes?.data;
    }
    catch (error) {
        console.error("Error while deleting the user project", error)
        return error?.response?.data;
    }
}

// below enpoint allow user to download single GDS image on graph

export const downloadSingleGDSImage = async (downloadSingleGDSImageReq) => {
    try {
        const downloadSingleGDSImageRes = await axiosInstance.post(
            `stage/download/gds/`,
            downloadSingleGDSImageReq,
            {
                responseType: 'blob',
            }
        );
        return downloadSingleGDSImageRes;
    } catch (error) {
        console.error("Error while downloading the GDS Image", error);
        return error?.response?.data;
    }
  };
  
//   Below endpoint gives Run Result summary Data for stage 1 & 2

export const RunResultSummaryData = async (RunResultSummaryReq) =>{
    try{
  const RunResultSummaryRes = await axiosInstance.post("/stage/summary/",RunResultSummaryReq)
  return RunResultSummaryRes?.data;
    }
    catch(error){
   console.error("Error While fetching Run Result Summary", error)
   return error?.response?.data;
    }

}


// below enpoint validate the netlist content

export const checkValidationNetlist = async (netlistFileContent) => {
    try {
        const encodedContent = btoa(netlistFileContent); // Encoding content to base64
        const requestBody = {
            netlistFileContents: encodedContent, 
        };
        const validationNetlistRes = await axiosInstance.post(`/netlist/validate/`, requestBody);
        return validationNetlistRes?.data;
    } catch (error) {
        console.error("Error while validating Netlist content", error);
        throw error;
    }
};

//below endpoint check status of run results for project and if results are there it gives true
export const getRunResultsStatus = async (runResultsReq) => {
    try {
        
        const runResultsRes = await axiosInstance.post(`/stage/status/`, runResultsReq);
        return runResultsRes?.data?.data;
    } catch (error) {
        console.error("Error while getting status of run results", error);
        //throw error;
    }
}; 

//below endpoint upload the project tech file from local
export const  uploadProjectTechFile = async(uploadTechFileReq) => {
    try{
     const uploadTechFileRes = await axiosInstance.post("/project/tech-upload/", uploadTechFileReq,
        {
            headers: {
                "Content-Type": "multipart/form-data",
            },
        }) 
        return uploadTechFileRes?.data
    }
    catch(error){
      console.error("Error while uploading tech file", error)
      return error?.response?.data;
    }
    }

//below endpoint get the lost of project techfile list 
export const getProjectTechFileList = async (projectId) => {
    try {
        const projectTechFileListRes = await axiosInstance.get(`/project/techfile/${projectId}`)
        return projectTechFileListRes?.data;
    }
    catch (error) {
        console.error("Error while getting the project TechFile list")
        return error?.response?.data;
    }
}

//below endpoint get data for project techfile
export const getProjectTechFileData = async (projectTechFileReq) => {
    try {
        const projectTechFileDataRes = await axiosInstance.post(`project/techfiledata/`, projectTechFileReq)
        return projectTechFileDataRes?.data
    }
    catch (error) {
        console.error("Error while getting the project TechFile Data")
        return error?.response?.data;
    }
}

// below endpoint will download project techfile 
export const downloadProjectTechFile = async (downloadProjectTechFileReq) => {
    try {
        const downloadProjectTechFileRes = await axiosInstance.post(`/project/downloadtech/`, downloadProjectTechFileReq,
            {
                responseType: 'blob',
            })
        return downloadProjectTechFileRes;
    }
    catch (error) {
        console.error("Error While downloading the project techfile", error)
        return error?.data
    }
}

// below endpoint will save techfile name
export const saveTechFile = async(saveTechFileReq) =>{
    try{
    const saveTechFileRes = await axiosInstance.post("/project/savetecfile/",saveTechFileReq)
    return saveTechFileRes?.data
    }
    catch(error){
        console.error("Error while saving the techfile", error)
        return error?.response?.data;
    }
} 

// below endpoint will rename the techfile
export const renameTechFile = async (renameTechFileReq) =>{
    try{
       const renameTechFileRes = await axiosInstance.post("project/renametechfile/",renameTechFileReq)
       return renameTechFileRes?.data
    }
     catch(error){
         console.error("Error while renaming the tech file", error)
         return error?.response?.data;
}
}