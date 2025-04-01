import anyio
import click
import logging
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from nova_act import NovaAct
from pydantic import BaseModel


class NovaActModel(BaseModel):
    url: str
    actions: list[str]


async def use_nova_act(url: str, actions: list[str]) -> str:
    with NovaAct(starting_page=url) as agent:
        for action in actions:
            agent.act(action)
        return agent.page.content()


@click.command()
@click.option("-v", "--verbose")
def main(verbose: bool) -> int:
    logging_level = logging.WARN
    if verbose == 1:
        logging_level = logging.INFO
    elif verbose >= 2:
        logging_level = logging.DEBUG

    logging.basicConfig(level=logging_level, stream=sys.stderr)

    server = Server("nova-act-mcp")

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> str:
        if name != "nova_act":
            raise ValueError(f"Unknown tool: {name}")
        if "url" not in arguments:
            raise ValueError("Missing required argument 'url'")
        if "actions" not in arguments:
            raise ValueError("Missing required argument 'actions'")
        return await use_nova_act(arguments["url"], arguments["actions"])

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="Nova Act",
                description="Uses Nova Act to perform actions on a website",
                inputSchema=NovaActModel,
            )
        ]

    async def run():
        async with stdio_server() as streams:
            await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )

    anyio.run(run)

    return 0
