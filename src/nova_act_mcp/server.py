import logging
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server


async def serve(repository: Path | None) -> None:
    logger = logging.getLogger(__name__)

    server = Server("nova-act-mcp")

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)
