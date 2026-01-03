#!/usr/bin/env python3
"""
Robust YAML frontmatter parser using only Python stdlib.

This parser is designed to handle the YAML subset used in SKILL.md files:
- Simple key:value pairs
- Nested objects (via indentation)
- Arrays (inline [item1, item2] and multiline - item)
- Quoted strings with special characters
- Block scalars (| and >)
- Comments

It uses a state-machine approach to handle edge cases that break simple
split-on-colon parsing, such as:
- Multiline values with colons
- Nested objects in verification metadata
- Machine-generated YAML from automated retrospectives
- Complex quoted strings

Design Principle: Zero Dependencies (stdlib only) for CI/CD portability.
"""

import re
from typing import Dict, List, Any, Tuple, Optional


def extract_frontmatter(content: str) -> Tuple[Dict, str]:
    """Extract YAML frontmatter and body from markdown content.

    Args:
        content: Full markdown file content.

    Returns:
        Tuple[Dict, str]: A tuple of (metadata_dict, body_text).
            metadata_dict: Dictionary parsed from YAML frontmatter.
            body_text: The markdown content after the frontmatter.

    Note:
        Robust parsing handles nested objects (verification), block scalars (|),
        arrays (both styles), and quoted strings with special characters.
    """
    if not content.startswith('---'):
        return {}, content

    try:
        # Split on --- delimiters
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}, content

        frontmatter_text = parts[1]
        body = parts[2].strip()

        # Parse YAML subset
        metadata = parse_yaml_subset(frontmatter_text)
        return metadata, body

    except Exception as e:
        # Fail gracefully - return empty metadata
        import sys
        print(f"Warning: Failed to extract frontmatter: {e}", file=sys.stderr)
        return {}, content


def parse_yaml_subset(yaml_text: str) -> Dict:
    """Parse safe subset of YAML using stdlib-only state machine.

    Supported YAML features:
    - key: value (simple pairs)
    - key: [array, items] (inline arrays)
    - key: (followed by indented nested object or array)
    - "quoted: strings" (preserve colons inside quotes)
    - # comments
    - null, ~, "" (empty values)

    Args:
        yaml_text: The YAML string to parse.

    Returns:
        Dict: Dictionary with parsed metadata.
    """
    lines = yaml_text.split('\n')
    metadata = {}

    i = 0
    while i < len(lines):
        line = lines[i]
        original_line = line
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            i += 1
            continue

        # Get indentation level (number of leading spaces)
        indent_level = len(line) - len(line.lstrip(' '))

        # Only process root-level keys (indent 0)
        if indent_level == 0 and ':' in line:
            key, value, lines_consumed = parse_key_value_pair(lines, i)

            if key:
                metadata[key] = value
                i += lines_consumed
            else:
                i += 1
        else:
            # Skip non-root lines (they're handled by nested parsing)
            i += 1

    return metadata


def parse_key_value_pair(lines: List[str], start_idx: int) -> Tuple[str, Any, int]:
    """Parse a key:value pair, handling nested objects and arrays.

    Args:
        lines: All YAML lines as a list of strings.
        start_idx: Index of the line containing the key.

    Returns:
        Tuple[str, Any, int]: A tuple of (key, value, lines_consumed).
            key: The parsed field name.
            value: The parsed value (string, list, or dict).
            lines_consumed: Number of lines processed from the input list.
    """
    line = lines[start_idx]

    # Split on first colon only
    if ':' not in line:
        return '', None, 1

    # Handle quoted keys (rare but possible)
    key_match = re.match(r'^(["\']?)([^:"\']+)\1\s*:\s*(.*)$', line)
    if not key_match:
        # Fallback to simple split
        key, _, value_str = line.partition(':')
        key = key.strip()
        value_str = value_str.strip()
    else:
        key = key_match.group(2).strip()
        value_str = key_match.group(3).strip()

    # Validate key
    if not key or key.startswith('-') or key.startswith('#'):
        return '', None, 1

    # Parse value based on what follows the colon
    if not value_str:
        # Empty value - check for nested content
        nested_value, lines_consumed = parse_nested_content(lines, start_idx + 1)
        if nested_value is not None:
            return key, nested_value, lines_consumed + 1
        else:
            return key, '', 1

    elif value_str in ('|', '>'):
        # Block scalar (multiline string)
        block_value, lines_consumed = parse_block_scalar(lines, start_idx + 1, value_str)
        return key, block_value, lines_consumed + 1

    else:
        # Inline value
        value = parse_inline_value(value_str)
        return key, value, 1


def parse_inline_value(value_str: str) -> Any:
    """Parse an inline YAML value.

    Args:
        value_str: The string fragment after the colon.

    Returns:
        Any: The parsed value. Handles:
            - Quoted strings: "value" or 'value'
            - Inline arrays: [item1, item2]
            - Booleans: true, false, yes, no
            - Numbers: 42, 3.14
            - Null: null, ~
            - Plain strings (comments stripped)
    """
    value_str = value_str.strip()

    # Handle null/empty
    if value_str in ('null', '~', ''):
        return ''

    # Handle quoted strings (preserve content exactly)
    if (value_str.startswith('"') and value_str.endswith('"')) or \
       (value_str.startswith("'") and value_str.endswith("'")):
        # Remove outer quotes
        return value_str[1:-1]

    # Handle inline arrays [item1, item2]
    if value_str.startswith('[') and value_str.endswith(']'):
        return parse_inline_array(value_str)

    # Handle booleans
    if value_str.lower() in ('true', 'yes', 'on'):
        return True
    if value_str.lower() in ('false', 'no', 'off'):
        return False

    # Handle numbers
    try:
        if '.' in value_str:
            return float(value_str)
        return int(value_str)
    except ValueError:
        pass

    # Return as plain string (remove trailing inline comments)
    # For unquoted strings, # starts a comment
    if '#' in value_str:
        # Find first # and truncate
        comment_idx = value_str.find('#')
        value_str = value_str[:comment_idx].strip()

    return value_str


def parse_inline_array(array_str: str) -> List:
    """Parse inline array syntax: [item1, item2, "item3"].

    Args:
        array_str: The string fragment containing brackets.

    Returns:
        List: A list of parsed items. Handles empty arrays, quotes, and commas.
    """
    # Remove brackets
    array_content = array_str[1:-1].strip()

    if not array_content:
        return []

    # Split by comma (simple approach - doesn't handle nested arrays)
    items = []
    current_item = ''
    in_quotes = False
    quote_char = None

    for char in array_content:
        if char in ('"', "'") and not in_quotes:
            in_quotes = True
            quote_char = char
        elif char == quote_char and in_quotes:
            in_quotes = False
            quote_char = None
        elif char == ',' and not in_quotes:
            # End of item
            item = current_item.strip()
            if item:
                # Remove quotes if present
                if (item.startswith('"') and item.endswith('"')) or \
                   (item.startswith("'") and item.endswith("'")):
                    item = item[1:-1]
                items.append(item)
            current_item = ''
        else:
            current_item += char

    # Add last item
    item = current_item.strip()
    if item:
        if (item.startswith('"') and item.endswith('"')) or \
           (item.startswith("'") and item.endswith("'")):
            item = item[1:-1]
        items.append(item)

    return items


def parse_nested_content(lines: List[str], start_idx: int) -> Tuple[Optional[Any], int]:
    """Parse nested content (object or array) following a key.

    Args:
        lines: All YAML lines.
        start_idx: Index of the first potential nested line.

    Returns:
        Tuple[Optional[Any], int]: A tuple of (parsed_value, lines_consumed).
            Returns (None, 0) if no nested content is discovered.
    """
    if start_idx >= len(lines):
        return None, 0

    # Find first non-empty, non-comment line
    first_content_idx = start_idx
    while first_content_idx < len(lines):
        stripped = lines[first_content_idx].strip()
        if stripped and not stripped.startswith('#'):
            break
        first_content_idx += 1

    if first_content_idx >= len(lines):
        return None, 0

    # Get indentation of first nested line
    first_line = lines[first_content_idx]
    base_indent = len(first_line) - len(first_line.lstrip(' '))

    # Must be indented to be nested content
    if base_indent == 0:
        return None, 0

    # Determine if this is an array (starts with -) or object (has :)
    stripped_first = first_line.strip()

    if stripped_first.startswith('-'):
        # Multiline array
        return parse_multiline_array(lines, first_content_idx, base_indent)
    elif ':' in stripped_first:
        # Nested object
        return parse_nested_object(lines, first_content_idx, base_indent)
    else:
        # Unknown structure - treat as empty
        return None, 0


def parse_multiline_array(lines: List[str], start_idx: int, base_indent: int) -> Tuple[List, int]:
    """Parse multiline array in '- item' format.

    Args:
        lines: All YAML lines.
        start_idx: Index to start parsing from.
        base_indent: Expected indentation level for the array items.

    Returns:
        Tuple[List, int]: A tuple of (items_list, lines_consumed).
    """
    items = []
    i = start_idx

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            i += 1
            continue

        # Calculate indentation
        indent = len(line) - len(line.lstrip(' '))

        # If dedented back to root or less than base, we're done
        if indent < base_indent:
            break

        # If at our indent level and starts with -, it's an item
        if indent == base_indent and stripped.startswith('-'):
            # Extract item value after the dash
            item_value = stripped[1:].strip()

            # Parse the item value
            if item_value:
                items.append(parse_inline_value(item_value))
            else:
                # Check if item has nested content
                nested_value, nested_lines = parse_nested_content(lines, i + 1)
                if nested_value is not None:
                    items.append(nested_value)
                    i += nested_lines
                else:
                    items.append('')
            i += 1
        elif indent > base_indent:
            # More deeply nested - skip (handled by nested parsing)
            i += 1
        else:
            # Same or less indentation but doesn't start with - means end of array
            break

    lines_consumed = i - start_idx
    return items, lines_consumed


def parse_nested_object(lines: List[str], start_idx: int, base_indent: int) -> Tuple[Dict, int]:
    """Parse nested object via indentation.

    Args:
        lines: All YAML lines.
        start_idx: Index to start parsing from.
        base_indent: Expected indentation level for the object keys.

    Returns:
        Tuple[Dict, int]: A tuple of (parsed_dict, lines_consumed).
    """
    obj = {}
    i = start_idx

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            i += 1
            continue

        # Calculate indentation
        indent = len(line) - len(line.lstrip(' '))

        # If dedented, we're done with this object
        if indent < base_indent:
            break

        # If at our level and has colon, it's a key:value pair
        if indent == base_indent and ':' in line:
            # Parse this key-value pair
            key, value, consumed = parse_key_value_pair(lines, i)

            if key:
                obj[key] = value
                i += consumed
            else:
                i += 1
        elif indent > base_indent:
            # More deeply nested - skip (handled by recursive parsing)
            i += 1
        else:
            # Same indent but no colon - end of object
            break

    lines_consumed = i - start_idx
    return obj, lines_consumed


def parse_block_scalar(lines: List[str], start_idx: int, scalar_type: str) -> Tuple[str, int]:
    """Parse block scalar (| or >) for multiline strings.

    Args:
        lines: All YAML lines.
        start_idx: Index of first line of block content.
        scalar_type: '|' (literal) or '>' (folded).

    Returns:
        Tuple[str, int]: A tuple of (concatenated_string, lines_consumed).
    """
    if start_idx >= len(lines):
        return '', 0

    # Get base indentation from first line
    first_line = lines[start_idx]
    base_indent = len(first_line) - len(first_line.lstrip(' '))

    # Collect all lines at this indentation or greater
    block_lines = []
    i = start_idx

    while i < len(lines):
        line = lines[i]

        # Check indentation
        if line.strip():  # Non-empty line
            indent = len(line) - len(line.lstrip(' '))
            if indent < base_indent:
                # Dedented - end of block
                break
            # Add the line (preserving relative indentation)
            block_lines.append(line[base_indent:])  # Remove base indent
        else:
            # Empty line within block
            block_lines.append('')

        i += 1

    # Join lines based on scalar type
    if scalar_type == '|':
        # Literal: preserve newlines
        result = '\n'.join(block_lines).rstrip('\n')
    else:  # '>'
        # Folded: join lines with spaces (simplified)
        result = ' '.join(line.strip() for line in block_lines if line.strip())

    lines_consumed = i - start_idx
    return result, lines_consumed


# Backward compatibility: export the main function
__all__ = ['extract_frontmatter', 'parse_yaml_subset']
