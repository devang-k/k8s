 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: AccordianComponent.js  
 * Description: This file defines a reusable React component for displaying Accordians. 
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
import Accordion from 'react-bootstrap/Accordion';

function AccordianComponent({ sections }) {
  return (
    sections === null ? <div style={{display:"flex",justifyContent:"center"}}>Variation Not Supported</div> :
    <>
     {/**if there is some data in sections then dispalying it in accordian */}
    <div style={{ width: '100%', overflowX: 'auto' }}>
      <Accordion>
        {sections.map((section, index) => (
          <Accordion.Item key={index} eventKey={index.toString()}>
            <Accordion.Header>{section.title}</Accordion.Header>
            <Accordion.Body>
              {section.content}
            </Accordion.Body>
          </Accordion.Item>
        ))}
      </Accordion>
      </div>
    </>
  );
}

export default AccordianComponent;