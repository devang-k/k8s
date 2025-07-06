import React from 'react'

const SaveAdminNetlistFileModalBody = ({ adminNetlistFileName, setAdminNetlistFileName, renameNetlistFileErrorMessage }) => {
  return (
    <div className="d-flex align-items-center flex-column w-100">
      <div className='d-flex align-items-center mb-2 w-100'>
        <input
          type="text"
          id="edit-netlist-file-name"
          value={adminNetlistFileName}
          onChange={(e) => setAdminNetlistFileName(e.target.value)}
          placeholder="Enter file name"
          className="form-control"
          style={{ width: '100%' }}
        />
        <span className="ms-2">.spice</span>
      </div>
      {renameNetlistFileErrorMessage?.status_code === 400 &&
        (
          <span className=' text-danger'>{renameNetlistFileErrorMessage?.message}</span>
        )
      }
    </div>
  )
}

export default SaveAdminNetlistFileModalBody