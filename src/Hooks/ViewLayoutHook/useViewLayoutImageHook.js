import { useCallback } from "react";
import { fetchImageData } from "../../server/server";

const useViewLayoutImageHook = ({selectedCellNameOnGraph, selectedLayoutData, setViewLayoutLoading, viewLayoutLoading}) => {
  // Function to fetch image data
  const getImageData = useCallback(async () => {
    if (viewLayoutLoading) return; // Prevent fetching if already loading

    setViewLayoutLoading(true); // Set loading state to true
    try {
      const imageData = await fetchImageData(selectedLayoutData); // Fetching image from S3
      if (imageData?.status && imageData?.status_code === 200) {
        const selectedGDSOnGraph = imageData?.images[0]?.encodedImage; // Extract encoded image

        const newTab = window.open(); // Open a new tab to display the image
        if (newTab) {
          newTab.document.body.innerHTML = `
            <div style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 90vh; text-align: center;">
              <h2>${selectedCellNameOnGraph}</h2>
              <img src="data:image/png;base64,${selectedGDSOnGraph}" alt="${selectedCellNameOnGraph}" style="width: 100%; height: 100%; object-fit: contain;" />
            </div>
          `;
          
          // Set the title of the new tab
          newTab.document.title = selectedCellNameOnGraph;
        }
      }
    } catch (error) {
      console.error("Error fetching images:", error);
    } finally {
      setViewLayoutLoading(false); // Set loading to false once done
    }
  }, [setViewLayoutLoading, viewLayoutLoading, selectedCellNameOnGraph, selectedLayoutData]);

  return {getImageData};
};

export default useViewLayoutImageHook;
