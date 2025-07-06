 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: index.js  
 * Description: This file is responsible to show main dashboard when result is ready. 
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

import { Outlet } from "react-router-dom";
import { useState } from "react";
import NavBar from "../navbar/navbar";
import Sidebar from "../Sidebar";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faChevronRight,
  faChevronLeft,
  faChevronDown,
  faChevronUp,
  faUpRightAndDownLeftFromCenter,
  faDownLeftAndUpRightToCenter,
  faWindowMinimize,
} from "@fortawesome/free-solid-svg-icons";
import CollapsibleTerminal from "../CollapsibleTerminal/CollapsibleTerminal";
import { Tooltip } from 'react-tooltip'
import Footer from "../Footer/Footer";

function Dashboard() {
  const [sidebarContent, setSidebarContent] = useState({
    upper: null,
    lower: null,
  });
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isTerminalFullScreenOpen, setIsTerminalFullScreenOpen] =
    useState(false);
  const [isTerminalSmallScreenOpen, setIsTerminalSmallScreenOpen] =
    useState(true);
  const [terminalHeight, setTerminalHeight] = useState("200px");

  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };  

  return (
    <>
      <NavBar />
      <div
        id="dashboard-container"
        className="container-fluid app-secondary-color"
      >
        <div className="row" style={{ height: "100%" }}>
          <div
            id="side-bar-menu"
            className={`col-${isSidebarCollapsed ? "0" : "3"
              } p-0 position-relative`}
          >
            {!isSidebarCollapsed && (
              <Sidebar
                sidebarupper={sidebarContent?.upper}
                sidebarlower={sidebarContent?.lower}
              />
            )}
          </div>

          <main className={`col-${isSidebarCollapsed ? "12" : "9"} p-0 h-100`}>
            <button
              data-tooltip-id="sidebar-collapsible-btn-tooltip"
              data-tooltip-content={isSidebarCollapsed ? "Restore Sidebar" : "Minimize Sidebar"}
              onClick={toggleSidebar}
              className="position-absolute rounded-circle"
              id="sidebar-collapsible-btn"
              style={{
                backgroundColor: "#fff",
                color: "#000",
                top: "40%",
                marginLeft: isSidebarCollapsed ? "0px" : "-10px",
                fontSize: "12px",
                zIndex: 999,
              }}
            >
              <FontAwesomeIcon
                icon={isSidebarCollapsed ? faChevronRight : faChevronLeft}
                style={{ cursor: "pointer" }}
              />
              <Tooltip id="sidebar-collapsible-btn-tooltip" style={{ fontSize: "11px" }} />
            </button>
            <div className="d-flex flex-column" style={{ height: "100%" }}>
              <div className="d-flex flex-column h-100 app-secondary-color border-start border-3 border-dark">
                <div
                  className={`flex-grow-1 outletDiv ${isTerminalFullScreenOpen ? "d-none" : ""
                    }`}
                  style={{
                    overflow: "hidden",
                    height: "100vh",
                    display: "flex",
                    flexDirection: "column",
                  }}
                >
                  <Outlet context={{ setSidebarContent, toggleSidebar, isSidebarCollapsed, terminalHeight }} />
                </div>
                  <CollapsibleTerminal
                    isTerminalFullScreenOpen={isTerminalFullScreenOpen}
                    setIsTerminalFullScreenOpen={setIsTerminalFullScreenOpen}
                    isTerminalSmallScreenOpen={isTerminalSmallScreenOpen}
                    setIsTerminalSmallScreenOpen={setIsTerminalSmallScreenOpen}
                    terminalHeight={terminalHeight}
                    setTerminalHeight={setTerminalHeight}
                    FontAwesomeIcon={FontAwesomeIcon}
                    faChevronDown={faChevronDown}
                    faChevronUp={faChevronUp}
                    faUpRightAndDownLeftFromCenter={
                      faUpRightAndDownLeftFromCenter
                    }
                    faDownLeftAndUpRightToCenter={faDownLeftAndUpRightToCenter}
                    faWindowMinimize={faWindowMinimize}
                  />
              </div>
            </div>
          </main>
        </div>
      </div>
    <Footer />
  </>
  );
}

export default Dashboard;
