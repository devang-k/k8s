import React, { useEffect } from "react";
import "./FilterRunResults.css";
import { faXmark } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button, Form, Row, Col, Table } from "react-bootstrap";

import { filterOperators } from "../../../constant";
import { fetchStageData } from "../../../server/server";

import { useFilterResultsContext } from "../../providers/FilterResultsProvider/FilterResultsContext";
import { useCreateProjectContext } from "../../providers/CreateProjectProvider/CreateProjectContext";
import { useStage1ResultContext } from "../../providers/Stage1ResultProvider/Stage1ResultContext";
import { useStage2ResultContext } from "../../providers/Stage2ResultProvider/Stage2ResultContext";
import { useLayoutGraphContext } from "../../providers/LayoutGraphProvider/LayoutGraphContext";

import useClearAllLevelFilter from "../../../Hooks/clearAllLevelFiltersHook/useClearAllLevelFilter";


const FilterRunResults = ({ closeFilterResultSlider, runSummaryData, filterStage }) => {

    const { handleClearAllLevelFilter } = useClearAllLevelFilter(filterStage)
    // all context goes below
    const { stage1FilterSelectedCells,
        setStage1SelectedFilterCells,
        stage1IsAllCellSelectedForFilter,
        setStage1IsAllCellSelectedForFilter,
        techVariationFilterSelectedParameter,
        setTechVariationFilterSelectedParameter,
        setFilterRequestParameter,
        setIsStage1FilterApplied,
        setIsStage2FilterApplied,
        isFilterApplied,
        setIsFilterApplied,
        stage1Level2Filter,
        stage2Level2Filter,
        stage1GraphSelectedGdsCells,
        stage2GraphSelectedGdsCells
    } = useFilterResultsContext();
    const { currentProjectId } = useCreateProjectContext();
    const { setStage1Result, stage1RunResultSummaryData, setSelectedGdsItems, setStage1GdsLayoutImageData } = useStage1ResultContext();
    const { setStage2Result, setStage2GdsLayoutImageData } = useStage2ResultContext();
    const { setStage1GraphData, setStage2GraphData } = useLayoutGraphContext();

    //To check Apply button enabled
    const applyButtonEnabled = () => {
        // Check if at least one cell is selected 
        const isStage1CellSelected = stage1FilterSelectedCells?.length > 0;

        const hasIncompleteCustomFilter = techVariationFilterSelectedParameter?.some(
            (parameter) =>
                // Only check for custom parameters
                !parameter?.selectAllValue && (
                    parameter?.filterationValue === null ||
                    parameter?.value1 === null ||
                    // For 'between' operator, ensure value2 is also filled
                    (parameter?.filterationValue === 'between' && parameter?.value2 === null)
                )
        );

        return !hasIncompleteCustomFilter && isStage1CellSelected;
    };



    //below function handles applying filter and calling result endpoint to filter searched data
    const handleApplyFilter = async () => {
        setIsFilterApplied(true);

        // Perform filter logic here
        // Call your API endpoint or perform any other necessary actions
        // create filter request here to be sent to result endpoint for fetching filtered data
        // filtered parameters sending to run endpoint , which will be used to fetch data only parameter who has custom filters applied 
        const filterParameters = techVariationFilterSelectedParameter?.filter((parameter) => parameter?.selectAllValue === false)

        const filterRequest = {

            cellSelectAll: stage1IsAllCellSelectedForFilter,
            cells: stage1FilterSelectedCells,

            filterParametersName: {
                filterLevel1: filterParameters,
                filterLevel2: filterStage === 1 ? stage1Level2Filter : filterStage === 2 ? stage2Level2Filter : null,
            }

        };

        // when level 3 filter is applied, pass the payload to the stage result. 
        const filterByLayoutReq = filterStage === 1 ? (stage1GraphSelectedGdsCells?.length > 0 && stage1GraphSelectedGdsCells) : filterStage === 2 ? (stage2GraphSelectedGdsCells?.length > 0  && stage2GraphSelectedGdsCells) : null;

        setFilterRequestParameter(filterRequest);
        // Trigger API call. stage 1 and page 0
        const stageRes = await fetchStageData(currentProjectId, filterStage, 0, filterRequest, filterByLayoutReq);
        if (filterStage === 1) {
            // setstage1 filter updated data
            setStage1Result(stageRes);
            setStage1GraphData(null);
            setIsStage1FilterApplied(true);
            // here we need to check if earlier result were genereted using cell on which filter is applied then if true will set selectedLayouts sent in results response or else we will empty selection since no gds are genereated for that 
            if (stage1FilterSelectedCells && stage1FilterSelectedCells?.length > 0) {
                // then check if that cell is included in selected layput sent in response and set value accordinlgy else
                const isSelectedCellPresentInFilter = stage1FilterSelectedCells?.some((searchCell) => stageRes?.data?.selectedLayouts?.some((item) => item?.includes(searchCell)));
                if (isSelectedCellPresentInFilter) {
                    setSelectedGdsItems(stageRes?.data?.selectedLayouts) // setting the selected layout sent by response
                } else {
                    setSelectedGdsItems([]);
                }
            } else {
                // empty gds selection
                setSelectedGdsItems([])
            }
            setStage1GdsLayoutImageData([])
        } else if (filterStage === 2) {
            setStage2Result(stageRes);
            setIsStage2FilterApplied(true);
            setStage2GraphData(null);
            setStage2GdsLayoutImageData([])
        }
        closeFilterResultSlider();
    }

    //below function helps in clearing filter 
    const handleClearFilter = async () => {
        closeNav();
        // setIsFilterApplied(false);// setting filter applied back to false since we are removing all filters
        // setFilterRequestParameter(null);// setting it to null since clearing filter
        // // Trigger API call. stage 1 and page 0
        // const stageRes = await fetchStageData(currentProjectId, filterStage, 0, null);
        // if (filterStage === 1) {
        //     // setstage1 filter updated data
        //     setStage1Result(stageRes);
        //     setIsStage1FilterApplied(true);
        //     setStage1GraphData(null);
        //     setSelectedGdsItems(stageRes?.data?.selectedLayouts)


        // } else if (filterStage === 2) {
        //     setStage2Result(stageRes);
        //     setIsStage2FilterApplied(true);
        //     setStage2GraphData(null);
        // }
        // resetting all values to default when clear filter is clicked
        // setStage1IsAllCellSelectedForFilter(true);
        handleClearAllLevelFilter();
        setStage1SelectedFilterCells(runSummaryData?.cells?.value);
        setTechVariationFilterSelectedParameter(
            runSummaryData?.variationTechParameters?.value?.map(item => ({
                parameterName1: item?.Parameter1 || null,
                parameterName2: null,
                selectAllValue: true, // Always true as per the requirement
                filterationValue: null, // Null because selectAllValue is true
                value1: null, // First value from Value array
                value2: null // Second value if it exists
            })))

    }

    useEffect(() => {
        const sidenav = document.getElementById("mySidenav");
        if (sidenav) {
            sidenav.style.width = window.innerWidth < 768 ? "100vw" : "45%";
        }
    }, []);

    //below function helps in closing filter slider
    function closeNav() {
        document.getElementById("mySidenav").style.width = "0";
        closeFilterResultSlider();
    }


    //below function handles custom cell selection checkbox , individual cell selection
    const handleCellCustomCheckboxChange = (event, cell) => {
        if (event.target.checked) {
            setStage1SelectedFilterCells([...stage1FilterSelectedCells, cell]);// adding cell to selected cell option
        } else {
            //removing cells from selected cells option
            setStage1SelectedFilterCells(stage1FilterSelectedCells?.filter((selectedCell) => selectedCell !== cell))
        }
    }

    // below function handles operator selection
    const handleOperatorChange = (paramName, value) => {
        setTechVariationFilterSelectedParameter(prev =>
            prev.map(item =>
                item.parameterName1 === paramName
                    ? { ...item, filterationValue: value }
                    : item
            )
        );
    };
    //below fucntion handles value acceptance from user for filtering
    const handleValueChange = (paramName, valueKey, value) => {
        setTechVariationFilterSelectedParameter(prev =>
            prev.map(item =>
                item.parameterName1 === paramName
                    ? { ...item, [valueKey]: Number(value) }
                    : item
            )
        );
    };


    //below functrion handles parameter custom  selection
    const handleCustomCheckboxChange = (paramName) => {
        setTechVariationFilterSelectedParameter(prev =>
            prev.map(item =>
                item.parameterName1 === paramName
                    ? { ...item, selectAllValue: false }
                    : item
            )
        );
    };

    //below fucntion handles all value selection for parameter
    const handleAllCheckboxChange = (paramName, type) => {
        setTechVariationFilterSelectedParameter(prev =>
            prev.map(item =>
                item.parameterName1 === paramName
                    ? type === "all"
                        ? { ...item, selectAllValue: true, filterationValue: null, value1: null, value2: null }
                        : { ...item, selectAllValue: false }
                    : item
            )
        );
    };


    //below function handles all checkbox selection for selecting all cells
    const handleSelectAllCellsCheckbox = (event) => {
        if (!event.target.checked) {
            // if false
            setStage1SelectedFilterCells([]);
        } else {
            // if true adding all cells 
            setStage1SelectedFilterCells(runSummaryData?.cells?.value);
        }
        setStage1IsAllCellSelectedForFilter(!stage1IsAllCellSelectedForFilter);

    }

    useEffect(() => {
        //hadnles checkboxes for cells selection 
        //check if all cells selected for filter or not 
        let summaryCells = runSummaryData?.cells?.value;
        let allCellsMatch = summaryCells.every(cell => stage1FilterSelectedCells?.includes(cell));
        if (allCellsMatch) {
            // all cell matching setting to true 
            setStage1IsAllCellSelectedForFilter(true)
        } else {
            setStage1IsAllCellSelectedForFilter(false)
        }

    }, [stage1FilterSelectedCells, setStage1IsAllCellSelectedForFilter, runSummaryData])

    useEffect(() => {
        //setting the value for tech filter parameter in filter context to be used in filter component for filtering results
        //since using summary Data in results sumary it is automatically going to handle which data to be used at which time
        //setting default type for all parameters in filter

        // using always stage1 summary data for filter since filter is to be carried forwarded
        setStage1SelectedFilterCells(isFilterApplied ? stage1FilterSelectedCells : stage1RunResultSummaryData?.data?.cells?.value);
        setTechVariationFilterSelectedParameter(
            isFilterApplied ? techVariationFilterSelectedParameter :
                stage1RunResultSummaryData?.data?.variationTechParameters?.value?.map(item => ({
                    parameterName1: Array.isArray(item?.Parameter1) ? item?.Parameter1[0] || null :  item?.Parameter1 || null,
                    parameterName2:  null,
                    selectAllValue: true, // Always true as per the requirement
                    filterationValue: null, // Null because selectAllValue is true
                    value1: null, // First value from Value array
                    value2: null // Second value if it exists

                })))
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [
        isFilterApplied, stage1RunResultSummaryData, setTechVariationFilterSelectedParameter, setStage1IsAllCellSelectedForFilter, setStage1SelectedFilterCells]);
    // rendering of data happens from the value received in props and filter values selected are used from context values
    return (
        <>
            {/* below div to make background blur */}
            <div
                className="overlay"
            />
            <div id="mySidenav" className="sidenav">
                {/* Header */}
                <div className="header d-flex justify-content-between align-items-center">
                    <span className="fw-bold">Select Filters (Filter Run Results)</span>
                    <button onClick={(e) => { e.preventDefault(); closeNav(); }} style={{
                        background: "none",
                        border: "none",
                        fontSize: "20px",
                        fontWeight: "bold",
                        cursor: "pointer"
                    }} id="filter-close-icon">
                        <FontAwesomeIcon icon={faXmark} style={{ fontSize: "20px" }} />
                    </button>
                </div>

                {/* Cells Section (Scrollable) */}
                <h6 className="fw-bold p-2">Cells</h6>
                <div className="cells-section mt-0">
                    <Row className="align-items-center border-bottom pb-2">
                        <Col md={3}>
                            <Form.Check
                                id="filter-selectAll-cell-checkbox"
                                type="checkbox"
                                checked={stage1IsAllCellSelectedForFilter}
                                onChange={(e) => handleSelectAllCellsCheckbox(e)}
                                label={"All"}
                            />
                        </Col>
                        <Col md={9} className="d-flex flex-wrap gap-2  scrollable-section">
                            {runSummaryData?.cells?.value?.map((cell) => (
                                <Form.Check
                                    id={`filter-selectcell-checkbox-${cell}`}
                                    key={cell}
                                    type="checkbox"
                                    label={cell}
                                    value={cell}
                                    checked={stage1IsAllCellSelectedForFilter ? true : stage1FilterSelectedCells?.includes(cell)}
                                    onChange={(e) => handleCellCustomCheckboxChange(e, cell)} // Handle checkbox selection
                                />))}
                        </Col>
                    </Row>
                </div>

                {/* Scrollable Tech Parameters Section */}
                {techVariationFilterSelectedParameter && techVariationFilterSelectedParameter?.length > 0 && (

                    <>
                        <h6 className="fw-bold p-2">Tech Parameters</h6>
                        <div className="tech-parameters-container">
                            <div className="border rounded shadow-sm p-3">
                                {/* {runSummaryData?.variationTechParameters?.value?.map((parameter, index) => { */}
                                {techVariationFilterSelectedParameter?.map((parameter, index) => {
                                    //getting selected value from techvariation selected value to with current value
                                    const selectedTechVariationValue = runSummaryData?.variationTechParameters?.value?.find(sel => {
                                        if (Array.isArray(sel?.Parameter1)) {
                                            return sel?.Parameter1?.includes(parameter?.parameterName1);
                                        }
                                        return sel?.Parameter1 === parameter?.parameterName1;
                                    }) || {};

                                    return (
                                        <Row key={index} className="mb-3 align-items-center border-bottom pb-3">
                                            {Array.isArray(parameter?.parameterName1) ? (
                                                parameter?.parameterName1[0] === parameter?.parameterName1[1] ? (
                                                    <Col md={3} className="fw-bold">{parameter?.parameterName1[0]}</Col>
                                                ) : (
                                                    <Col md={3} className="fw-bold">{parameter?.parameterName1.join(', ')}</Col>
                                                )
                                            ) : (
                                                <Col md={3} className="fw-bold">{parameter?.parameterName1}</Col>
                                            )}
                                            {/* <Col md={3} className="fw-bold"> {parameter?.parameterName1}</Col> */}
                                            <Col md={9}>
                                                <Row>
                                                    <Col md={5} className="d-flex flex-column gap-2">
                                                        <Form.Check type="checkbox"
                                                            checked={parameter?.selectAllValue} label="All"
                                                            onChange={() => handleAllCheckboxChange(parameter?.parameterName1, "all")}
                                                            id="filter-parameter-selectAll-checkbox"
                                                        />
                                                        <Table bordered size="sm">
                                                            <tbody>
                                                                <tr><td>Start:</td><td>{selectedTechVariationValue?.Start}</td></tr>
                                                                <tr><td>End:</td><td>{selectedTechVariationValue?.End}</td></tr>
                                                                <tr><td>Step:</td><td>{selectedTechVariationValue?.Step}</td></tr>
                                                            </tbody>
                                                        </Table>
                                                    </Col>
                                                    <Col md={7} className="d-flex flex-column gap-2">
                                                        <Form.Check type="checkbox" label="Custom" checked={!parameter?.selectAllValue}
                                                            onChange={() => handleCustomCheckboxChange(parameter?.parameterName1)}
                                                            id="filter-parameter-custom-selection-checkbox"
                                                        />

                                                        <Form.Select disabled={parameter?.selectAllValue}
                                                            value={parameter.filterationValue || ""}
                                                            onChange={(e) => handleOperatorChange(parameter?.parameterName1, e.target.value)}
                                                            id="filter-parameter-operator-dropdown"
                                                            className="form-select-custom"
                                                        >
                                                            <option value="">Select Operator</option>
                                                            {filterOperators?.map((op) => (
                                                                <option id={`filter-operator-selection-${op}`} className="form-option-select-custom" style={{ cursor: "pointer" }} key={op} value={op}>{op}</option>
                                                            ))}
                                                        </Form.Select>
                                                        <Form.Control min={selectedTechVariationValue?.Start} max={selectedTechVariationValue?.End} type="number" placeholder="Enter Value" disabled={parameter?.selectAllValue}
                                                            value={(parameter?.value1)?.toString() || ""}
                                                            onChange={(e) => handleValueChange(parameter?.parameterName1, "value1", e.target.value)}
                                                            id="filter-option-value1"
                                                            className="form-select-custom"
                                                        />
                                                        {parameter?.filterationValue === "between" && (
                                                            <Form.Control min={selectedTechVariationValue?.Start} max={selectedTechVariationValue?.End} type="number" placeholder="Enter Value" disabled={parameter?.selectAllValue}
                                                                value={(parameter?.value2)?.toString() || ""}
                                                                onChange={(e) => handleValueChange(parameter?.parameterName1, "value2", e.target.value)}
                                                                id="filter-option-value2"
                                                                className="form-select-custom"
                                                            />
                                                        )}
                                                    </Col>
                                                </Row>
                                            </Col>
                                        </Row>
                                    )
                                })}
                            </div>
                        </div>
                    </>

                )}
                {/* Button Container (Fixed) */}
                <div className="button-container d-flex justify-content-end gap-2 position-absolute bottom-0 w-100">
                    <Button className="app-secondary-button-color border-0 w-25" onClick={(e) => { e.preventDefault(); closeNav(); }} >Close</Button>
                    <Button
                        className={applyButtonEnabled() ? 'app-primary-button-color border-0 w-25' : 'app-secondary-button-color border-0 w-25 cursor_not_allowed'}
                        disabled={!applyButtonEnabled()}
                        onClick={handleApplyFilter}
                    >
                        Apply
                    </Button>
                    <Button className={!isFilterApplied ? 'app-secondary-button-color border-0 w-25 cursor_not_allowed' : 'app-primary-button-color border-0 w-25'} disabled={!isFilterApplied} onClick={handleClearFilter}>Clear Filters</Button>
                </div>
            </div>
        </>
    );
};

export default FilterRunResults;
