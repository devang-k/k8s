import React from 'react'

const DeleteProjectModalBody = ({selectedFileNameFromListOfSavedProject}) => {
  return (
    <div>
      <h6>Are you sure you want to delete {selectedFileNameFromListOfSavedProject}?</h6>  
    </div>
  )
}

export default DeleteProjectModalBody