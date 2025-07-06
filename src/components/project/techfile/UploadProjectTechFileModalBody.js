import React from 'react';

const UploadProjectTechFileModalBody = ({ handleLoadTechFileChange, handleUploadOnProjectTechfile }) => {
    return (
        <div>
            <form id="upload-tech-file-form" onSubmit={handleUploadOnProjectTechfile}>
                <input
                    type="file"
                    id="user-tech-file"
                    name="tech-file-name"
                    onChange={handleLoadTechFileChange}
                    className="w-100"
                    accept='.tech'
                />
            </form>

        </div>
    );
};

export default UploadProjectTechFileModalBody;
