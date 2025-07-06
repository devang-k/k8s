 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: LayoutGraphContext.js  
 * Description: This file is responsible to save stage 1 & stage 2 (Layout generation & Hyper expressivity) graph data in context 
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

import { createContext, useContext } from 'react';

export const LayoutGraphContext = createContext({
    stage1GraphData: null, // Make sure this is initially null or an empty object
    setStage1GraphData: () => null,
    stage2GraphData: null, // Make sure this is initially null or an empty object
    setStage2GraphData: () => null,

});

export const useLayoutGraphContext = () => {
    return useContext(LayoutGraphContext);
};
