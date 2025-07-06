
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: DownloadResultsModalBody.js  
 * Description: This file is responsible to show download result modal content 
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

import React, { useEffect } from 'react';
import Form from 'react-bootstrap/Form';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faImages, faTable, faChartColumn } from '@fortawesome/free-solid-svg-icons';
import { useFilterResultsContext } from '../providers/FilterResultsProvider/FilterResultsContext';
import { useStage1ResultContext } from '../providers/Stage1ResultProvider/Stage1ResultContext';
import { useStage2ResultContext } from '../providers/Stage2ResultProvider/Stage2ResultContext';
import { isDebugModeOn} from "../../constant";

export const DownloadResultsModalBody = ({ checkedValues, handleCheckboxChange, isDownloading, userStage }) => {

  const {
    selectedDownloadOption,
    setSelectedDownloadOption,
    stage1GdsCartData,
    stage2GdsCartData,
    stage1Level2Filter,
    stage2Level2Filter,
    stage1GraphSelectedGdsCells,
    stage2GraphSelectedGdsCells,
    isFilterApplied } = useFilterResultsContext();
  const { stage1Result } = useStage1ResultContext();
  const { stage2Result } = useStage2ResultContext()


  // Check if cart download option should be visible and if data exists for cart download
  const isCartDownloadVisible = (userStage === 1 && stage1GdsCartData && stage1GdsCartData?.length > 0) || (userStage === 2 && stage2GdsCartData && stage2GdsCartData?.length > 0);

  // Check if there is no data after applying filter
  const hasNoFilteredData = isFilterApplied && ((stage1Result?.status === false) || (stage2Result?.status === false))

  const handleRadioChange = (option) => {
    // Disable filtered download if no data available 
    if (hasNoFilteredData && option === 3) return;
    setSelectedDownloadOption(option);
  };

  // Set default selection based on conditions
  useEffect(() => {
    if (isCartDownloadVisible) {  // If cart data exists, select cart download by default
      setSelectedDownloadOption(1);
    } else if (isFilterApplied && hasNoFilteredData) {  // If no filtered data, select summary download
      setSelectedDownloadOption(4);
    } else if( (userStage === 1 && stage1GraphSelectedGdsCells?.length > 0) || (userStage === 2 && stage2GraphSelectedGdsCells?.length > 0)){
      setSelectedDownloadOption(3);
    }
    else {
      setSelectedDownloadOption(3);
    }
  }, [isCartDownloadVisible, isFilterApplied, hasNoFilteredData, setSelectedDownloadOption,stage1GraphSelectedGdsCells,stage2GraphSelectedGdsCells,userStage]);


  return (
    <div className="container">
      <div className='column gap-8'>
        <div className='column gap-8 mb-2'>
          {/* Adding radio buttons here to select the download type  */}
          <Form>
            {isCartDownloadVisible && (
              <Form.Check
                inline
                label="Cart Download"
                name="downloadGroup"
                type={"radio"}
                id={"download-cart-radio"}
                checked={selectedDownloadOption === 1}
                onChange={() => handleRadioChange(1)}
                className={hasNoFilteredData ? "cursor_not_allowed" : ""}
              />
            )}
            <Form.Check
              inline
              label={isFilterApplied || stage1Level2Filter.length > 0 || stage2Level2Filter.length > 0 ||(userStage === 1 && stage1GraphSelectedGdsCells?.length > 0) || (userStage === 2 && stage2GraphSelectedGdsCells?.length > 0) ? "Filtered Download" : "Download All"}
              name="downloadGroup"
              type={"radio"}
              id={"all-filterd-download-cart-radio"}
              checked={selectedDownloadOption === 3}
              onChange={() => handleRadioChange(3)}
              disabled={hasNoFilteredData}  // Disable if no filtered data
              className={hasNoFilteredData ? "cursor_not_allowed" : ""}
            />
            <Form.Check
              inline
              label={"Download Summary"}
              name="downloadGroup"
              type={"radio"}
              id={"download-summary-download-cart-radio"}
              checked={selectedDownloadOption === 4}
              onChange={() => handleRadioChange(4)}
            />
          </Form>
        </div>
        <br />
        {selectedDownloadOption === 4 ? (<></>) : (
          <div className="row justify-content-center">
            {/* GDS Data */}
            <div className="col-md-4">
              <div className="card bg-transparent border-2 py-4 flex-grow-1"
                style={{ cursor: 'pointer' }}
              >
                <label htmlFor="gds" className="card-body py-5"
                  style={{ cursor: 'pointer' }}
                >
                  <div className="d-flex flex-column align-items-center text-center">
                    <input
                      className="form-check-input position-absolute"
                      type="checkbox"
                      id="gds"
                      value="gds"
                      checked={checkedValues.gds}
                      onChange={handleCheckboxChange}
                      style={{ top: '25px', left: '25px', zIndex: 1 }}

                    />
                    <FontAwesomeIcon
                      icon={faImages}
                      className="mb-2 tabs-btn active"
                      style={{ fontSize: '48px' }}
                    />
                    <span className="fw-bold text-muted">GDS Data</span>
                  </div>
                </label>
              </div>
            </div>

            {/* Metrics Data */}
            {/* Metrics option is only enabled if debug mode is on , for prod this option is always disabled */}
            {isDebugModeOn && (
            <div className="col-md-4">
              <div className="card bg-transparent border-2 py-4">
                <label htmlFor="metrics" className="card-body py-5"
                  style={{ cursor: 'pointer' }}
                >
                  <div className="d-flex flex-column align-items-center text-center">
                    <input
                      className="form-check-input position-absolute"
                      type="checkbox"
                      id="metrics"
                      value="metrics"
                      checked={checkedValues?.metrics}
                      onChange={handleCheckboxChange}
                      style={{ top: '25px', left: '25px', zIndex: 1 }}

                    />
                    <FontAwesomeIcon
                      icon={faTable}
                      className="mb-2 tabs-btn active"
                      style={{ fontSize: '48px' }}
                    />
                    <span className="fw-bold text-muted">Metrics Data</span>
                  </div>
                </label>
              </div>
            </div>
            )}
            {/* Pex Data */}
            <div className="col-md-4">
              <div className="card bg-transparent border-2 py-4">
                <label htmlFor="pex" className="card-body py-5"
                  style={{ cursor: 'pointer' }}
                >
                  <div className="d-flex flex-column align-items-center text-center">
                    <input
                      className="form-check-input position-absolute"
                      type="checkbox"
                      id="pex"
                      value="pex"
                      checked={checkedValues?.pex}
                      onChange={handleCheckboxChange}
                      style={{ top: '25px', left: '25px', zIndex: 1 }}

                    />
                    <FontAwesomeIcon
                      icon={faChartColumn}
                      className="mb-2 tabs-btn active"
                      style={{ fontSize: '48px' }}
                    />
                    <span className="fw-bold text-muted">PEX Data</span>
                  </div>
                </label>
              </div>
            </div>

            {/* Show the spinner and progress bar while downloading */}
            {isDownloading && (
              <div className="col-12 mt-3 d-flex justify-content-center align-items-center">
                <div className="spinner-border text-primary" role="status" style={{ marginRight: '10px' }}>
                  <span className="sr-only">Loading...</span>
                </div>
                <p className="mb-0">Generating ZIP...</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
