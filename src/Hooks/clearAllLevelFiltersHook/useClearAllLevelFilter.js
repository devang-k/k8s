import { fetchStageData } from "../../server/server";

import { useFilterResultsContext } from "../../components/providers/FilterResultsProvider/FilterResultsContext";
import { useCreateProjectContext } from "../../components/providers/CreateProjectProvider/CreateProjectContext";
import { useStage1ResultContext } from "../../components/providers/Stage1ResultProvider/Stage1ResultContext";
import { useStage2ResultContext } from "../../components/providers/Stage2ResultProvider/Stage2ResultContext";
import { useLayoutGraphContext } from "../../components/providers/LayoutGraphProvider/LayoutGraphContext";

const useClearAllLevelFilter = (filterStage) => {

     // all context goes below
        const { 
            setStage1IsAllCellSelectedForFilter,
            setFilterRequestParameter,
            setIsStage1FilterApplied,
            setIsStage2FilterApplied,          
            setIsFilterApplied,        
            setStage1Level2Filter,
            setStage2Level2Filter,
            setStage1GraphSelectedGdsCells,
            setStage2GraphSelectedGdsCells,
            setStage1TotalPexDataFilters,
            setStage2TotalPexDataFilters,
        } = useFilterResultsContext();
        const { currentProjectId } = useCreateProjectContext();
        const { setStage1Result , setSelectedGdsItems, setStage1GdsLayoutImageData} = useStage1ResultContext();
        const { setStage2Result, setStage2GdsLayoutImageData } = useStage2ResultContext();
        const { setStage1GraphData, setStage2GraphData } = useLayoutGraphContext();

      const handleClearAllLevelFilter = async (action) => {
       
            setIsFilterApplied(false);// setting filter applied back to false since we are removing all filters
            setFilterRequestParameter(null);// setting it to null since clearing filter
            // Trigger API call. stage 1 and page 0
            const stageRes = await fetchStageData(currentProjectId, filterStage, 0, null);
            let stage2Res;
            if(action && action === 3){
                stage2Res = await fetchStageData(currentProjectId,2,0,null);
            }
            // incase of action3  & user has hyper result as well making sure both button are visible to user 
            if(filterStage === 1 && action === 3){
                setStage2Result(stage2Res);
                setIsStage2FilterApplied(true);
                setStage2GraphData(null);
                setStage2GraphSelectedGdsCells(null);
                setStage2Level2Filter([]);
                setStage2GdsLayoutImageData([]);
                setStage2TotalPexDataFilters({})
            }
            if (filterStage === 1) {
                // setstage1 filter updated data
                setStage1Result(stageRes);
                setIsStage1FilterApplied(true);
                setStage1GraphData(null);
                setSelectedGdsItems(stageRes?.data?.selectedLayouts);
                setStage1GraphSelectedGdsCells(null);
                setStage1Level2Filter([]);
                setStage1GdsLayoutImageData([]);
                setStage1TotalPexDataFilters({})
            } else if (filterStage === 2) {
                setStage2Result(stageRes);
                setIsStage2FilterApplied(true);
                setStage2GraphData(null);
                setStage2GraphSelectedGdsCells(null);
                setStage2Level2Filter([]);
                setStage2GdsLayoutImageData([]);
                setStage2TotalPexDataFilters({})
            }
            // resetting all values to default when clear filter is clicked
            setStage1IsAllCellSelectedForFilter(true);
          
    
        }

    return {handleClearAllLevelFilter};
}

export default useClearAllLevelFilter;