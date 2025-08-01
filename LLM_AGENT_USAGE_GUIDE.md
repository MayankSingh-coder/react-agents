# LLM Agent Usage Guide for Element Tools

## Overview

The element discovery and interaction tools now expose specific actions that the LLM agent can call directly, eliminating the need for natural language parsing.

## Tool Structure

Both tools use the same pattern:
```python
await tool.execute(query="optional description", **kwargs)
```

Where `kwargs` must include:
- `action`: The specific action to perform
- Additional parameters specific to that action

## Element Discovery Tool

### Available Actions

#### 1. `find_all_elements`
Find all interactive elements on the page.

**Parameters:**
- `action`: "find_all_elements"
- `visible_only`: boolean (default: True)
- `limit`: integer (default: 20)

**Example:**
```python
result = await element_discovery.execute(
    query="Find all interactive elements",
    action="find_all_elements",
    limit=10,
    visible_only=True
)
```

#### 2. `find_by_type`
Find elements by specific type.

**Parameters:**
- `action`: "find_by_type"
- `element_type`: string (button, input, link, form, field, text, checkbox, radio, select, image, div, span)
- `visible_only`: boolean (default: True)
- `limit`: integer (default: 20)

**Example:**
```python
result = await element_discovery.execute(
    query="Find all buttons",
    action="find_by_type",
    element_type="button",
    limit=5
)
```

#### 3. `find_by_text`
Find elements containing specific text.

**Parameters:**
- `action`: "find_by_text"
- `text_contains`: string
- `visible_only`: boolean (default: True)
- `limit`: integer (default: 20)

**Example:**
```python
result = await element_discovery.execute(
    query="Find login elements",
    action="find_by_text",
    text_contains="login",
    limit=5
)
```

#### 4. `find_form_elements`
Find all form-related elements.

**Parameters:**
- `action`: "find_form_elements"
- `visible_only`: boolean (default: True)
- `limit`: integer (default: 20)

**Example:**
```python
result = await element_discovery.execute(
    query="Find form fields",
    action="find_form_elements"
)
```

#### 5. `find_by_attributes`
Find elements by specific attributes.

**Parameters:**
- `action`: "find_by_attributes"
- `attribute_filter`: dict (e.g., {"placeholder": "email", "name": "username"})
- `visible_only`: boolean (default: True)
- `limit`: integer (default: 20)

**Example:**
```python
result = await element_discovery.execute(
    query="Find email input",
    action="find_by_attributes",
    attribute_filter={"placeholder": "email"}
)
```

#### 6. `analyze_element`
Get detailed information about a specific element.

**Parameters:**
- `action`: "analyze_element"
- `element_selector`: string (CSS selector, ID, etc.)

**Example:**
```python
result = await element_discovery.execute(
    query="Analyze login button",
    action="analyze_element",
    element_selector="#login-btn"
)
```

## Element Interaction Tool

### Available Actions

#### 1. `click`
Click on an element.

**Parameters:**
- `action`: "click"
- `selector`: string (required)

**Example:**
```python
result = await element_interaction.execute(
    query="Click login button",
    action="click",
    selector="#login-button"
)
```

#### 2. `type_text`
Type text in an element.

**Parameters:**
- `action`: "type_text"
- `selector`: string (required)
- `text`: string (required)

**Example:**
```python
result = await element_interaction.execute(
    query="Enter username",
    action="type_text",
    selector="#username",
    text="john@email.com"
)
```

#### 3. `clear_and_type`
Clear element and type new text.

**Parameters:**
- `action`: "clear_and_type"
- `selector`: string (required)
- `text`: string (required)

**Example:**
```python
result = await element_interaction.execute(
    query="Replace password",
    action="clear_and_type",
    selector="[name='password']",
    text="newpassword123"
)
```

#### 4. `check_visibility`
Check if an element is visible.

**Parameters:**
- `action`: "check_visibility"
- `selector`: string (required)

**Example:**
```python
result = await element_interaction.execute(
    query="Check error message",
    action="check_visibility",
    selector=".error-message"
)
```

#### 5. `get_text`
Get text content from an element.

**Parameters:**
- `action`: "get_text"
- `selector`: string (required)

**Example:**
```python
result = await element_interaction.execute(
    query="Get status message",
    action="get_text",
    selector=".status-text"
)
```

#### 6. `get_value`
Get value from an input element.

**Parameters:**
- `action`: "get_value"
- `selector`: string (required)

**Example:**
```python
result = await element_interaction.execute(
    query="Get current input value",
    action="get_value",
    selector="#search-input"
)
```

#### 7. `hover`
Hover over an element.

**Parameters:**
- `action`: "hover"
- `selector`: string (required)

**Example:**
```python
result = await element_interaction.execute(
    query="Hover over menu",
    action="hover",
    selector=".menu-item"
)
```

#### 8. `scroll_to`
Scroll element into view.

**Parameters:**
- `action`: "scroll_to"
- `selector`: string (required)

**Example:**
```python
result = await element_interaction.execute(
    query="Scroll to footer",
    action="scroll_to",
    selector="#footer"
)
```

#### 9. `press_keys`
Press specific keys on an element.

**Parameters:**
- `action`: "press_keys"
- `selector`: string (required)
- `keys`: string (e.g., "Enter", "Tab", "Escape")

**Example:**
```python
result = await element_interaction.execute(
    query="Press Enter on search",
    action="press_keys",
    selector="#search-input",
    keys="Enter"
)
```

## Complete Workflow Example

Here's how the LLM agent should use these tools for a complete automation task:

### Task: Login to a website

```python
# Step 1: Open browser and navigate
result = await unified_browser.execute(
    query="Open Chrome and go to example.com",
    action="open_and_navigate",
    browser="chrome",
    url="https://example.com/login"
)

# Step 2: Find all form elements
result = await element_discovery.execute(
    query="Find login form elements",
    action="find_form_elements",
    limit=10
)

# Result will contain elements like:
# [
#   {"selectors": ["#username", "[name='username']"], "tag": "input", "type": "text"},
#   {"selectors": ["#password", "[name='password']"], "tag": "input", "type": "password"},
#   {"selectors": ["#login-btn", ".login-button"], "tag": "button", "text": "Login"}
# ]

# Step 3: Type username
result = await element_interaction.execute(
    query="Enter username",
    action="type_text",
    selector="#username",
    text="john@email.com"
)

# Step 4: Type password
result = await element_interaction.execute(
    query="Enter password",
    action="type_text",
    selector="#password",
    text="mypassword123"
)

# Step 5: Click login button
result = await element_interaction.execute(
    query="Click login",
    action="click",
    selector="#login-btn"
)

# Step 6: Check for success/error messages
result = await element_discovery.execute(
    query="Find status messages",
    action="find_by_text",
    text_contains="error"
)

if result.success and result.data.get('elements'):
    # Handle error case
    error_element = result.data['elements'][0]
    error_text = await element_interaction.execute(
        query="Get error message",
        action="get_text",
        selector=error_element['selectors'][0]
    )
```

### Task: Search and select items

```python
# Step 1: Find search box
result = await element_discovery.execute(
    query="Find search input",
    action="find_by_attributes",
    attribute_filter={"placeholder": "Search"}
)

if result.success and result.data.get('elements'):
    search_selector = result.data['elements'][0]['selectors'][0]
    
    # Step 2: Type search query
    await element_interaction.execute(
        query="Enter search term",
        action="type_text",
        selector=search_selector,
        text="Python automation"
    )
    
    # Step 3: Press Enter
    await element_interaction.execute(
        query="Submit search",
        action="press_keys",
        selector=search_selector,
        keys="Enter"
    )

# Step 4: Find search results
result = await element_discovery.execute(
    query="Find search results",
    action="find_by_type",
    element_type="link",
    limit=5
)

# Step 5: Click first result
if result.success and result.data.get('elements'):
    first_result = result.data['elements'][0]
    await element_interaction.execute(
        query="Click first result",
        action="click",
        selector=first_result['selectors'][0]
    )
```

## Error Handling

Always check the `success` field in the result:

```python
result = await element_interaction.execute(
    action="click",
    selector="#non-existent"
)

if not result.success:
    print(f"Error: {result.error}")
    # Error: Element not found with selector: #non-existent. Use element_discovery tool to find correct selector.
```

## Best Practices for LLM Agents

1. **Always discover before interacting:**
   ```python
   # ✅ Good
   discovery_result = await element_discovery.execute(action="find_by_type", element_type="button")
   selector = discovery_result.data['elements'][0]['selectors'][0]
   await element_interaction.execute(action="click", selector=selector)
   
   # ❌ Bad - guessing selectors
   await element_interaction.execute(action="click", selector="#login")
   ```

2. **Use the most reliable selector:**
   ```python
   # Elements return multiple selectors in order of reliability
   # selectors[0] is usually the most reliable (ID-based)
   selectors = element['selectors']  # ["#unique-id", "[name='field']", ".class-name"]
   best_selector = selectors[0]  # Use the first one
   ```

3. **Handle errors gracefully:**
   ```python
   result = await element_interaction.execute(action="click", selector=selector)
   if not result.success:
       # Try alternative selector or different approach
       alternative_result = await element_discovery.execute(
           action="find_by_text", 
           text_contains="login"
       )
   ```

4. **Validate element state:**
   ```python
   # Check if element is visible before interacting
   visibility_result = await element_interaction.execute(
       action="check_visibility",
       selector=selector
   )
   
   if visibility_result.data.get('visible'):
       # Proceed with interaction
       await element_interaction.execute(action="click", selector=selector)
   ```

## Summary

The refactored tools provide:

✅ **Explicit Actions**: No more natural language parsing
✅ **Clear Parameters**: Structured input/output
✅ **Better Error Messages**: Specific guidance on what went wrong
✅ **Reliable Selectors**: Multiple options for each element
✅ **Predictable Behavior**: Same input always produces same output

This approach gives the LLM agent precise control over web automation tasks while eliminating the ambiguity of natural language interpretation.