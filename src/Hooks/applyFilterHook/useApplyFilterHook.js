import { fetchStageData } from "../../server/server";

import { useFilterResultsContext } from "../../components/providers/FilterResultsProvider/FilterResultsContext";
import { useCreateProjectContext } from "../../components/providers/CreateProjectProvider/CreateProjectContext";
import { useStage1ResultContext } from "../../components/providers/Stage1ResultProvider/Stage1ResultContext";
import { useStage2ResultContext } from "../../components/providers/Stage2ResultProvider/Stage2ResultContext";
import { useLayoutGraphContext } from "../../components/providers/LayoutGraphProvider/LayoutGraphContext";

const useApplyFilterHook = (filterStage) => {

     // all context goes below
        const { 
            filterRequestParameter,
            setIsStage1Level2FilterApplied,
            stage1FilterSelectedCells,
            setIsStage2Level2FilterApplied,
            stage1GraphSelectedGdsCells,
            stage2GraphSelectedGdsCells
        } = useFilterResultsContext();
        const { currentProjectId } = useCreateProjectContext();
        const { setStage1Result , setSelectedGdsItems} = useStage1ResultContext();
        const { setStage2Result } = useStage2ResultContext();
        const { setStage1GraphData, setStage2GraphData } = useLayoutGraphContext();

         // apply filter handle to sync level2 filter data across tabs on stage1
          const handleApplyFilterStage1 = async () => {
            
            // Perform filter logic here
            // Call your API endpoint or perform any other necessary actions
            // create filter request here to be sent to result endpoint for fetching filtered data
            // filtered parameters sending to run endpoint , which will be used to fetch data only parameter who has custom filters applied 
        
            // If 'cellSelectAll' is enabled in the filter request, keep the selected GDS cells; otherwise, reset to null.
            const updatedStage1GraphSelectedGdsCells = ( filterRequestParameter?.cellSelectAll || filterRequestParameter?.cells)
                ? stage1GraphSelectedGdsCells 
                : null;
            
            // If there are selected GDS cells, reset the filter request parameter to null; otherwise, keep it unchanged.
            const updatedFilterRequestParameter = stage1GraphSelectedGdsCells === null 
                ? filterRequestParameter 
                : null;
        
            // Trigger API call. stage 1 and page 0
            const stageRes = await fetchStageData(currentProjectId, 1, 0, updatedFilterRequestParameter, updatedStage1GraphSelectedGdsCells);
            // if (filterStage === 1) {
                // setstage1 filter updated data
                setStage1Result(stageRes);
                setStage1GraphData(null);
                setIsStage1Level2FilterApplied(true);
                //setIsStage1FilterApplied(true);
                // here we need to check if earlier result were genereted using cell on which filter is applied then if true will set selectedLayouts sent in results response or else we will empty selection since no gds are genereated for that 
                if(stage1FilterSelectedCells && stage1FilterSelectedCells?.length >0 ){
                    // then check if that cell is included in selected layput sent in response and set value accordinlgy else
                    const isSelectedCellPresentInFilter = stage1FilterSelectedCells?.some((searchCell)=> stageRes?.data?.selectedLayouts?.some((item)=> item?.includes(searchCell)));
                    if(isSelectedCellPresentInFilter){
                    setSelectedGdsItems(stageRes?.data?.selectedLayouts) // setting the selected layout sent by response
                    }else{
                        setSelectedGdsItems([]);
                    }
                }else{
                    // empty gds selection
                setSelectedGdsItems([])
                }
        }

        // apply filter handle to sync level2 filter data across tabs on stage2
        const handleApplyFilterStage2 = async () => {
        
            // Perform filter logic here
            // Call your API endpoint or perform any other necessary actions
            // create filter request here to be sent to result endpoint for fetching filtered data
            // filtered parameters sending to run endpoint , which will be used to fetch data only parameter who has custom filters applied 
        
            // If 'cellSelectAll' is enabled in the filter request, keep the selected GDS cells; otherwise, reset to null.
            const updatedStage2GraphSelectedGdsCells = (filterRequestParameter?.cellSelectAll || filterRequestParameter?.cells) 
                ? stage2GraphSelectedGdsCells 
                : null;
            // If there are selected GDS cells, reset the filter request parameter to null; otherwise, keep it unchanged.
            const updatedFilterRequestParameter = stage2GraphSelectedGdsCells === null 
                ? filterRequestParameter 
                : null;
         
            // Trigger API call. stage 2 and page 0
            const stageRes = await fetchStageData(currentProjectId, 2, 0, updatedFilterRequestParameter, updatedStage2GraphSelectedGdsCells);
            setStage2Result(stageRes);
            setStage2GraphData(null);
            setIsStage2Level2FilterApplied(true);
          }
    return {handleApplyFilterStage1,handleApplyFilterStage2};
}

export default useApplyFilterHook;