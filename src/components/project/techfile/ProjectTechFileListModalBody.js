import React, { useState } from 'react';
import { Tooltip as ReactTooltip } from 'react-tooltip'
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faPen, faDownload } from "@fortawesome/free-solid-svg-icons";
import { Button } from 'react-bootstrap';

const ProjectTechFileListModalBody = ({ projectTechFileListData, setSelectedProjectTechFileId, setSelectedProjectTechFileNameFromList, setSelectedProjectTechFileProjectIdFromList, handleRenameTechFile, handleDownloadProjectTechFile, loading }) => {
    const [selectedID, setSelectedID] = useState();

    const convertToIST = (utcDateString) => {
        const date = new Date(utcDateString);
        const formatter = new Intl.DateTimeFormat('en-IN', {
            timeZone: 'Asia/Kolkata',
            year: 'numeric',
            month: 'short',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false,
        });
        return formatter.format(date);
    };

    const handleRowClick = (id, name, projectId) => {
        setSelectedID(id);
        setSelectedProjectTechFileId(id);
        setSelectedProjectTechFileNameFromList(name)
        setSelectedProjectTechFileProjectIdFromList(projectId)
    };

    return (
        <div className="row w-100">
            <ul className="list-group">
                {/* Header Row */}
                <li
                    className="list-group-item border rounded mb-2 bg-light sticky-top me-0 pe-3"
                    style={{ zIndex: 1 }}
                >
                    <div className="d-flex w-100">
                        <div className="fw-bold w-50 text-start">File Name</div>
                        <div className="fw-bold w-25 text-center">LVS Failed</div>
                        <div className="fw-bold w-25 text-center">DRC Failed</div>
                        <div className="fw-bold w-50 text-center">Timestamp</div>
                        <div className="fw-bold w-25 text-center">Action</div>
                    </div>
                </li>

                {projectTechFileListData && projectTechFileListData.length > 0 ? (
                    projectTechFileListData.map((data) => (
                        <li
                            key={data?.id}
                            className={`list-group-item d-flex align-items-center py-2 border rounded mb-2 ${selectedID === data?.id
                                ? "app-primary-button-color border-0 text-white"
                                : "bg-light"
                                }`}
                            onClick={() => handleRowClick(data?.id, data?.file_name, data?.project_id)}
                            style={{ cursor: "pointer" }}
                        >
                            <div className="w-50 text-start text-truncate fw-semibold"
                                data-tooltip-id="project-techfile-name"
                                data-tooltip-content={data?.file_name}
                                data-tooltip-place="top"
                            >{data?.file_name}
                                <ReactTooltip id="project-techfile-name" style={{ whiteSpace: 'nowrap', zIndex: 9999 }} />
                            </div>
                            <div className="w-25 text-center">{data?.lvs_count}</div>
                            <div className="w-25 text-center">{data?.drc_count}</div>
                            <div className="w-50 text-center">{convertToIST(data?.created_at)}</div>
                            <div className='w-25 text-center'>
                                <Button
                                    id="edit-tech-file-name"
                                    className={`btn p-0 border-0 bg-transparent text-black me-2 ${loading ? "cursor_not_allowed" :""} ${selectedID === data?.id && "bg-white"} `}
                                    onClick={() =>handleRenameTechFile(data?.file_name)}
                                    disabled={loading}
                                    data-tooltip-id="rename-tech-file-tooltip"
                                    data-tooltip-content={"Rename"}
                                >
                                    <FontAwesomeIcon icon={faPen} className='me-2' />
                                    <ReactTooltip id="rename-tech-file-tooltip" place="top" style={{ whiteSpace: 'nowrap', zIndex: 9999 }} />
                                </Button>
                                <Button
                                    id="download-project-tech-file"
                                    className={`btn p-0 border-0 bg-transparent text-black ${loading ? "cursor_not_allowed" : ""}`}
                                    onClick={() => handleDownloadProjectTechFile(data.id, data?.project_id, data?.file_name)}
                                    disabled={loading}
                                    data-tooltip-id="download-tech-file-tooltip"
                                    data-tooltip-content={"Download"}
                                >
                                    <FontAwesomeIcon icon={faDownload} />
                                    <ReactTooltip id="download-tech-file-tooltip" place="top" style={{ whiteSpace: 'nowrap', zIndex: 9999 }} />
                                </Button>
                            </div>
                        </li>
                    ))
                ) : (
                    <div className="row">
                        <span className="text-center align-content-center pt-5">{projectTechFileListData?.message || "No project Tech File data found"}</span>
                    </div>
                )}
            </ul>
        </div>
    );
};

export default ProjectTechFileListModalBody;
