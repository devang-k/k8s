import { useCallback, useMemo } from "react";
import { useFilterResultsContext } from "../../components/providers/FilterResultsProvider/FilterResultsContext";
import { useStage2ResultContext } from "../../components/providers/Stage2ResultProvider/Stage2ResultContext";


const useGetTableFilterData = (data = [], filters = []) => {

    const {setStage1FilteredLevel2Cells,setStage2FilteredLevel2Cells} = useFilterResultsContext();
    const {isUserOnStage2Page} = useStage2ResultContext();

    // Function to filter data based on filters
    const getFilteredData = useCallback((inputData, inputFilters) => {
        if (!Array.isArray(inputFilters) || inputFilters.length === 0) {
            return inputData;
        }

        const filteredLevel2Data =  inputData.filter(row =>
            inputFilters.every(({ parameterName1, filterationValue, value1, value2 }) => {
                const value = row?.[parameterName1]; // Optional chaining to prevent errors if the key is missing

                if (value === undefined) return false;

                if (filterationValue === "between") {
                    return value >= value1 && value <= value2;
                }
                
                return true;
            })
        );

        //  assign filtered cells 
        const filteredLevel2FilteredCells = [...new Set(filteredLevel2Data?.map((filterData) => {
            
                const cellName = filterData.File.split('_')[0]; // Split the 'File' value and get the first part
                return cellName; // Return the cell name (this will be truthy, so the filter will keep the item)
        }))];
        
        if(!isUserOnStage2Page){
            // set stage1 filtered cells
            setStage1FilteredLevel2Cells(filteredLevel2FilteredCells);    
        }else{
            // set stage2 filtered cells
            setStage2FilteredLevel2Cells(filteredLevel2FilteredCells);
        }
            
        return filteredLevel2Data;
    },[setStage1FilteredLevel2Cells,isUserOnStage2Page,setStage2FilteredLevel2Cells]);

    // Memoized filtered data
    const filteredData = useMemo(() => getFilteredData(data, filters), [data, filters,getFilteredData]);

    return { filteredData };
};

export default useGetTableFilterData;
