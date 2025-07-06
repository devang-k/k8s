import React from 'react';

const SaveTechFieModalBody = ({ setNewTechFileName, newTechFileName, renameTechFileErrorMessage}) => {

  return (
    <div className="d-flex align-items-center flex-column w-100">
      <div className='d-flex align-items-center mb-2 w-100'>
      <input
        type="text"
        id="edit-tech-file-name"
        value={newTechFileName}
        onChange={(e) => setNewTechFileName(e.target.value)}
        placeholder="Enter file name"
        className="form-control"
        style={{ width: '100%' }}
      />
      <span className="ms-2">.tech</span>
      </div>
      {renameTechFileErrorMessage?.status_code === 400 &&
        (
          <span className=' text-danger'>{renameTechFileErrorMessage?.message}</span>
        )
      }
    </div>
  );
};

export default SaveTechFieModalBody;
