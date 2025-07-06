
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: LayoutImageData.js  
 * Description: This file is responsible to show Layout GDS Image Data 
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

import React, { useState } from "react";
import { Empty } from "antd";
import { useStage1ResultContext } from "../providers/Stage1ResultProvider/Stage1ResultContext.js";
import { useStage2ResultContext } from "../providers/Stage2ResultProvider/Stage2ResultContext.js";
import { useCreateProjectContext } from "../providers/CreateProjectProvider/CreateProjectContext.js";
import useSingleGdsDownload from "../../Hooks/downloadSingleGdsFileHook/useSingleGdsDownload.js";
import useGdsLayoutCart from "../../Hooks/gdsLayoutCartHook/useGdsLayoutCart";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import ContextMenu from "../utils/ContextMenu/ContextMenu.js";
import { faDownload, faImage, faMinus, faPlus, faShoppingCart, faTrash } from "@fortawesome/free-solid-svg-icons";

const LayoutImageData = ({ gdsData, actionSelected, loadingRef, loadingMore, setViewCartOption, stageGdsCartData, userCurrentStage}) => {
    const { selectedGdsItems, setSelectedGdsItems, setIsGdsSelectAllChecked } = useStage1ResultContext();
    const { isUserOnStage2Page } = useStage2ResultContext();
    const { currentProjectId } = useCreateProjectContext();
    const [layoutContextMenu, setLayoutContextMenu] = useState(false);
    const [selectedGdsImage, setSelectedGdsImage] = useState();
    const [selectedGdsName, setSelectedGdsName] = useState();
    const [contextMenuPosition, setContextMenuPosition] = useState(null); 
    const { handleCart, isGDSAddedToCart, handleClearCart } = useGdsLayoutCart(selectedGdsName, userCurrentStage);
    const {downloadGDSFile} = useSingleGdsDownload();


     //below function helps open image in new tab base64 image in new tab to view it in enlarged format
    const handleGdsLayout = (imageData, gdsName, e) => {
        setSelectedGdsImage(imageData);
        setSelectedGdsName(gdsName);
        const { clientX, clientY } = e;
        setContextMenuPosition({ x: clientX, y: clientY });
        setLayoutContextMenu(true);
    };

     //below function handles the view layout in different tab.
    const handleViewLayout = () => {
        const newTab = window.open();
        if (newTab) {
            newTab.document.body.innerHTML =
                `<div style="display: flex; flex-direction: column; height: 90vh; justify-content: center; align-items: center; text-align: center;">
                   <h2>${selectedGdsName}</h2>
                   <img src="${selectedGdsImage}" alt="${selectedGdsName}" style="width: 100%; height: 100%; object-fit: contain;" />
                 </div>`;
            newTab.document.title = selectedGdsName; // Setting gds name as title
        }
    }

    // context menu option
    const ContextMenuData = [
        {
            title: 'Download',
            action: () => {downloadGDSFile(selectedGdsName, currentProjectId, setLayoutContextMenu, userCurrentStage)},
            icon: <FontAwesomeIcon icon={faDownload} />
        },
        {
            title: 'View Layout',
            action: handleViewLayout,
            icon: <FontAwesomeIcon icon={faImage} />
        },
        {
            title: isGDSAddedToCart ? "Remove from cart" : "Add to cart",
            action: () => { handleCart() },
            icon: <FontAwesomeIcon icon={isGDSAddedToCart ? faMinus : faPlus} />
        },
        ...(stageGdsCartData?.length > 0 ? [{
            title: "View Cart",
            action: () => { setViewCartOption(true) },
            icon: <FontAwesomeIcon icon={faShoppingCart} />
        }] : []),
        ...(stageGdsCartData?.length > 0 ? [{
            title: "Clear Cart",
            action: () => { handleClearCart(setSelectedGdsName, setViewCartOption) },
            icon: <FontAwesomeIcon icon={faTrash} />
        }] : [])

    ]

    // Function to handle checkbox change
    const handleCheckboxChange = (itemName) => {
        if (!Array.isArray(selectedGdsItems)) {
            setSelectedGdsItems([itemName]); // Initialize with the first item
        }
        else if (selectedGdsItems && Array.isArray(selectedGdsItems) && selectedGdsItems?.includes(itemName)) {
            setSelectedGdsItems(
                selectedGdsItems?.filter((item) => item !== itemName)
            );
            setIsGdsSelectAllChecked(false);
        } else {
            setSelectedGdsItems([...selectedGdsItems, itemName]);
        }
    };
    return (
        <div
            className="p-3 pb-0 h-100"
        >
            {loadingRef?.current && !loadingMore && (
                <div className="d-flex justify-content-center align-items-center" style={{ height: "100%" }}>
                    <div className="spinner-border" role="status">
                        <span className="sr-only">Loading...</span>
                    </div>
                </div>
            )}
            <div className="row">
                {gdsData?.items?.map((gds, index) => (
                    <div
                        key={index}
                        className="col-12 col-sm-6 col-md-4 col-lg-3 mb-3"
                    >
                        <div className="card">
                            {(actionSelected === 2 || actionSelected === 3) && (
                             
                                <>
                                   {(!isUserOnStage2Page)&&(
                                    <input
                                        className="form-check-input position-absolute cursor_pointer"
                                        type="checkbox"
                                        id={`gds-images-checkbox-${gds?.name}`}
                                        name={`gds-images-checkbox-${gds?.name}`}
                                        value={gds?.name}
                                        checked={selectedGdsItems?.includes(gds?.name)}
                                        onChange={() => handleCheckboxChange(gds?.name)}
                                        style={{
                                            top: "5px",
                                            left: "15px",
                                            zIndex: 1,
                                            padding: "8px",
                                            borderColor: "#b19494",
                                        }}
                                    />
                                )}
                                </>
                            )}
                            <img
                                className="card-img-top"
                                title={gds?.name}
                                src={gds?.src}
                                alt={gds?.name}
                                style={{
                                    width: "100%",
                                    height: "auto",
                                    objectFit: "cover",
                                    border: `${stageGdsCartData?.includes(gds?.name) ? "4px" : "0.5px"} solid #1b5376`,
                                    cursor: "pointer",
                                }}
                                loading="lazy"
                                onClick={(e) => handleGdsLayout(gds?.src, gds?.name, e)}
                            />
                            <div
                                className="app-primary-button-color border-0 rounded-bottom card-body py-0 m-0 text-center text-light"
                               
                            >
                                <p className="card-text">{gds?.name}</p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
            {loadingMore && (
                <div className="d-flex justify-content-center align-items-center">
                    <div className="spinner-border" role="status">
                        <span className="sr-only">Loading more...</span>
                    </div>
                </div>
            )}
            {!loadingRef?.current && gdsData?.length === 0 && (
                <div
                    className="d-flex justify-content-center align-items-center"
                    style={{ height: "50vh" }}
                >
                    <Empty />
                </div>
            )}
            <ContextMenu
                show={layoutContextMenu}
                menuOptions={ContextMenuData}
                onHide={() => setLayoutContextMenu(false)}
                position={contextMenuPosition}
            />
        </div>
    );
};

export default LayoutImageData;
