 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: ModalComponent.js  
 * Description: This file defines a reusable React component for displaying modals. 
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

import React from "react";
import Modal from "react-bootstrap/Modal";

//  show accepts the boolean value when the state is true then the modal will appear
// modalContent accepts object and the object should have the title, body and footer
const ModalComponent = ({
  id,
  size,
  show,
  handleClose,
  modalContent,
  modalCSSClass,
  bodyClassName,
  modalTitleCSSClass
}) => {
  const { title, body, footer } = modalContent;

  return (
    <Modal
      id={id ? id : "generic-modal-id"}
      show={show}
      backdrop="static"
      keyboard={false}
      onHide={handleClose}
      centered
      size={size ? size : "lg"}
      animation={false}
      className={`${modalCSSClass ? modalCSSClass : "modal-style overflow-hidden "} ${show ? "modal-fade-in-bottom" : ""}`}
    >
      <Modal.Header closeButton>
      <Modal.Title style={modalTitleCSSClass}>{title}</Modal.Title>
      </Modal.Header>
      <Modal.Body
        className={
          bodyClassName
            ? bodyClassName
            : "d-flex align-items-center justify-content-center"
        }
      >
        {body}
      </Modal.Body>
      <Modal.Footer className="text-center d-block justify-content-center">
        {footer}
      </Modal.Footer>
    </Modal>
  );
};

export default ModalComponent;
