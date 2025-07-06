
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: CollapsibleTerminal.js  
 * Description: This file is responsible to show terminal which is collapsible. 
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

import React, { useEffect, useRef, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useRunProjectContext } from "../providers/RunProjectProvider/RunProjectContext";
import { Tooltip as ReactTooltip } from 'react-tooltip'

const CollapsibleTerminal = ({
  isTerminalFullScreenOpen,
  setIsTerminalFullScreenOpen,
  isTerminalSmallScreenOpen,
  setIsTerminalSmallScreenOpen,
  terminalHeight,
  setTerminalHeight,
  faChevronDown,
  faChevronUp,
  faUpRightAndDownLeftFromCenter,
  faDownLeftAndUpRightToCenter,
  faWindowMinimize,
}) => {

  const { runLayoutRunningJobLogs } = useRunProjectContext();  //reading data  from run project context
  const terminalRef = useRef(null);
  const [shouldScroll, setShouldScroll] = useState(true);

  useEffect(() => {
    if (isTerminalFullScreenOpen) {
      setTerminalHeight("100%");
    } else if (isTerminalSmallScreenOpen) {
      setTerminalHeight("200px");
    } else {
      setTerminalHeight("25px");
    }
  }, [isTerminalFullScreenOpen, isTerminalSmallScreenOpen, setTerminalHeight]);


  // Check if the terminal should auto-scroll to the bottom
  const handleScroll = () => {
    if (terminalRef?.current) {
      // scrollTop → The distance the user has scrolled from the top.
      //scrollHeight → The total height of the content inside the terminal.
      //clientHeight → The height of the terminal that is currently visible on the screen(without scrolling).
      const { scrollTop, scrollHeight, clientHeight } = terminalRef?.current;
      setShouldScroll(Math?.abs(scrollHeight - scrollTop - clientHeight) < 100);
    }
  };

  // Auto-scroll to the latest log when new logs are added
  useEffect(() => {
    if (shouldScroll && terminalRef?.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [runLayoutRunningJobLogs, shouldScroll]);


  const toggleTerminalFullScreen = () => {
    setIsTerminalFullScreenOpen(!isTerminalFullScreenOpen);
    setIsTerminalSmallScreenOpen(false);
  };

  const toggleTerminalSmallScreen = () => {
    setIsTerminalSmallScreenOpen(!isTerminalSmallScreenOpen);
    setIsTerminalFullScreenOpen(false);
  };

  const minimizeTerminal = () => {
    setIsTerminalFullScreenOpen(false);
    setIsTerminalSmallScreenOpen(false);
  };

  return (
    <div className="terminal-container" style={{ height: terminalHeight }}>
      <div
        style={{
          height:
            !isTerminalSmallScreenOpen && !isTerminalFullScreenOpen
              ? "25px"
              : terminalHeight,
          position: "relative",
        }}
      >
        <div
          className="terminal-header"
          id="terminal-header"
          style={{
            height: "25px",
            padding: "0 12px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            backgroundColor: "#1b5376",
            color: "white",
          }}
        >
          <span>Status</span>
          <div style={{ display: "flex", alignItems: "center" }}>
            <span
              
              data-tooltip-id="collapsible-terminal-fullscreen-button-tooltip"
              data-tooltip-content={"Maximize"}
              onClick={toggleTerminalFullScreen}
              style={{
                cursor: "pointer",
                marginRight: "12px",
                padding: "8px",
                transition: "transform 0.2s",
                borderRadius: "4px",
                display: isTerminalFullScreenOpen ? "none" : "flex",
                alignItems: "center",
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.transform = "scale(1.1)")
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.transform = "scale(1)")
              }
            >
              <FontAwesomeIcon
                id="fullscreen-icon"
                icon={
                  isTerminalFullScreenOpen
                  ? faDownLeftAndUpRightToCenter
                  : faUpRightAndDownLeftFromCenter
                }
                size="sm"
              />
              <ReactTooltip id="collapsible-terminal-fullscreen-button-tooltip" style={{ fontSize: "11px", zIndex: 9999}} />
            </span>
            <span
              
              data-tooltip-id="collapsible-terminal-smallscreen-button-tooltip"
              data-tooltip-content={"Restore"}
              onClick={toggleTerminalSmallScreen}
              style={{
                cursor: "pointer",
                marginRight: "12px",
                padding: "8px",
                transition: "transform 0.2s",
                borderRadius: "4px",
                display: isTerminalSmallScreenOpen ? "none" : "flex",
                alignItems: "center",
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.transform = "scale(1.1)")
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.transform = "scale(1)")
              }
            >
              <FontAwesomeIcon id="small-screen-icon"
                icon={(!isTerminalFullScreenOpen && !isTerminalSmallScreenOpen) ? faChevronUp : faChevronDown}
                size="sm"
              />
              <ReactTooltip id="collapsible-terminal-smallscreen-button-tooltip" style={{ fontSize: "11px",  zIndex: 9999  }} />
            </span>
            <span
              
              data-tooltip-id="collapsible-terminal-minimize-button-tooltip"
              data-tooltip-content={"Minimize"}
              onClick={minimizeTerminal}
              style={{
                cursor: "pointer",
                padding: "8px",
                transition: "transform 0.2s",
                borderRadius: "4px",
                merginBottom: "-15px",
                display: (!isTerminalSmallScreenOpen && !isTerminalFullScreenOpen) ? "none" : "flex",
                alignItems: "center",
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.transform = "scale(1.1)")
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.transform = "scale(1)")
              }
            >
              <FontAwesomeIcon id="minimize-icon" icon={faWindowMinimize} size="sm" />
              <ReactTooltip id="collapsible-terminal-minimize-button-tooltip" style={{ fontSize: "11px", zIndex: 9999 }} />
            </span>
          </div>
        </div>

        {(!isTerminalFullScreenOpen && !isTerminalSmallScreenOpen) || (
          <div
            className="terminal-body app-secondary-color"
            id="terminal-body"
            onScroll={handleScroll}
            ref={terminalRef}
            style={{
              color:"black",
              height: "calc(100% - 25px)", // Adjust height to account for the header
              overflowY: "auto", // Enable vertical scrolling
              padding: "10px", // Optional padding for better aesthetics
            }}
          >
            {(runLayoutRunningJobLogs !== null || runLayoutRunningJobLogs?.length) && runLayoutRunningJobLogs?.map((item, index) => (
              <div key={index}>{item}</div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default CollapsibleTerminal;
