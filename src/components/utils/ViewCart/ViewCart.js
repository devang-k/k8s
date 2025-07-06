import React, { useEffect } from 'react';
import "./ViewCart.css";
import useGdsLayoutCart from '../../../Hooks/gdsLayoutCartHook/useGdsLayoutCart';
import { faXmark, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button } from 'react-bootstrap';
import { useFilterResultsContext } from '../../providers/FilterResultsProvider/FilterResultsContext';

const ViewCart = ({ setViewCartOption, viewCartOption, selectedCellFromList, setSelectedCellFromList, setDownloadResultModal, userCurrentStage, stageGdsCartData}) => {

const {setSelectedDownloadOption } = useFilterResultsContext();

  const {handleCart, handleClearCart} = useGdsLayoutCart(selectedCellFromList,userCurrentStage)

   
  
  // below function handles removing the cell from list
    const handleDeleteCellFromCart = (item) => {
        setSelectedCellFromList(item);
    }

    // below function open the download modal
    const handleDownloadCart = () => {
        setSelectedDownloadOption(1);// making cart radio button selected default
        setDownloadResultModal(true);
    }

    // below useState close the view cart side bar if there is no data
    useEffect(() => {
        if (stageGdsCartData?.length === 0) {   
            setViewCartOption(false);
        }
    })

    // below function is refreshed when the cell is removed.
    useEffect(() => {
        if (selectedCellFromList) {
            handleCart();
            setSelectedCellFromList(null);
        }
    }, [selectedCellFromList, handleCart, setSelectedCellFromList]);

    return (
        <>
                <div
                    className="overlay"
                />
            <div id="mySidenav" className="sidenavbar">
                {/* Header */}
                <div className="header d-flex justify-content-between align-items-center">
                    <span className="fw-bold">View Cart</span>
                    <button onClick={() => setViewCartOption(false)} style={{
                        background: "none",
                        border: "none",
                        fontSize: "20px",
                        fontWeight: "bold",
                        cursor: "pointer"
                    }} id="view-cart-close-icon">
                        <FontAwesomeIcon icon={faXmark} style={{ fontSize: "20px" }} />
                    </button>
                </div>

                {/* list of cells added in cart */}    
                <div className="cart-items-list mt-2 mb-1 overflow-y-auto">
                    {(stageGdsCartData  && stageGdsCartData?.length > 0) && stageGdsCartData?.map((item) => (
                        <div
                            key={item}
                            className="cart-item d-flex justify-content-between align-items-center"
                        >
                            <span>{item}</span>
                            <button
                                id="remove-cell-name-from-list"
                                onClick={() => handleDeleteCellFromCart(item)}
                                style={{
                                    background: "none",
                                    border: "none",
                                    cursor: "pointer",
                                    padding: "5px",
                                    marginLeft: "10px"
                                }}
                            >
                                <FontAwesomeIcon icon={faTrash} style={{ fontSize: "15px", color: "#534d4d" }} />
                            </button>
                        </div>
                    ))}
                </div>

                {/* Bottom buttons */}
                <div className="button-container d-flex justify-content-end gap-2 position-absolute bottom-0 w-100">
                    <Button className="app-primary-button-color border-0 w-25" id="view-cart-download-button" onClick={handleDownloadCart}>Download</Button>
                    <Button className="app-primary-button-color border-0 w-25" id="view-cart-clear-button" onClick={() => handleClearCart(setSelectedCellFromList, setViewCartOption)}>Clear Cart</Button>
                    <Button className="app-primary-button-color border-0 w-25" id="view-cart-cancel-button" onClick={()=>setViewCartOption(false)}>Cancel</Button>
                </div>
            </div>
        </>
    );
};

export default ViewCart;