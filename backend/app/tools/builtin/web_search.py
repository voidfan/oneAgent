"""Web search tool."""
import httpx

from app.tools.base import BaseTool, ToolResult


class WebSearchTool(BaseTool):
    """Search the web for information."""

    name = "web_search"
    description = "Search the web for current information on a given query."
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query.",
            },
            "num_results": {
                "type": "integer",
                "description": "Number of results to return.",
                "default": 5,
            },
        },
        "required": ["query"],
    }

    async def execute(self, query: str, num_results: int = 5, **kwargs) -> ToolResult:
        try:
            # Using a simple DuckDuckGo HTML search as fallback
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                if response.status_code == 200:
                    # Simple extraction of results
                    text = response.text
                    results = []
                    # Extract result snippets (simplified)
                    import re
                    snippets = re.findall(
                        r'class="result__snippet">(.*?)</a>', text, re.DOTALL
                    )
                    for i, snippet in enumerate(snippets[:num_results]):
                        clean = re.sub(r'<[^>]+>', '', snippet).strip()
                        if clean:
                            results.append({"index": i + 1, "snippet": clean})

                    if results:
                        return ToolResult(success=True, output=results)
                    return ToolResult(
                        success=True,
                        output=f"Search completed for '{query}' but no structured results extracted.",
                    )
                return ToolResult(
                    success=False,
                    error=f"Search request failed with status {response.status_code}",
                )
        except Exception as e:
            return ToolResult(success=False, error=f"Web search failed: {str(e)}")
