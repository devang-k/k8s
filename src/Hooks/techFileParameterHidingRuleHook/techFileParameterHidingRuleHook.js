
import {useTechFileContext} from "../../components/providers/TechFileProvider/TechFileContext";


const useTechFileParameterHidingRuleHook = () => {


    const { techFileData } = useTechFileContext();
    // function that checks parameter will be hidden or not
    const shouldParameterBeHidden = (parameterValueInRow) => {
    
        if (!parameterValueInRow?.parameterHidingRule || !techFileData?.data?.FileContent) {
          return false;
        }
      
        for (const rule of parameterValueInRow.parameterHidingRule) {
          // Check if all ruleItems in this rule are matched in techFileData for hiding parameter in UI
          const allItemsMatch = rule?.every((ruleItem) => {
            return techFileData?.data?.FileContent?.some((techFileDataItem) => {
              return techFileDataItem?.data?.some((data) => 
              {
                if(data?.key?.key2){
                  return   data?.key?.key1 === ruleItem?.key1 && data?.key?.key2 === ruleItem?.key2 && data?.val === ruleItem?.keyValue
                }else{
                  return  data?.key?.key1 === ruleItem?.key1 && data?.val === ruleItem?.keyValue
               }
             }
              );
            });
          });
      
          if (allItemsMatch) {
            return true;
          }
        }
      
        return false;
      };
    return {shouldParameterBeHidden}
}

export default  useTechFileParameterHidingRuleHook;