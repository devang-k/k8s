
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: NetListFileProvider.js  
 * Description: This file is responsible to share Netlist file data to other components within the application. 
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

import React, { useMemo, useState } from "react"

import { NetListContext } from "./NetListFileContext"

export const NetListFileProvider = ({ children }) => {

    const [netListFileData, setNetListFileData] = useState();
    const [selectedNetlistFileName, setSelectedNetlistFileName] = useState();
    const [selectedNetlistFileType, setSelectedNetlistFileType] = useState();
    const [netlistFileContent, setNetlistFileContent] = useState("");
    const [netlistCellInfo, setNetlistCellInfo] = useState([]);
    const [isNetListFileSelected, setIsNetListFileSelected] = useState(false);
    const [actionSelected, setActionSelected] = useState(1);
    const [isSelectAllChecked, setIsSelectAllChecked] = useState(false);
    const [isNetlistDataChanged, setIsNetlistDataChanged] = useState(false);
    const [defaultNetlistFileData, setDefaultNetlistFileData] = useState({});
    const [isNetlistFileContentDataChanged ,setIsNetlistFileContentDataChanged ] = useState(false)

    const value = useMemo(() => {
        return {
            netListFileData,
            setNetListFileData,
            selectedNetlistFileName,
            setSelectedNetlistFileName,
            selectedNetlistFileType,
            setSelectedNetlistFileType,
            netlistFileContent,
            setNetlistFileContent,
            netlistCellInfo,
            setNetlistCellInfo,
            isNetListFileSelected,
            setIsNetListFileSelected,
            actionSelected,
            setActionSelected,
            isSelectAllChecked,
            setIsSelectAllChecked,
            isNetlistDataChanged,
            setIsNetlistDataChanged,
            defaultNetlistFileData,
            setDefaultNetlistFileData,
            isNetlistFileContentDataChanged ,
            setIsNetlistFileContentDataChanged,
        }
    }, [
        netListFileData,
        setNetListFileData,
        selectedNetlistFileName,
        setSelectedNetlistFileName,
        selectedNetlistFileType,
        setSelectedNetlistFileType,
        netlistFileContent,
        setNetlistFileContent,
        netlistCellInfo,
        setNetlistCellInfo,
        isNetListFileSelected,
        setIsNetListFileSelected,
        actionSelected,
        setActionSelected,
        isSelectAllChecked,
        setIsSelectAllChecked,
        isNetlistDataChanged,
        setIsNetlistDataChanged,
        defaultNetlistFileData,
        setDefaultNetlistFileData,
        isNetlistFileContentDataChanged,
        setIsNetlistFileContentDataChanged,
    ]);

    return (
        <NetListContext.Provider value={value}>{children}</NetListContext.Provider>
    )
}