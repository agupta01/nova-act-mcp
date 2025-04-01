import json
import logging
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from nova_act import NovaAct
from pydantic import BaseModel, Field


class NovaActModel(BaseModel):
    url: str = Field(description="URL to fetch")
    actions: list[str] = Field(
        description="Specific, prescriptive actions to perform. Each action should be a clear instruction that a human could follow."
    )


def use_nova_act(
    url: str,
    actions: list[str],
) -> str:
    with NovaAct(starting_page=url) as agent:
        for action in actions:
            agent.act(action)
        return "Done"


def _format_text_tool_result(
    response_content: str,
    is_error: bool = False,
) -> types.CallToolResult:
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=response_content)],
        isError=is_error,
    )


async def serve() -> int:
    logger = logging.getLogger(__name__)

    server = Server("nova-act-mcp")

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> types.CallToolResult:
        if name != "nova-act":
            return _format_text_tool_result(f"Unknown tool: {name}", is_error=True)
        if "url" not in arguments:
            return _format_text_tool_result(
                "Missing required argument 'url'", is_error=True
            )
        if "actions" not in arguments:
            return _format_text_tool_result(
                "Missing required argument 'actions'", is_error=True
            )
        try:
            result = use_nova_act(
                arguments["url"],
                arguments["actions"],
            )
            return _format_text_tool_result(result)
        except Exception as e:
            return _format_text_tool_result(str(e), is_error=True)

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="nova-act",
                description="""Uses Nova Act to perform actions on a website. 
                
For effective browser automation, follow these best practices when creating actions:
1. Be prescriptive and succinct about UI interactions
2. Break large tasks into smaller, specific steps
3. Explicitly mention UI elements to interact with

Examples of good actions:
- "Click on the search bar at the top of the page"
- "Type 'matcha set' in the search bar"
- "Press Enter or click the search button"
- "Find a product that matches 'matcha set' in the search results and click on it"
- "On the product page, look for the 'Add to Cart' button and click it"

Examples of poor actions:
- "navigate"
- "search for a matcha set"
- "order a matcha set from amazon"

When using this tool, provide a list of specific, step-by-step actions that Nova Act should perform.
""",
                inputSchema=NovaActModel.model_json_schema(),
            )
        ]

    async def run():
        logger.info("Starting Nova Act MCP server...")
        async with stdio_server() as streams:
            await server.run(
                streams[0],
                streams[1],
                server.create_initialization_options(),
            )

    await run()
