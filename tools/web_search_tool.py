"""Web search tool for the React Agent."""

import requests
from typing import Any, Dict, List, Optional
from .base_tool import BaseTool, ToolResult
from config import Config


class WebSearchTool(BaseTool):
    """Tool for searching the web using various search APIs."""
    
    def __init__(self):
        super().__init__(
            name="web_search",
            description=self._get_detailed_description()
        )
        self.serper_api_key = Config.SERPER_API_KEY
    
    def _get_detailed_description(self) -> str:
        """Get detailed description with examples for web search operations."""
        return """Search the web for current information, news, and real-time data using advanced search APIs.

WHAT IT DOES:
• Searches the internet for up-to-date information
• Returns relevant web pages, articles, and resources
• Provides real-time data and current events
• Finds information not available in static databases

SEARCH TYPES:
• General Search: Find web pages, articles, documentation
  Examples: "latest AI developments", "Python programming tutorial"
  
• News Search: Current events, breaking news, recent updates
  Examples: "today's news", "stock market updates", "weather forecast"
  
• Technical Information: Documentation, APIs, code examples
  Examples: "React hooks documentation", "MySQL syntax guide"
  
• Product Information: Reviews, comparisons, specifications
  Examples: "iPhone 15 review", "best laptops 2024"

BEST USE CASES:
• Current events and breaking news
• Real-time data (stock prices, weather, sports scores)
• Recent developments in technology, science, politics
• Product reviews and comparisons
• Technical documentation and tutorials
• Finding specific websites or resources

USAGE EXAMPLES:
- Current events: "Ukraine war latest news"
- Technical info: "Docker compose tutorial"
- Product research: "best electric cars 2024"
- Real-time data: "Bitcoin price today"
- Specific searches: "OpenAI GPT-4 capabilities"

SEARCH STRATEGIES:
• Use specific keywords for better results
• Include time indicators for recent info ("2024", "latest", "recent")
• Use quotes for exact phrases: "climate change effects"
• Add context for ambiguous terms
• Combine multiple relevant keywords

RETURNED INFORMATION:
- Page titles and descriptions
- URLs for full articles
- Publication dates when available
- Relevance rankings
- Related search suggestions

ADVANTAGES OVER OTHER TOOLS:
• More current than Wikipedia
• Broader coverage than academic databases
• Real-time information updates
• Access to diverse sources and perspectives
• Technical documentation and tutorials"""
    
    async def execute(self, query: str, **kwargs) -> ToolResult:
        """Execute web search."""
        try:
            # Get optional parameters
            num_results = kwargs.get("num_results", 5)
            search_type = kwargs.get("search_type", "search")  # search, news, images
            
            if self.serper_api_key:
                return await self._search_with_serper(query, num_results, search_type)
            else:
                # Fallback to a simple mock search if no API key
                return await self._mock_search(query, num_results)
        
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Web search failed: {str(e)}"
            )
    
    async def _search_with_serper(self, query: str, num_results: int, search_type: str) -> ToolResult:
        """Search using Serper API."""
        try:
            url = f"https://google.serper.dev/{search_type}"
            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "q": query,
                "num": num_results
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract results based on search type
            if search_type == "search":
                results = self._extract_search_results(data)
            elif search_type == "news":
                results = self._extract_news_results(data)
            else:
                results = self._extract_search_results(data)
            
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "results": results,
                    "total_results": len(results)
                },
                metadata={
                    "search_type": search_type,
                    "num_results": num_results,
                    "provider": "serper"
                }
            )
        
        except requests.RequestException as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Serper API request failed: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Serper search failed: {str(e)}"
            )
    
    async def _mock_search(self, query: str, num_results: int) -> ToolResult:
        """Mock search results when no API key is available."""
        mock_results = [
            {
                "title": f"Mock Result 1 for '{query}'",
                "link": "https://example.com/result1",
                "snippet": f"This is a mock search result for the query '{query}'. In a real implementation, this would contain actual search results from the web."
            },
            {
                "title": f"Mock Result 2 for '{query}'",
                "link": "https://example.com/result2", 
                "snippet": f"Another mock result for '{query}'. This demonstrates how the web search tool would return structured data."
            },
            {
                "title": f"Mock Result 3 for '{query}'",
                "link": "https://example.com/result3",
                "snippet": f"Third mock result for '{query}'. Configure SERPER_API_KEY in your .env file for real search results."
            }
        ]
        
        # Limit results to requested number
        results = mock_results[:num_results]
        
        return ToolResult(
            success=True,
            data={
                "query": query,
                "results": results,
                "total_results": len(results),
                "note": "These are mock results. Set SERPER_API_KEY for real web search."
            },
            metadata={
                "search_type": "mock",
                "num_results": num_results,
                "provider": "mock"
            }
        )
    
    def _extract_search_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract search results from Serper response."""
        results = []
        
        # Extract organic results
        for item in data.get("organic", []):
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "position": item.get("position", 0)
            })
        
        # Extract knowledge graph if available
        if "knowledgeGraph" in data:
            kg = data["knowledgeGraph"]
            results.insert(0, {
                "title": f"Knowledge Graph: {kg.get('title', '')}",
                "link": kg.get("website", ""),
                "snippet": kg.get("description", ""),
                "type": "knowledge_graph"
            })
        
        return results
    
    def _extract_news_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract news results from Serper response."""
        results = []
        
        for item in data.get("news", []):
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "date": item.get("date", ""),
                "source": item.get("source", ""),
                "type": "news"
            })
        
        return results
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's input schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to find information on the web"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of search results to return (default: 5)",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20
                },
                "search_type": {
                    "type": "string",
                    "description": "Type of search to perform",
                    "enum": ["search", "news", "images"],
                    "default": "search"
                }
            },
            "required": ["query"]
        }