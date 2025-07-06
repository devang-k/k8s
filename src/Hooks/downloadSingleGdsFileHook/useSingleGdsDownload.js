import { downloadSingleGDSImage } from '../../server/server';
import { toast } from 'react-toastify';

const useSingleGdsDownload = () => {

    // the below hook handles the download for single GDS File.
    const downloadGDSFile = async (selectedGdsName, projectId ,setContextMenu, userCurrentStage ) => {
        if (selectedGdsName && projectId) {
            const selectedGDS = [selectedGdsName];
            const stage1GDSImageDownloadReq = {
                stage: userCurrentStage,
                projectId: projectId,
                fileList: selectedGDS,
            };

            try {
                const stage1GDSImageDownloadRes = await downloadSingleGDSImage(stage1GDSImageDownloadReq);
                if (stage1GDSImageDownloadRes?.status === 200) {
                    const blob = new Blob([stage1GDSImageDownloadRes?.data], { type: 'application/zip' });
                    const url = window.URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = url;

                    // Extract filename from headers or set a default
                    const contentDisposition = stage1GDSImageDownloadRes?.headers["x-filename"];
                    let fileName = 'download.zip'; // Default filename

                    if (contentDisposition) {
                        const fileNameMatch = contentDisposition.match(/filename="(.+)"/);
                        if (fileNameMatch && fileNameMatch[1]) {
                            fileName = fileNameMatch[1];
                        } else {
                            fileName = contentDisposition;
                        }
                    }

                    // Set the filename for the download
                    link.download = fileName;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    window.URL.revokeObjectURL(url);
                    setContextMenu(false);
                    toast.success("GDS downloaded successfully", { autoClose: 10000 });
                }
            } catch (error) {
                console.error('Error downloading GDS image:', error);
            }
        }
    }
  return {downloadGDSFile}
}

export default useSingleGdsDownload