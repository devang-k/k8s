 
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: App.js  
 * Description: This file serves as the main entry point for the React application. 
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
import "./App.css";
import MainLayout from "./components/MainLayout/MainLayout";
import Home from "./components/home/Home";
import NotFound from "./components/404/";
import LoginPage from "./components/login/LoginPage";
import Dashboard from "./components/Dashboard";
import Stage1Result from "./components/Results/Stage1Result";
import Stage2Result from "./components/Results/Stage2Result";
import { Routes, Route, BrowserRouter } from "react-router-dom";
import NetlistFile from "./components/project/netlistfile/NetlistFile";
import TechFile from "./components/project/techfile/TechFile";
import Variations from "./components/project/techfile/variations/Variations";
import Parameters from "./components/project/techfile/parameters/Parameters";
import { TechFileProvider } from "./components/providers/TechFileProvider/TechFileProvider";
import { NetListFileProvider } from "./components/providers/NetListFileProvider/NetListFileProvider";
import { CreateProjectProvider } from "./components/providers/CreateProjectProvider/CreateProjectProvider";
import { EditProjectProvider } from "./components/providers/EditProjectProvider/EditProjectProvider";
import { Stage1ResultProvider } from "./components/providers/Stage1ResultProvider/Stage1ResultProvider";
import { Stage2ResultProvider } from "./components/providers/Stage2ResultProvider/Stage2ResultProvider";
import { LayoutGraphProvider } from "./components/providers/LayoutGraphProvider/LayoutGraphProvider";
import { RunProjectProvider } from "./components/providers/RunProjectProvider/RunProjectProvider";
import { RunHyperExpressivityProjectProvider } from "./components/providers/RunHyperExpressivityProjectProvider/RunHyperExpressivityProjectProvider";
import { AdminProvider } from "./components/providers/AdminProvider/AdminProvider";
import { ManageUserProvider } from "./components/providers/ManageUserProvider/ManageUserProvider";
import { FilterResultsProvider } from "./components/providers/FilterResultsProvider/FilterResultsProvider";
import Loader from "./components/Results/Loader";
import ProtectRoute from "./components/RouterProtection/ProtectRoute";
import PrivacyPolicy from "./components/Footer/PrivacyPolicy";
import TermsAndConditions from "./components/Footer/TermsAndConditions";
import RefreshHandler from "./components/RefreshHandler/RefreshHandler";
import AdminDashboard from "./Admin/AdminDashboard";
import ProtectAdminRoute from "./Admin/ProtectAdminRoute";
import AdminNetlist from "./Admin/AdminComponents/AdminNetlist/AdminNetlist";
import AdminSettings from "./Admin/AdminSettings";
import ManageUsers from "./Admin/AdminComponents/ManageUsers/ManageUsers";
import AdminTechFile from "./Admin/AdminComponents/AdminTechFile/AdminTechFile";
import Profile from "./components/UserProfile/Profile";


function App() {
  return (
    <BrowserRouter>
      <RefreshHandler>
      <LayoutGraphProvider>
        <CreateProjectProvider>
          <NetListFileProvider>
            <TechFileProvider>
              <EditProjectProvider>
                <Stage1ResultProvider>
                  <Stage2ResultProvider>
                    <RunProjectProvider>
                      <RunHyperExpressivityProjectProvider>
                        <FilterResultsProvider>
                        <AdminProvider>
                          <ManageUserProvider>
                            <Routes>
                              <Route path="*" element={<NotFound />} />
                              <Route path="/" element={<LoginPage />} />
                              <Route element={<ProtectRoute />}>
                                <Route path="home" element={<MainLayout />}>
                                  <Route path="" element={<Home />} />
                                  <Route path="user-profile" element={<Profile />} />
                                </Route>

                                <Route path="dashboard" element={<Dashboard />}>
                                  <Route path="netlist-file" element={<NetlistFile />} />
                                  <Route path="techfiles" element={<TechFile />}>
                                    <Route path="variations" element={<Variations />} />
                                    <Route path="parameters" element={<Parameters />} />
                                  </Route>
                                  <Route path="loader" element={<Loader />} />
                                  <Route path="stage1result" element={<Stage1Result />} />
                                  <Route path="stage2result" element={<Stage2Result />} />
                                </Route>
                                <Route element={<ProtectAdminRoute />}>
                                  <Route path="admin-settings" element={<AdminSettings />}>
                                    <Route path="user-profile" element={<Profile />} />
                                    <Route path="adminDashboard" element={<AdminDashboard />} />
                                    <Route path="manage-admin-netlist" element={<AdminNetlist />} />
                                    <Route path="manage-admin-techfile" element={<AdminTechFile />} />
                                    <Route path="manage-users" element={<ManageUsers />} />
                                  </Route>
                                </Route>
                              </Route>
                              <Route path="privacy-policy" element={<PrivacyPolicy />} />
                              <Route path="terms-and-conditions" element={<TermsAndConditions />} />
                            </Routes>
                          </ManageUserProvider>
                        </AdminProvider>
                        </FilterResultsProvider>
                      </RunHyperExpressivityProjectProvider>
                    </RunProjectProvider>
                  </Stage2ResultProvider>
                </Stage1ResultProvider>
              </EditProjectProvider>
            </TechFileProvider>
          </NetListFileProvider>
        </CreateProjectProvider>
        </LayoutGraphProvider>
      </RefreshHandler>
    </BrowserRouter>
  );
}

export default App;
