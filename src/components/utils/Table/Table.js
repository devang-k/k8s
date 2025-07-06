
/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: Table.js  
 * Description: This file defines a reusable React component for displaying Tables. 
 *  
 * Author: [Author's Name]  
 * Created On: [Creation Date]  
 *  
 * Revision History:  
 * - [Date] [Modifier's Name]: [JIRA Id]:[Summary of changes made]  
 *  
 * This source code and associated materials are the property of SiClarity, Inc.  
 * Unauthorized copying, modification, distribution, or use of this software,  
 * in whole or in part, is strictly prohibited without prior written permission  
 * from SiClarity, Inc.  
 *  
 * Disclaimer:  
 * This software is provided "as is," without any express or implied warranties,  
 * including but not limited to warranties of merchantability, fitness for a  
 * particular purpose, or non-infringement. In no event shall SiClarity, Inc.  
 * be held liable for any damages arising from the use of this software.  
 *  
 * SiClarity and its logo are trademarks of SiClarity, Inc.  
 *  
 * For inquiries, contact: support@siclarity.com  
 ***************************************************************************/

import React, { useState, useCallback, useEffect } from "react";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import { FilterMatchMode, FilterOperator } from "primereact/api";
import { InputText } from "primereact/inputtext";
import { Button } from "primereact/button";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faFilterCircleXmark } from "@fortawesome/free-solid-svg-icons";
import "primereact/resources/themes/lara-light-blue/theme.css";
import "./Table.css";
import { useFilterResultsContext } from "../../providers/FilterResultsProvider/FilterResultsContext";
import { useStage2ResultContext } from "../../providers/Stage2ResultProvider/Stage2ResultContext";

const Table = ({
    data = [],
    columns = [],
    pagination = true,
    rowsPerPage = 10,
    rowsPerPageOptions = [10, 20, 50, 100],
    resizable = true,
    reorderable = true,
    striped = false,
    size = "small",
    filterDisplay = "menu",
    emptyMessage = "No records found",
    clearFilter = () => {},
    saveFiltersInContext = false // New prop to control saving filters in context
}) => {
    const { 
        stage1TotalPexDataFilters, 
        setStage1TotalPexDataFilters, 
        stage2TotalPexDataFilters, 
        setStage2TotalPexDataFilters, 
        isGraphFilterCleared,
        setIsGraphFilterCleared
    } = useFilterResultsContext();
    
    const { isUserOnStage2Page } = useStage2ResultContext();
    const [globalFilterValue, setGlobalFilterValue] = useState("");
    const [localFilters, setLocalFilters] = useState(null); // Local state for filters when not using context

    // It generates default filter settings based on the columns and the first row of data.
    const initFilters = useCallback(() => ({
        global: { value: null, matchMode: FilterMatchMode.CONTAINS },
        ...columns.reduce((acc, col) => {
            const field = col.field || col;
            acc[field] = {
                operator: FilterOperator.AND,
                constraints: [{
                    value: null,
                    matchMode: typeof data[0]?.[field] === "number" ? FilterMatchMode.EQUALS : FilterMatchMode.STARTS_WITH
                }]
            };
            return acc;
        }, {})
    }), [columns, data]);

    useEffect(() => {
        // it sets default table filter settings on initial run.
        if (!isGraphFilterCleared) {
            if (saveFiltersInContext) {
                if (isUserOnStage2Page) {
                    setStage2TotalPexDataFilters(prevFilters => {                    
                        // Check if prevFilters is null, undefined, or has only the "global" key or 1 key
                        const isOnlyGlobalKey = prevFilters && Object.keys(prevFilters).length === 1 && 'global' in prevFilters;
                    
                        // If prevFilters is valid and either has only 1 key (global), or is an empty object, initialize default filters
                        return (isOnlyGlobalKey || !prevFilters || Object.keys(prevFilters).length === 0) 
                            ? initFilters() 
                            : prevFilters;
                    });  
                } else {
                    setStage1TotalPexDataFilters(prevFilters => {
                        // Check if prevFilters is null, undefined, or has only the "global" key or 1 key
                        const isOnlyGlobalKey = prevFilters && Object.keys(prevFilters).length === 1 && 'global' in prevFilters;
                    
                        // If prevFilters is valid and either has only 1 key (global), or is an empty object, initialize default filters
                        return (isOnlyGlobalKey || !prevFilters || Object.keys(prevFilters).length === 0) 
                            ? initFilters() 
                            : prevFilters;
                    });                    
                }
            } else {
                // we are not saving filters in context setting default table filter settings
                setLocalFilters(initFilters());
            }
        }
        // it triggers when graph filter reset is clicked.
        // If `isGraphFilterCleared` is true, reset the filters in table and graph both
        else {
            // Handle reset logic
            if (saveFiltersInContext) {
                if (isUserOnStage2Page) {
                    // Save and reset stage 2 total pex table data filters
                    setStage2TotalPexDataFilters(initFilters());
                } else {
                    // Save and reset stage 1 total pex table data filters
                    setStage1TotalPexDataFilters(initFilters());
                }
            } else {
                setLocalFilters(initFilters()); // Use local state if not saving in context
            }
            setIsGraphFilterCleared(false); // Reset graph filter cleared state
        }
    }, [
        isGraphFilterCleared,          // Triggers on isGraphFilterCleared change
        saveFiltersInContext,          // Triggers on context change
        isUserOnStage2Page,            // Triggers if the user is on stage 2 page
        initFilters,                   // Triggers if initFilters change
        setStage1TotalPexDataFilters,  // Dependency for stage 1 filters
        setStage2TotalPexDataFilters,  // Dependency for stage 2 filters
        setLocalFilters,               // Dependency for local filters
        setIsGraphFilterCleared       // Ensures reset happens correctly
    ]);

    const onGlobalFilterChange = (e) => {
        // updated global values to filters. 
        const value = e.target.value;
        setGlobalFilterValue(value);
    
        if (saveFiltersInContext) {
            if (isUserOnStage2Page) {
                setStage2TotalPexDataFilters(prevFilters => ({
                    ...prevFilters,
                    global: { value, matchMode: FilterMatchMode.CONTAINS }
                }));
            } else {
                setStage1TotalPexDataFilters(prevFilters => ({
                    ...prevFilters,
                    global: { value, matchMode: FilterMatchMode.CONTAINS }
                }));
            }
        } else {
            setLocalFilters(prevFilters => ({
                ...prevFilters,
                global: { value, matchMode: FilterMatchMode.CONTAINS }
            }));
        }
    };

    const clear = () => {
        setGlobalFilterValue(""); // Reset global filter input
        if (saveFiltersInContext) {
            if (isUserOnStage2Page) {
                setStage2TotalPexDataFilters(initFilters());
            } else {
                setStage1TotalPexDataFilters(initFilters());
            }
        } else {
            setLocalFilters(initFilters());
        }
        setIsGraphFilterCleared(false);
        clearFilter();
    };

    const renderHeader = (
        <div className="flex justify-content-between align-items-center gap-3 p-0">
            <Button
                type="button"
                icon={<FontAwesomeIcon className="me-2" icon={faFilterCircleXmark} />}
                label="Clear Filters"
                outlined
                onClick={clear}
                className="clear-filter-button p-button-sm p-button-secondary"
            />
            <InputText
                value={globalFilterValue}
                onChange={onGlobalFilterChange}
                placeholder="Keyword Search"
                className="global-search-input w-full float-end"
            />
        </div>
    );



    const totalPexDataFilters = saveFiltersInContext
        ? isUserOnStage2Page 
            ? stage2TotalPexDataFilters 
            : stage1TotalPexDataFilters
        : localFilters;

    // Custom sort function for mixed data types (RunSummery Value column)
    const customSortFunction = (field) => ({ data, order }) => {
        // Define priority order for different data types
        const typePriority = new Map([["number", 1], ["boolean", 2], ["string", 3]]);

        return data?.sort((a, b) => {
            const valueA = a[field];
            const valueB = b[field];

            //extract numeric part from a string if it contains a number
            const extractNumeric = (val) =>
                typeof val === "string" ? parseFloat(val?.match(/^(\d+(\.\d+)?)\s?/)?.[1]) || val : val;

            // Extract number if available
            const numericA = extractNumeric(valueA);
            const numericB = extractNumeric(valueB);

            const typeA = typeof numericA;
            const typeB = typeof numericB;

            // Different types: sort by predefined priority
            if (typeA !== typeB) return (typePriority?.get(typeA) - typePriority?.get(typeB)) * order;
            if (typeA === "number") return (numericA - numericB) * order;
            if (typeA === "boolean") return (valueA === valueB ? 0 : valueA ? 1 : -1) * order;
            return String(valueA)?.localeCompare(String(valueB)) * order; // Ensure string comparison
        });
    };


    const formattedColumns = columns.map(col => {
        return {
            field: col,
            header: col,
            sortable: col === "LayoutGDS" ? false : true, // Set to false if column is "LayoutGDS"
            filter: col === "LayoutGDS" ? false : true, // Set to false if column is "LayoutGDS"
            style: col === "LayoutGDS" ? { minWidth: "180px", maxWidth: "180px" } : { minWidth: "180px" },
            //custom sort function for RunSummary(value column)
            ...(col === "Value" ? { sortFunction: customSortFunction("Value") } : {})
        };
    });
        

     // Reorder "LayoutGDS" Column to the second position
     const layoutIndex = formattedColumns?.findIndex(col => col.field === "LayoutGDS");
     if (layoutIndex > -1) {
         const [layoutColumn] = formattedColumns.splice(layoutIndex, 1);
         formattedColumns.splice(1, 0, layoutColumn);
     }
     

     const onFilterHandler = useCallback((e) => {
        if (saveFiltersInContext) {
            if (isUserOnStage2Page) {
                setStage2TotalPexDataFilters(e.filters); // Store in context if on Stage 2
            } else {
                setStage1TotalPexDataFilters(e.filters); // Store in context if on Stage 1
            }
        } else {
            setLocalFilters(e.filters); // Use local filters when not saving in context
        }
    }, [saveFiltersInContext, setStage1TotalPexDataFilters, setStage2TotalPexDataFilters, isUserOnStage2Page]);

    return (
        <DataTable
            scrollable
            scrollHeight="flex"
            value={data}
            filters={totalPexDataFilters}
            onFilter={onFilterHandler}
            header={renderHeader}
            filterDisplay={filterDisplay}
            size={size}
            paginator={pagination}
            showGridlines
            rows={rowsPerPage}
            rowsPerPageOptions={rowsPerPageOptions}
            removableSort
            resizableColumns={resizable}
            reorderableColumns={reorderable}
            stripedRows={striped}
            emptyMessage={emptyMessage}
            style={{ fontSize: "14px" }}
            globalFilterFields={columns.map(col => (col.field || col))}
        >
            {formattedColumns.filter(col => col.field !== "LayoutData").map(col => (
                <Column
                    key={col.field}
                    field={col.field}
                    header={col.header}
                    sortable={col.sortable}
                    filter={col.filter}
                    filterField={col.field}
                    filterPlaceholder={`Search ${col.header}`}
                    style={col.style}
                    {...(typeof data[0]?.[col.field] === "number" ? { dataType: "numeric" } : {})}
                    body={rowData => rowData[col.field] ?? "-"}
                    sortFunction={col.sortFunction}
                />
            ))}
        </DataTable>
    );
};

export default Table;


