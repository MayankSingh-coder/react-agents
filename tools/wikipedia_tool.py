"""Wikipedia tool for the React Agent."""

import wikipedia
from typing import Any, Dict
from .base_tool import BaseTool, ToolResult


class WikipediaTool(BaseTool):
    """Tool for searching and retrieving information from Wikipedia."""
    
    def __init__(self):
        super().__init__(
            name="wikipedia",
            description="Search Wikipedia for information about people, places, events, concepts, and general knowledge"
        )
        # Set Wikipedia language and other settings
        wikipedia.set_lang("en")
    
    async def execute(self, query: str, **kwargs) -> ToolResult:
        """Execute Wikipedia search and retrieval."""
        try:
            # Get optional parameters
            sentences = kwargs.get("sentences", 3)
            auto_suggest = kwargs.get("auto_suggest", True)
            
            # Search for the page
            try:
                # Get page summary
                summary = wikipedia.summary(
                    query, 
                    sentences=sentences, 
                    auto_suggest=auto_suggest
                )
                
                # Get the page object for additional info
                page = wikipedia.page(query, auto_suggest=auto_suggest)
                
                result_data = {
                    "title": page.title,
                    "summary": summary,
                    "url": page.url,
                    "categories": page.categories[:10] if hasattr(page, 'categories') else [],
                    "links": page.links[:20] if hasattr(page, 'links') else []
                }
                
                return ToolResult(
                    success=True,
                    data=result_data,
                    metadata={
                        "query": query,
                        "sentences": sentences,
                        "auto_suggest": auto_suggest
                    }
                )
                
            except wikipedia.DisambiguationError as e:
                # Handle disambiguation - return options
                options = e.options[:10]  # Limit to first 10 options
                
                return ToolResult(
                    success=False,
                    data={
                        "disambiguation_options": options,
                        "message": f"Multiple pages found for '{query}'. Please be more specific."
                    },
                    error=f"Disambiguation needed for '{query}'"
                )
                
            except wikipedia.PageError:
                # Try to search for similar pages
                try:
                    search_results = wikipedia.search(query, results=5)
                    if search_results:
                        return ToolResult(
                            success=False,
                            data={
                                "search_suggestions": search_results,
                                "message": f"Page '{query}' not found. Here are some suggestions."
                            },
                            error=f"Page '{query}' not found"
                        )
                    else:
                        return ToolResult(
                            success=False,
                            data=None,
                            error=f"No Wikipedia page found for '{query}'"
                        )
                except Exception:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"No Wikipedia page found for '{query}'"
                    )
        
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Wikipedia search failed: {str(e)}"
            )
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's input schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term or topic to look up on Wikipedia"
                },
                "sentences": {
                    "type": "integer",
                    "description": "Number of sentences to return in summary (default: 3)",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 10
                },
                "auto_suggest": {
                    "type": "boolean",
                    "description": "Whether to use Wikipedia's auto-suggestion feature (default: true)",
                    "default": True
                }
            },
            "required": ["query"]
        }