# Tool Schemas for LLM Agent

## Element Discovery Tool

### Schema
```json
{
  "tool_name": "element_discovery",
  "required_parameters": ["action"],
  "actions": {
    "find_all_elements": {
      "description": "Find all interactive elements on the page",
      "parameters": {
        "action": {"type": "string", "value": "find_all_elements"},
        "visible_only": {"type": "boolean", "default": true, "optional": true},
        "limit": {"type": "integer", "default": 20, "optional": true}
      }
    },
    "find_by_type": {
      "description": "Find elements by specific type",
      "parameters": {
        "action": {"type": "string", "value": "find_by_type"},
        "element_type": {"type": "string", "required": true, "options": ["button", "input", "link", "form", "field", "text", "checkbox", "radio", "select", "image", "div", "span"]},
        "visible_only": {"type": "boolean", "default": true, "optional": true},
        "limit": {"type": "integer", "default": 20, "optional": true}
      }
    },
    "find_by_text": {
      "description": "Find elements containing specific text",
      "parameters": {
        "action": {"type": "string", "value": "find_by_text"},
        "text_contains": {"type": "string", "required": true},
        "visible_only": {"type": "boolean", "default": true, "optional": true},
        "limit": {"type": "integer", "default": 20, "optional": true}
      }
    },
    "find_form_elements": {
      "description": "Find all form-related elements",
      "parameters": {
        "action": {"type": "string", "value": "find_form_elements"},
        "visible_only": {"type": "boolean", "default": true, "optional": true},
        "limit": {"type": "integer", "default": 20, "optional": true}
      }
    },
    "find_by_attributes": {
      "description": "Find elements by specific attributes",
      "parameters": {
        "action": {"type": "string", "value": "find_by_attributes"},
        "attribute_filter": {"type": "object", "required": true, "example": {"placeholder": "email", "name": "username"}},
        "visible_only": {"type": "boolean", "default": true, "optional": true},
        "limit": {"type": "integer", "default": 20, "optional": true}
      }
    },
    "analyze_element": {
      "description": "Get detailed information about a specific element",
      "parameters": {
        "action": {"type": "string", "value": "analyze_element"},
        "element_selector": {"type": "string", "required": true, "example": "#username"}
      }
    }
  }
}
```

### Usage Examples
```python
# Find all buttons
await element_discovery.execute(
    query="Find buttons",
    action="find_by_type",
    element_type="button",
    limit=5
)

# Find elements with specific text
await element_discovery.execute(
    query="Find login elements",
    action="find_by_text",
    text_contains="login"
)

# Find elements by attributes
await element_discovery.execute(
    query="Find email input",
    action="find_by_attributes",
    attribute_filter={"placeholder": "email"}
)
```

## Element Interaction Tool

### Schema
```json
{
  "tool_name": "element_interaction",
  "required_parameters": ["action", "selector"],
  "actions": {
    "click": {
      "description": "Click on an element",
      "parameters": {
        "action": {"type": "string", "value": "click"},
        "selector": {"type": "string", "required": true, "example": "#login-button"}
      }
    },
    "type_text": {
      "description": "Type text in an element",
      "parameters": {
        "action": {"type": "string", "value": "type_text"},
        "selector": {"type": "string", "required": true, "example": "#username"},
        "text": {"type": "string", "required": true, "example": "john@email.com"}
      }
    },
    "clear_and_type": {
      "description": "Clear element and type new text",
      "parameters": {
        "action": {"type": "string", "value": "clear_and_type"},
        "selector": {"type": "string", "required": true, "example": "[name='password']"},
        "text": {"type": "string", "required": true, "example": "newpassword"}
      }
    },
    "check_visibility": {
      "description": "Check if an element is visible",
      "parameters": {
        "action": {"type": "string", "value": "check_visibility"},
        "selector": {"type": "string", "required": true, "example": ".error-message"}
      }
    },
    "get_text": {
      "description": "Get text content from an element",
      "parameters": {
        "action": {"type": "string", "value": "get_text"},
        "selector": {"type": "string", "required": true, "example": ".status-text"}
      }
    },
    "get_value": {
      "description": "Get value from an input element",
      "parameters": {
        "action": {"type": "string", "value": "get_value"},
        "selector": {"type": "string", "required": true, "example": "#search-input"}
      }
    },
    "hover": {
      "description": "Hover over an element",
      "parameters": {
        "action": {"type": "string", "value": "hover"},
        "selector": {"type": "string", "required": true, "example": ".menu-item"}
      }
    },
    "scroll_to": {
      "description": "Scroll element into view",
      "parameters": {
        "action": {"type": "string", "value": "scroll_to"},
        "selector": {"type": "string", "required": true, "example": "#footer"}
      }
    },
    "press_keys": {
      "description": "Press specific keys on an element",
      "parameters": {
        "action": {"type": "string", "value": "press_keys"},
        "selector": {"type": "string", "required": true, "example": "#search-input"},
        "keys": {"type": "string", "required": true, "options": ["Enter", "Tab", "Escape", "Space", "Backspace"], "example": "Enter"}
      }
    }
  }
}
```

### Usage Examples
```python
# Click an element
await element_interaction.execute(
    query="Click login button",
    action="click",
    selector="#login-button"
)

# Type text
await element_interaction.execute(
    query="Enter username",
    action="type_text",
    selector="#username",
    text="john@email.com"
)

# Check visibility
await element_interaction.execute(
    query="Check error message",
    action="check_visibility",
    selector=".error-message"
)
```

## Unified Browser Tool

### Schema
```json
{
  "tool_name": "unified_browser",
  "required_parameters": ["action"],
  "actions": {
    "open_browser": {
      "description": "Open a browser",
      "parameters": {
        "action": {"type": "string", "value": "open_browser"},
        "browser": {"type": "string", "required": true, "options": ["chrome", "chromium", "safari"], "default": "chrome"}
      }
    },
    "navigate": {
      "description": "Navigate to a URL",
      "parameters": {
        "action": {"type": "string", "value": "navigate"},
        "url": {"type": "string", "required": true, "example": "https://google.com"}
      }
    },
    "open_and_navigate": {
      "description": "Open browser and navigate to URL in one action",
      "parameters": {
        "action": {"type": "string", "value": "open_and_navigate"},
        "browser": {"type": "string", "required": true, "options": ["chrome", "chromium", "safari"], "default": "chrome"},
        "url": {"type": "string", "required": true, "example": "https://google.com"}
      }
    },
    "close_browser": {
      "description": "Close the browser",
      "parameters": {
        "action": {"type": "string", "value": "close_browser"}
      }
    }
  }
}
```

### Usage Examples
```python
# Open browser and navigate
await unified_browser.execute(
    query="Open Chrome and go to Google",
    action="open_and_navigate",
    browser="chrome",
    url="https://google.com"
)

# Close browser
await unified_browser.execute(
    query="Close browser",
    action="close_browser"
)
```

## Response Format

All tools return a `ToolResult` object with this structure:

```json
{
  "success": boolean,
  "data": object | null,
  "error": string | null,
  "metadata": object | null
}
```

### Success Response Example
```json
{
  "success": true,
  "data": {
    "elements": [
      {
        "tag": "input",
        "selectors": ["#username", "[name='username']", ".username-field"],
        "placeholder": "Enter username",
        "visible": true,
        "enabled": true,
        "type": "text"
      }
    ],
    "total_found": 1,
    "page_url": "https://example.com"
  },
  "error": null,
  "metadata": {
    "action": "find_by_attributes",
    "query": "Find username field"
  }
}
```

### Error Response Example
```json
{
  "success": false,
  "data": null,
  "error": "Element not found with selector: #non-existent. Use element_discovery tool to find correct selector.",
  "metadata": {
    "action": "click",
    "query": "Click non-existent button"
  }
}
```

## Common Patterns for LLM Agents

### 1. Discovery → Interaction Pattern
```python
# Step 1: Discover elements
discovery_result = await element_discovery.execute(
    action="find_by_type",
    element_type="button"
)

# Step 2: Use discovered selector
if discovery_result.success:
    button_selector = discovery_result.data['elements'][0]['selectors'][0]
    await element_interaction.execute(
        action="click",
        selector=button_selector
    )
```

### 2. Error Handling Pattern
```python
result = await element_interaction.execute(
    action="click",
    selector="#button"
)

if not result.success:
    # Try to find the element with discovery tool
    discovery_result = await element_discovery.execute(
        action="find_by_text",
        text_contains="submit"
    )
    
    if discovery_result.success:
        # Retry with discovered selector
        new_selector = discovery_result.data['elements'][0]['selectors'][0]
        await element_interaction.execute(
            action="click",
            selector=new_selector
        )
```

### 3. Form Filling Pattern
```python
# Find all form elements
form_result = await element_discovery.execute(
    action="find_form_elements"
)

# Fill each field
for element in form_result.data['elements']:
    if element['tag'] == 'input' and element.get('type') == 'text':
        await element_interaction.execute(
            action="type_text",
            selector=element['selectors'][0],
            text="appropriate_value"
        )
```

This schema-based approach ensures the LLM agent knows exactly what parameters to provide for each action, eliminating ambiguity and improving reliability.