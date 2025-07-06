
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: ModifyNetlistFileModal.js  
 * Description: This file is responsible to handle modify netlist file modal at admin level 
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

import React from 'react';
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faRotate } from "@fortawesome/free-solid-svg-icons";
import { Tooltip as ReactTooltip } from 'react-tooltip'

const ModifyNetlistFileModal = ({ userNetlistFileContent, setUserNetlistFileContent, validationError, setValidationError, handleResetNetlistFile }) => {


  // below function handle input change
  const handleContentChange = (e) => {
    setUserNetlistFileContent(e?.target?.value);

  };

  return (
    <div className='w-100 h-100'>
      {/* Show error message when netlistcontent not validate */}
      <div className='d-flex justify-content-end align-items-center mb-2'>
        <FontAwesomeIcon
          icon={faRotate}
          id="admin-netlist-edit-icon"
          style={{
            cursor: "pointer",
            border: "none",
            textDecoration: "none",
            outline: "none",
          }}
          className="admin-button border-0"
          onClick={handleResetNetlistFile}
          data-tooltip-id="admin-netlist-content-reset-icon"
          data-tooltip-content="Reset Netlist Content"
        />
      </div>
      <ReactTooltip id="admin-netlist-content-reset-icon" style={{ zIndex: 9999 }} />

      {/* Validation Errors messages */}
      {validationError && (
        <div
          className="mb-2"
          style={{
            maxHeight: '60px',
            overflowY: 'auto',
            color: '#dc3545',
            fontSize: '14px',
            fontFamily: 'sans-serif',
            whiteSpace: 'pre-line',
            padding: '8px',
            
          }}
        >
          {Array.isArray(validationError) ? (
            validationError?.map((err, index) => <div key={index}>{err}</div>)
          ) : (
            <div>{validationError}</div>
          )}
        </div>
      )}

      
      <textarea
        value={userNetlistFileContent}
        onChange={handleContentChange}
        style={{
          width: '100%',
          height: validationError ? 'calc(85% - 20px)' : '95%',
          padding: '8px',
          fontSize: '16px',
          fontFamily: 'monospace',
          whiteSpace: 'pre',
          overflowWrap: 'normal',
          overflowY: 'auto',
          backgroundColor: '#f8f8f8',
          border: validationError ? '5px solid #dc3545' : '1px solid #ced4da',
          borderRadius: '4px'
        }}
      />
    </div>
  );
};

export default ModifyNetlistFileModal;
