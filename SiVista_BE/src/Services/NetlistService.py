"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: NetlistService.py  
 * Description: Netlist functions to validate netlist
 *  
 * Author: Mansi Mahadik 
 * Created On: 17-12-2024
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
 ***************************************************************************/"""
from rest_framework import status
from base64 import b64decode
import re

def extract_subckt(content):
    words=[]
    word_list = content.split()
    for i in range(len(word_list) - 1):
        current_word = word_list[i]
        if current_word.endswith('.subckt') or current_word.endswith('.SUBCKT'):
            words.append(word_list[i + 1])
    return(words)

def extract_cells(netlist_data):
    pattern = r'(\.subckt\s+[\w\d_]+[\s\S]+?\.ends\s+[\w\d_]+)'
    return re.findall(pattern, netlist_data)

def extract_cells_incomplete(netlist_data):
    """
    Extracts subcircuit definitions from netlist data.
    Returns a tuple of (cells, unappended_content, incomplete_indices).
    - cells: List of strings, each representing a subcircuit definition.
    - unappended_content: List of strings for content not part of any .subckt block.
    - incomplete_indices: List of indices in 'cells' where the cell is incomplete (missing .ends).
    If .ends tag is missing, stops at the start of the next .subckt or end of netlist.
    """
    starts = [m.start() for m in re.finditer(r'\.subckt\b', netlist_data, re.IGNORECASE)]
    if not starts:
        return ([], [netlist_data.strip()] if netlist_data.strip() else [], [])

    cells = []
    incomplete_cells = []
    unappended_fragments = []
    last_end = 0

    for i, start in enumerate(starts):
        # Capture content before this .subckt if it exists (unappended content)
        if start > last_end:
            unappended_text = netlist_data[last_end:start].strip()
            if unappended_text:
                unappended_fragments.append(unappended_text)

        # Determine the tentative end: either the next .subckt or the end of netlist
        tentative_end = starts[i + 1] if i + 1 < len(starts) else len(netlist_data)

        # Look for the corresponding .ENDS tag (case-insensitive)
        end_pattern = r'\.ends\s*(\w*)'
        end_matches = [m for m in re.finditer(end_pattern, netlist_data[start:tentative_end], re.IGNORECASE)]
        if end_matches:
            match = end_matches[0]
            end = start + match.end()
        else:
            end = tentative_end
            incomplete_cells.append(netlist_data[start:end].strip())

        cells.append(netlist_data[start:end].strip())
        last_end = end

    # Capture any remaining content after the last cell
    if last_end < len(netlist_data):
        remaining_text = netlist_data[last_end:].strip()
        if remaining_text:
            unappended_fragments.append(remaining_text)
    return cells, incomplete_cells, unappended_fragments[1:]



def v_header(netlist_data):
    valid_pmos_vdd = {'vdd', 'vpwr', 'vcc', 'pwr'}
    valid_nmos_vss = {'vss', 'vgnd', 'gnd'}
    
    error_messages = []

    first_line = netlist_data.lstrip().split('\n')[0]
    components = first_line.split()

    if not (len(components) >= 3 and components[0] == ".global"):
        error_messages.append("Netlist does not start with a valid '.global' line.")
    else:
        vdd_valid = components[1] in valid_pmos_vdd
        vss_valid = components[2] in valid_nmos_vss
        
        if not vdd_valid or not vss_valid:
            error_messages.append("Netlist does not contain valid VDD or VSS pin names.")    
    return error_messages if error_messages else None

def v_cells_exist(cells):
    error_messages = []
    if not cells:
        error_messages.append("No subcircuit (.subckt ... .ends) blocks found.")
    return error_messages if error_messages else None

def v_cell_starts_with_subckt(cells):
    """
    Validates that each cell definition starts with '.subckt'.
    """
    error_messages = []
    for i, cell in enumerate(cells):
        cell = cell.strip()
        if not cell:
            continue
        if not cell.lower().startswith('.subckt'):
            first_line = cell.splitlines()[0] if cell.splitlines() else cell
            words = first_line.split()
            if len(words) > 1:
                next_word = words[1]
                error_messages.append(f"Cell does not start with '.subckt'. Found: '{words[0]} {next_word}...'")
            else:
                error_messages.append(f"Cell does not start with '.subckt'. Found: '{words[0]}...'")
    return error_messages if error_messages else None

def v_unique_cell_names(cells):
    error_messages = []
    names = []
    for cell in cells:
        m = re.match(r'\.subckt\s+(\w+)', cell, re.IGNORECASE)
        if m:
            names.append(m.group(1))
    duplicates = set([x for x in names if names.count(x) > 1])
    if duplicates:
        error_messages.append(f"Duplicate cell names found: {', '.join(duplicates)}")
    return error_messages if error_messages else None

def v_missing_ends_tag(cells):
    """
    Ensures each cell has a .ends <cellname> tag.
    Returns an error string if any cell is missing .ends, otherwise None.
    """
    error_messages = []
    for cell in cells:
        subckt_match = re.match(r'\.subckt\s+(\w+)', cell, re.IGNORECASE)
        cell_name = subckt_match.group(1)
        ends_match = re.search(r'\.ends\s+(\w+)', cell, re.IGNORECASE)
        if not ends_match:
            error_messages.append(f".ends tag missing for subcircuit '{cell_name}'.")
    return error_messages if error_messages else None

def v_subckt_name_mismatch(cells):
    """
    Ensures .subckt and .ends use the same name in each cell.
    Returns an error string if any name is mismatched, otherwise None.
    """
    error_messages = []
    for cell in cells:
        subckt_match = re.match(r'\.subckt\s+(\w+)', cell, re.IGNORECASE)
        ends_match = re.search(r'\.ends\s+(\w+)', cell, re.IGNORECASE)
        if not (subckt_match and ends_match):  # Skip if already caught by other validators
            continue
        cell_name = subckt_match.group(1)
        ends_name = ends_match.group(1)
        if cell_name.upper() != ends_name.upper():
            error_messages.append(f"subcircuit name mismatch: "
                    f".subckt '{cell_name}' and .ends '{ends_name}'.")
    return error_messages if error_messages else None

def v_cell_names_capitalization(cells):
    """
    Ensures all cell names in .subckt and .ends are uppercase.
    """
    error_messages = []
    for cell in cells:
        subckt_match = re.match(r'\.subckt\s+(\w+)', cell, re.IGNORECASE)
        ends_match   = re.search(r'\.ends\s+(\w+)', cell, re.IGNORECASE)
        if not subckt_match:
            continue
        cell_name_subckt = subckt_match.group(1)
        if cell_name_subckt != cell_name_subckt.upper():
            error_messages.append(f"Cell name '{cell_name_subckt}' in .subckt must be uppercase.")
        if ends_match:
            cell_name_ends = ends_match.group(1)
            if cell_name_ends != cell_name_ends.upper():
                error_messages.append(f"Cell name '{cell_name_ends}' in .ends must be uppercase.")
    return error_messages if error_messages else None

def preprocess_plus_lines(cell_text):
    """Join continuation lines (starting with '+') with previous line."""
    result = []
    for line in cell_text.splitlines():
        if line.strip().startswith('+') and result:
            # Join +line to previous line with space
            result[-1] += ' ' + line.strip()[1:].strip()
        else:
            result.append(line)
    return '\n'.join(result)

def v_transistor_naming(cells):
    """
    - Only transistor lines (containing 'nmos' or 'pmos') must start with 'M'.
    - Only subcircuit/nested cell instance lines (starting with 'X') are allowed as children.
    - If any other device types, skip (or add more rules if needed).
    """
    error_messages = []
    for cell in cells:
        subckt_match = re.match(r'\.subckt\s+(\w+)', cell, re.IGNORECASE)
        cell_name = subckt_match.group(1)
        for line in cell.splitlines():
            line = line.strip()
            if not line or line.startswith(('.', '*', '+')): continue
            tokens = line.split()
            if not tokens: continue
            instance_name = tokens[0]
            # Transistor device line
            if any(t.lower() in ('nmos', 'pmos') for t in tokens):
                if not instance_name.upper().startswith('M'):
                    error_messages.append(f"cell '{cell_name}' Transistor instance '{instance_name}' must start with 'M'.")
            else:
                error_messages.append(f"cell '{cell_name}' contains an invalid instance '{instance_name}'.")
    return error_messages if error_messages else None

def v_at_least_one_transistor(cells):
    """
    Ensure each cell contains at least one transistor line (M* or MM* with 'pmos' or 'nmos').
    Handles continuation lines starting with '+'.
    """
    error_messages = []
    for cell in cells:
        subckt_match = re.match(r'\.subckt\s+(\w+)', cell, re.IGNORECASE)
        cell_name = subckt_match.group(1)
        found = False
        
        for line in cell.splitlines():
            line = line.strip()
            if not line or line.startswith(('.', '*', '+')):
                continue  # Skip empty lines, directives, comments, and continuation lines
            tokens = line.split()
            if len(tokens) < 2:
                continue
            instance_name = tokens[0].upper()
            line_lower = line.lower()
            # Check if instance name starts with 'M' (covers M, MM, etc.) and contains 'pmos' or 'nmos'
            if instance_name.startswith('M') and ('pmos' in line_lower or 'nmos' in line_lower):
                found = True
                break
        
        if not found:
            error_messages.append(f"Cell '{cell_name}' does not contain any transistor.")
    return error_messages if error_messages else None

def v_transistor_instance_uniqueness(cells):
    """
    Each transistor must be unique in each individual cell.
    """
    error_messages = []
    for cell in cells:
        cell_name = re.match(r'\.subckt\s+(\w+)', cell, re.IGNORECASE).group(1)
        block = preprocess_plus_lines(cell)
        names = set()
        for line in block.splitlines():
            if not line or line.startswith(('.', '*', '+')): continue
            tokens = line.split()
            if tokens and tokens[0].upper().startswith("M"):
                if tokens[0] in names:
                    error_messages.append(f"In cell '{cell_name}', transistor instance '{tokens[0]}' is duplicated.")
                names.add(tokens[0])
    return error_messages if error_messages else None

def v_child_cells_exist(cells):
    """
    For every subcircuit/nested cell call (X... lines), checks if the cell
    is defined in the netlist (i.e., there's a matching .subckt definition).
    """
    error_messages = []
    # 1. Collect all defined cell names in uppercase (case-insensitive)
    defined_cells = set()
    for cell in cells:
        subckt_match = re.match(r'\.subckt\s+(\w+)', cell)
        if subckt_match:
            defined_cells.add(subckt_match.group(1).upper())
    
    # 2. Within each subckt, look for X instance lines (ignoring comments, directives)
    for cell in cells:
        subckt_match = re.match(r'\.subckt\s+(\w+)', cell)
        parent_cell = subckt_match.group(1)
        for line in cell.splitlines():
            line = line.strip()
            if not line or line.startswith(('.', '*', '+')):
                continue
            tokens = line.split()
            if not tokens: continue
            if tokens[0].upper().startswith('X'):
                # Get child cell name (last token in the line)
                # Remove optional params after cell name (handle inline params)
                # We'll use the last standalone word that looks like a cell name
                child_cell = tokens[-1].upper()
                # Check if it's in the defined cells
                if child_cell not in defined_cells:
                    error_messages.append(f"In cell '{parent_cell}', child cell '{child_cell}' "
                            "is not defined in the netlist.")
    return error_messages if error_messages else None

def v_child_cell_pin_count(cells):
    """
    For every child subcircuit instance (X...), check its pin count matches the parent cell subckt.
    """
    error_messages = []
    # 1. Gather all subckt definitions: name -> list-of-pin-names
    cell_pins = {}
    for cell in cells:
        lines = cell.splitlines()
        if not lines:
            continue
        # Find subckt header line and its pins
        header = lines[0].strip()
        m = re.match(r'\.subckt\s+(\w+)\s+(.*)', header)
        if m:
            cell_name = m.group(1).upper()
            pin_str = m.group(2)
            # Remove possible double spaces and split on whitespace
            pin_list = [pin for pin in pin_str.strip().split() if pin]
            cell_pins[cell_name] = pin_list

    # 2. For each usage of X*, check if argument count (except instance name and cell type) matches pin count
    for cell in cells:
        subckt_match = re.match(r'\.subckt\s+(\w+)', cell)
        parent_cell = subckt_match.group(1)
        for line_num, line in enumerate(cell.splitlines(), 1):
            line = line.strip()
            if not line or line.startswith(('.', '*', '+')):
                continue
            tokens = line.split()
            if not tokens: continue
            if tokens[0].upper().startswith('X'):
                # Assume format: Xname <pin1> <pin2> ... <celltype>
                child_cell = tokens[-1].upper()
                if child_cell not in cell_pins:
                    # Possibly caught in another validator, skip here
                    continue
                pins_passed = tokens[1:-1]
                pins_defined = cell_pins[child_cell]
                if len(pins_passed) != len(pins_defined):
                    error_messages.append(f"In '{parent_cell}' line {line_num}, "
                            f"child '{tokens[0]}' has {len(pins_passed)} pins, "
                            f"but '{child_cell}' needs {len(pins_defined)}.")
    return error_messages if error_messages else None

def v_transistor_param_count(cells):
    """
    Each transistor line must have exactly 4 parameters between the
    instance name and the 'nmos' or 'pmos' keyword.
    """
    error_messages = []
    for cell in cells:
        subckt_match = re.match(r'\.subckt\s+(\w+)', cell, re.IGNORECASE)
        cell_name = subckt_match.group(1)
        cell_processed = preprocess_plus_lines(cell)
        for idx, line in enumerate(cell_processed.splitlines(), 1):
            line = line.strip()
            if not line or line.startswith(('.', '*', '+')):
                continue
            tokens = line.split()
            if len(tokens) < 6:
                continue # not a valid device line
            instance_name = tokens[0]
            # Only consider M* lines with nmos/pmos
            try:
                # find the position of "nmos" or "pmos"
                for t_target in ('nmos', 'pmos'):
                    if t_target in [t.lower() for t in tokens]:
                        t_pos = [t.lower() for t in tokens].index(t_target)
                        break
                else:
                    continue
                if instance_name.upper().startswith('M'):
                    if t_pos != 5:
                        error_messages.append(f"In cell '{cell_name}' line {idx}, "
                                f"transistor '{instance_name}' does not have exactly 4 pins ")
            except Exception as e:
                error_messages.append(f"Could not validate transistor parameters in cell '{cell_name}', line {idx}.")
    return error_messages if error_messages else None

def v_pin_usage(cells):
    error_messages = []
    for i, cell in enumerate(cells):
        # Extract the .subckt line to get defined pins
        first_line = cell.splitlines()[0].strip()
        subckt_match = re.match(r'\.subckt\s+(\w+)\s+([^\n]+)', first_line, re.IGNORECASE)
        if not subckt_match:
            return None
        
        cell_name = subckt_match.group(1)
        pins_str = subckt_match.group(2)
        defined_pins = set(pins_str.split())
        
        # Extract transistor lines and collect used pins from all tokens
        used_pins = set()
        for line in cell.splitlines():
            if not line.strip() or line.strip().startswith(('.', '*', '+')):
                continue
            tokens = line.split()
            if tokens and tokens[0].upper().startswith("M"):
                # Check all tokens in the line for matches with defined pins
                for token in tokens[1:]:  # Skip the transistor name (M*)
                    if token in defined_pins:
                        used_pins.add(token)
        
        # Check for unused pins
        unused_pins = defined_pins - used_pins
        if unused_pins:
            error_messages.append(f"In cell '{cell_name}', the following defined pins are unused: {', '.join(unused_pins)}.")
    return error_messages if error_messages else None

def v_duplicate_pins(cells):
    """
    Validates that there are no duplicate pins in the .subckt line of each cell.
    Returns an error message if duplicate pins are found, otherwise None.
    """
    error_messages = []
    for cell in cells:
        # Match the .subckt format:
        first_line = cell.splitlines()[0].strip()
        subckt_match = re.match(r'\.subckt\s+(\w+)(?:\s+([^\n]+))?', first_line, re.IGNORECASE)
        if not subckt_match:
            error_messages.append(f"'{cell}' has no valid .subckt definition.")
            continue
        
        cell_name = subckt_match.group(1)
        pins_str = subckt_match.group(2)
        
        if not pins_str:
            continue  # No pins defined, also no duplicates
        
        pin_list = pins_str.split()  # List of pins
        
        pin_set = set(pin_list)
        if len(pin_list) != len(pin_set):
            seen = set()
            duplicates = set()
            for pin in pin_list:
                if pin in seen:
                    duplicates.add(pin)
                else:
                    seen.add(pin)
            error_messages.append(f"In cell '{cell_name}', the following pins are duplicated: {', '.join(duplicates)}.")
    
    return error_messages if error_messages else None

def validate_transistor_names(cells):
    """
    Validates transistor pin names in two steps:
    1. Checks the pin immediately preceding 'pmos' or 'nmos' against general valid sets.
    2. Identifies VDD and VSS from .subckt pins and ensures the pin before 'pmos' or 'nmos' matches the declared pins.
    """
    error_messages = []
    valid_pmos_vdd = {'vdd', 'vpwr', 'vcc', 'pwr'}
    valid_nmos_vss = {'vss', 'vgnd', 'gnd'}

    for cell in cells:
        subckt_match = re.match(r'\.subckt\s+(\w+)(.*)', cell, re.IGNORECASE)
        if subckt_match:
            cell_name = subckt_match.group(1)
            # Get all pin names from .subckt line
            pin_part = subckt_match.group(2).strip()
            pins = pin_part.split()
            # Identify potential VDD and VSS from pins
            declared_vdd = None
            declared_vss = None
            for pin in pins:
                pin_lower = pin.lower()
                if pin_lower in valid_pmos_vdd and declared_vdd is None:
                    declared_vdd = pin_lower
                elif pin_lower in valid_nmos_vss and declared_vss is None:
                    declared_vss = pin_lower
                if declared_vdd and declared_vss:  # Stop if we have both
                    break
            if not declared_vdd:
                error_messages.append(f"In cell {cell_name}, no pin found in .subckt definition.")
            if not declared_vss:
                error_messages.append(f"In cell {cell_name}, no pin found in .subckt definition.")
        else:
            cell_name = "Unknown"
            declared_vdd = None
            declared_vss = None
            error_messages.append(f"In cell {cell_name}, unable to parse .subckt line.")

        for idx, line in enumerate(cell.splitlines(), 1):
            trimmed_line = line.strip().lower()
            if trimmed_line.startswith('m'):
                parts = trimmed_line.split()
                if len(parts) < 5:  # Ensure enough parts for a valid transistor definition
                    error_messages.append(f"In cell {cell_name}, incomplete transistor definition.")

                # Step 1 & 2: Check the pin immediately before 'pmos' or 'nmos'
                if 'pmos' in parts:
                    index = parts.index('pmos')
                    if index > 0:  # Ensure we're not checking an invalid index
                        transistor_name = parts[0]
                        preceding_value = parts[index - 1]
                        # Step 1: Check against general valid set
                        if preceding_value not in valid_pmos_vdd:
                            error_messages.append(
                                f"In cell {cell_name}, Invalid pin '{preceding_value}' before 'pmos'. "
                                f"Valid pins are {', '.join(valid_pmos_vdd)}."
                            )
                        # Step 2: Check consistency with declared VDD
                        elif declared_vdd and preceding_value != declared_vdd:
                            error_messages.append(
                                f"In cell {cell_name}, transistor {transistor_name}: pin '{preceding_value}' before 'pmos' does not match "
                                f"declared pin '{declared_vdd}'."
                            )

                elif 'nmos' in parts:
                    index = parts.index('nmos')
                    if index > 0:  # Ensure we're not checking an invalid index
                        transistor_name = parts[0]
                        preceding_value = parts[index - 1]
                        # Step 1: Check against general valid set
                        if preceding_value not in valid_nmos_vss:
                            error_messages.append(
                                f"In cell {cell_name}, Invalid pin '{preceding_value}' before 'nmos'. "
                                f"Valid pins are {', '.join(valid_nmos_vss)}."
                            )
                        # Step 2: Check consistency with declared VSS
                        elif declared_vss and preceding_value != declared_vss:
                            error_messages.append(
                                f"In cell {cell_name}, transistor {transistor_name}: pin '{preceding_value}' before 'nmos' does not match "
                                f"declared pin '{declared_vss}'."
                            )

    return error_messages if error_messages else None

def validate_netlist(netlist_bytes):
    try:
        netlist_data = netlist_bytes.decode('utf-8')
    except Exception:
        return "Error decoding file!", status.HTTP_400_BAD_REQUEST, False, None

    # Pre-parsing for validators that need it
    cells, incomplete_cells, unappended_fragments = extract_cells_incomplete(netlist_data)
    cells = [preprocess_plus_lines(cell) for cell in cells]

    # List of all validators you want to run, in order. Pass as lambdas if they require args.
    validators = [
        lambda: v_header(netlist_data),
        lambda: v_cells_exist(cells),
        lambda: v_cell_starts_with_subckt(unappended_fragments),
        lambda: v_unique_cell_names(cells),
        lambda: v_missing_ends_tag(cells),
        lambda: v_subckt_name_mismatch(cells),
        lambda: v_cell_names_capitalization(cells),
        lambda: v_duplicate_pins(cells),
        lambda: v_at_least_one_transistor(cells),
        lambda: v_transistor_instance_uniqueness(cells),
        lambda: v_transistor_naming(cells),
        lambda: v_transistor_param_count(cells),
        lambda: validate_transistor_names(cells),
        lambda: v_pin_usage(cells),
    ]

    def run_validators(validators):
        errors = []
        seen = set()

        for v in validators:
            err = v()
            if err:
                for e in sorted(err):  
                    if e not in seen:
                        seen.add(e)
                        errors.append(e)

        return errors

    errors = run_validators(validators)

    if errors:
        numbered_errors = [f"Error {i+1}: {error}" for i, error in enumerate(errors)]
        error_message = numbered_errors  # Join all numbered error messages with a newline
        return error_message, status.HTTP_203_NON_AUTHORITATIVE_INFORMATION, False, None


    # If all passed...
    try:
        cell_list = extract_subckt(netlist_data)
    except Exception:
        cell_list = []
    cell_info = [{'cell_name': name, 'is_selected': False} for name in (cell_list or [])]
    get_response = {'FileContent': netlist_data, 'Cell_Info': cell_info}
    if not errors and not get_response['Cell_Info']:
        return "No valid cell found.", status.HTTP_203_NON_AUTHORITATIVE_INFORMATION, False, None
    else:
        return "Netlist is valid.", status.HTTP_200_OK, True, get_response