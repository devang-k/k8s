 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: DeleteNetlistFileModal.js  
 * Description: This file is responsible to show netlist file delete confirmation modal content at admin level 
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

import React from 'react'

const DeleteNetlistFileModal = ({ selectedNetlistFileName }) => {
    return (
        <div className='w-100'>
            <p className='d-flex justify-content-center' style={{ wordBreak: 'break-word' }}>{`Are you sure you want to delete ${selectedNetlistFileName}?`}</p>
        </div>
    )
}

export default DeleteNetlistFileModal