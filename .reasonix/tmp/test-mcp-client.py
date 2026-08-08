# -*- coding: utf-8 -*-
"""临时验证：test-assets-mcp stdio 握手 + 工具调用"""
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SCRIPT = r"C:/Users/ahusj/claude-code-vibe/test-ds-v4-flash/.reasonix/mcp/test-assets-mcp.py"

async def main():
    params = StdioServerParameters(command="python", args=[SCRIPT])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("已暴露工具:", [t.name for t in tools.tools])

            r1 = await session.call_tool("assets_list", {"module": "register"})
            print("\n[assets_list register]", r1.content[0].text)

            r2 = await session.call_tool("assets_read_json", {"module": "login", "version": 3})
            text = r2.content[0].text
            print("\n[assets_read_json login v3] 前 120 字符:", text[:120])

            r3 = await session.call_tool("report_index", {})
            print("\n[report_index]", r3.content[0].text)

asyncio.run(main())
