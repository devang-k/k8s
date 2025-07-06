import { useEffect ,useState} from "react";
import { toast } from "react-toastify";


import { useFilterResultsContext } from "../../components/providers/FilterResultsProvider/FilterResultsContext";


//below selectedcellnameongraph is user clicked gds item on graph or table
//userRunStage is either stage1 or stage2 indicating user is on which stage to handle cart for particular stage
const useGdsLayoutCart = (selectedCellNameOnGraph , userRunStage) => {
    const { stage1GdsCartData,setStage1GdsCartData , stage2GdsCartData,setStage2GdsCartData } = useFilterResultsContext();
    const [isGDSAddedToCart, setIsGDSAddedToCart] = useState(false);


   const handleAddOrRemoveFromCart = (prev) => {
    if (prev === null) { return [selectedCellNameOnGraph] }
    else { 
      // check if item already present if yes then remove else add it 
      if(prev.includes(selectedCellNameOnGraph)){
        // removing from filter
        return prev.filter((item) => item !== selectedCellNameOnGraph);
      }else{
        //adding to filter cart
      return [...prev, selectedCellNameOnGraph] } }
   }
   
   const handleCart = () => {
    // will add selected gds to cart stage1 cart 
    // handling addition of gds
    
    let isAdded = false;
  
    if (userRunStage === 1) {
      setStage1GdsCartData((prev) => {
        const updatedCart = handleAddOrRemoveFromCart(prev);
        // If prev is null, the item was just added, otherwise check if the item was added
        isAdded = (prev === null) || (prev && !prev.includes(selectedCellNameOnGraph));
        return updatedCart;
      });
    } else if (userRunStage === 2) {
      setStage2GdsCartData((prev) => {
        const updatedCart = handleAddOrRemoveFromCart(prev);
        // If prev is null, the item was just added, otherwise check if the item was added
        isAdded = (prev === null) || (prev && !prev.includes(selectedCellNameOnGraph));
        return updatedCart;
      });
    }
  
    // Show success message after the cart has been updated
    toast.success(`${selectedCellNameOnGraph} ${isAdded ? "added to" : "removed from"} cart successfully`, { autoClose: 2000 });
  };
  
  
    const handleClearCart = (setSelectedCellFromList, setViewCartOption) => {
      if(userRunStage=== 1){
        setStage1GdsCartData([]);
      } else if(userRunStage ===2 ){
      setStage2GdsCartData([]);
      }
      setSelectedCellFromList(null);
      setViewCartOption(false);
      toast.success("Cart cleared successfully", { autoClose: 3000 })
    }

    // below useeffect to handle stage1 & stage2 gds add to cart
    useEffect(() => {
      if (userRunStage === 1) {
        setIsGDSAddedToCart(stage1GdsCartData && stage1GdsCartData.includes(selectedCellNameOnGraph));
      } else if (userRunStage === 2) {
        setIsGDSAddedToCart(stage2GdsCartData && stage2GdsCartData.includes(selectedCellNameOnGraph));
      }
    }, [selectedCellNameOnGraph, stage1GdsCartData, stage2GdsCartData, userRunStage]);
    



    return { handleCart ,isGDSAddedToCart, handleClearCart};
};

export default useGdsLayoutCart;