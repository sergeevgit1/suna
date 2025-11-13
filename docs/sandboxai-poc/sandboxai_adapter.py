"""
SandboxAI Adapter for SUNA
Provides compatibility layer between SUNA and SandboxAI

This adapter implements the same interface as the Daytona client,
allowing seamless migration from Daytona to SandboxAI.

Usage:
    from sandboxai_adapter import SandboxAIClient, SandboxAIContext
    
    # Method 1: Manual connection
    client = SandboxAIClient("workspace-123")
    client.connect()
    result = client.execute_code("print('hello')")
    client.disconnect()
    
    # Method 2: Context manager (recommended)
    with SandboxAIContext("workspace-123") as sandbox:
        result = sandbox.execute_code("print('hello')")
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Try to import sandboxai, provide helpful error if not available
try:
    from sandboxai import Sandbox
    SANDBOXAI_AVAILABLE = True
except ImportError:
    SANDBOXAI_AVAILABLE = False
    import warnings
    warnings.warn(
        "sandboxai-client is not installed. "
        "Install it with: pip install sandboxai-client"
    )

logger = logging.getLogger(__name__)


class SandboxAIClient:
    """
    Adapter class to interface with SandboxAI
    Provides API compatible with existing SUNA sandbox interface (Daytona)
    """
    
    def __init__(self, workspace_id: str, **kwargs):
        """
        Initialize SandboxAI client
        
        Args:
            workspace_id: Unique identifier for the workspace
            **kwargs: Additional configuration options:
                - workspace_dir: Custom workspace directory (default: /workspace/{workspace_id})
                - embedded: Run in embedded mode (default: True)
                - timeout: Operation timeout in seconds (default: 300)
        """
        if not SANDBOXAI_AVAILABLE:
            raise RuntimeError(
                "sandboxai-client is not installed. "
                "Install it with: pip install sandboxai-client"
            )
        
        self.workspace_id = workspace_id
        self.workspace_dir = kwargs.get('workspace_dir', f'/workspace/{workspace_id}')
        self.embedded = kwargs.get('embedded', True)
        self.timeout = kwargs.get('timeout', 300)
        self.sandbox = None
        self._connected = False
        
        logger.info(f"Initialized SandboxAI client for workspace: {workspace_id}")
    
    def connect(self) -> bool:
        """
        Connect to or create a sandbox
        
        Returns:
            True if connection successful
            
        Raises:
            RuntimeError: If connection fails
        """
        try:
            logger.info(f"Connecting to sandbox for workspace: {self.workspace_id}")
            
            # Create sandbox instance
            self.sandbox = Sandbox(embedded=self.embedded)
            self.sandbox.__enter__()
            
            # Create workspace directory
            result = self.sandbox.run_shell_command(f"mkdir -p {self.workspace_dir}")
            if result.error:
                logger.warning(f"Workspace directory creation warning: {result.error}")
            
            self._connected = True
            logger.info(f"Successfully connected to sandbox: {self.workspace_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to sandbox: {e}")
            self._connected = False
            raise RuntimeError(f"Sandbox connection failed: {e}")
    
    def disconnect(self):
        """Disconnect from sandbox and cleanup resources"""
        if self.sandbox and self._connected:
            try:
                self.sandbox.__exit__(None, None, None)
                self._connected = False
                logger.info(f"Disconnected from sandbox: {self.workspace_id}")
            except Exception as e:
                logger.error(f"Error disconnecting from sandbox: {e}")
    
    def is_connected(self) -> bool:
        """Check if sandbox is connected"""
        return self._connected and self.sandbox is not None
    
    def _ensure_connected(self):
        """Ensure sandbox is connected, raise error if not"""
        if not self.is_connected():
            raise RuntimeError(
                "Sandbox not connected. Call connect() first or use context manager."
            )
    
    def execute_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Execute code in the sandbox
        
        Args:
            code: Code to execute
            language: Programming language (python, bash, shell)
            
        Returns:
            Dict with keys:
                - success: bool - whether execution succeeded
                - output: str - stdout output
                - error: str - stderr output or error message
                - execution_time: float - execution time in seconds
        """
        self._ensure_connected()
        
        start_time = datetime.now()
        
        try:
            logger.debug(f"Executing {language} code: {code[:100]}...")
            
            if language == "python":
                result = self.sandbox.run_ipython_cell(code)
            elif language in ["bash", "shell"]:
                result = self.sandbox.run_shell_command(code)
            else:
                raise ValueError(f"Unsupported language: {language}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "output": result.output if result.output else "",
                "error": result.error if hasattr(result, 'error') and result.error else None,
                "execution_time": execution_time
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Code execution failed: {e}")
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "execution_time": execution_time
            }
    
    def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Write content to a file in the sandbox
        
        Args:
            file_path: Path to the file (relative to workspace)
            content: File content to write
            
        Returns:
            Dict with keys:
                - success: bool
                - path: str - full path to file
                - message: str - success message
                - error: str - error message (if failed)
        """
        self._ensure_connected()
        
        try:
            # Construct full path
            full_path = os.path.join(self.workspace_dir, file_path)
            
            # Create directory if needed
            dir_path = os.path.dirname(full_path)
            if dir_path and dir_path != self.workspace_dir:
                self.sandbox.run_shell_command(f"mkdir -p {dir_path}")
            
            # Escape content for shell (handle quotes and special characters)
            # Use Python to write file to avoid shell escaping issues
            write_code = f"""
import os
with open('{full_path}', 'w') as f:
    f.write({repr(content)})
"""
            result = self.sandbox.run_ipython_cell(write_code)
            
            if result.error:
                raise Exception(result.error)
            
            logger.info(f"File written successfully: {file_path}")
            return {
                "success": True,
                "path": full_path,
                "message": f"File written: {file_path}",
                "size": len(content)
            }
            
        except Exception as e:
            logger.error(f"File write failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read content from a file in the sandbox
        
        Args:
            file_path: Path to the file (relative to workspace)
            
        Returns:
            Dict with keys:
                - success: bool
                - content: str - file content
                - path: str - full path to file
                - error: str - error message (if failed)
        """
        self._ensure_connected()
        
        try:
            full_path = os.path.join(self.workspace_dir, file_path)
            
            # Use Python to read file to handle binary/encoding properly
            read_code = f"""
with open('{full_path}', 'r') as f:
    print(f.read())
"""
            result = self.sandbox.run_ipython_cell(read_code)
            
            if result.error:
                raise Exception(result.error)
            
            logger.info(f"File read successfully: {file_path}")
            return {
                "success": True,
                "content": result.output,
                "path": full_path
            }
            
        except Exception as e:
            logger.error(f"File read failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_files(self, directory: str = ".", pattern: str = "*") -> Dict[str, Any]:
        """
        List files in a directory
        
        Args:
            directory: Directory path (relative to workspace)
            pattern: File pattern (e.g., "*.py", "test_*")
            
        Returns:
            Dict with keys:
                - success: bool
                - files: List[str] - list of file names
                - output: str - raw ls output
                - error: str - error message (if failed)
        """
        self._ensure_connected()
        
        try:
            full_path = os.path.join(self.workspace_dir, directory)
            command = f"ls -la {full_path}/{pattern}"
            result = self.sandbox.run_shell_command(command)
            
            if result.error:
                logger.warning(f"List files warning: {result.error}")
            
            # Parse output into file list
            files = []
            for line in result.output.split('\n'):
                if line and not line.startswith('total'):
                    parts = line.split()
                    if len(parts) >= 9:
                        filename = ' '.join(parts[8:])
                        if filename not in ['.', '..']:
                            files.append(filename)
            
            return {
                "success": True,
                "files": files,
                "output": result.output,
                "count": len(files)
            }
            
        except Exception as e:
            logger.error(f"List files failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """
        Delete a file in the sandbox
        
        Args:
            file_path: Path to the file (relative to workspace)
            
        Returns:
            Dict with success status
        """
        self._ensure_connected()
        
        try:
            full_path = os.path.join(self.workspace_dir, file_path)
            result = self.sandbox.run_shell_command(f"rm -f {full_path}")
            
            if result.error:
                raise Exception(result.error)
            
            logger.info(f"File deleted: {file_path}")
            return {
                "success": True,
                "message": f"File deleted: {file_path}"
            }
            
        except Exception as e:
            logger.error(f"File delete failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def execute_shell_command(
        self, 
        command: str, 
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute a shell command in the sandbox
        
        Args:
            command: Shell command to execute
            cwd: Working directory (relative to workspace)
            env: Environment variables to set
            
        Returns:
            Dict with execution result
        """
        self._ensure_connected()
        
        try:
            # Prepare command with cwd
            if cwd:
                full_cwd = os.path.join(self.workspace_dir, cwd)
                command = f"cd {full_cwd} && {command}"
            else:
                command = f"cd {self.workspace_dir} && {command}"
            
            # Add environment variables if provided
            if env:
                env_str = ' '.join([f"{k}={v}" for k, v in env.items()])
                command = f"{env_str} {command}"
            
            logger.debug(f"Executing shell command: {command[:100]}...")
            result = self.sandbox.run_shell_command(command)
            
            return {
                "success": True,
                "output": result.output if result.output else "",
                "error": result.error if hasattr(result, 'error') and result.error else None
            }
            
        except Exception as e:
            logger.error(f"Shell command failed: {e}")
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
    
    def get_workspace_info(self) -> Dict[str, Any]:
        """
        Get information about the workspace
        
        Returns:
            Dict with workspace information
        """
        self._ensure_connected()
        
        try:
            # Get disk usage
            du_result = self.sandbox.run_shell_command(f"du -sh {self.workspace_dir}")
            disk_usage = du_result.output.split()[0] if du_result.output else "unknown"
            
            # Get file count
            count_result = self.sandbox.run_shell_command(f"find {self.workspace_dir} -type f | wc -l")
            file_count = int(count_result.output.strip()) if count_result.output else 0
            
            return {
                "success": True,
                "workspace_id": self.workspace_id,
                "workspace_dir": self.workspace_dir,
                "disk_usage": disk_usage,
                "file_count": file_count,
                "connected": self._connected
            }
            
        except Exception as e:
            logger.error(f"Failed to get workspace info: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class SandboxAIContext:
    """
    Context manager for SandboxAI client
    
    Usage:
        with SandboxAIContext("workspace-123") as sandbox:
            result = sandbox.execute_code("print('hello')")
    """
    
    def __init__(self, workspace_id: str, **kwargs):
        """
        Initialize context manager
        
        Args:
            workspace_id: Unique identifier for the workspace
            **kwargs: Additional configuration options (passed to SandboxAIClient)
        """
        self.client = SandboxAIClient(workspace_id, **kwargs)
    
    def __enter__(self) -> SandboxAIClient:
        """Enter context and connect to sandbox"""
        self.client.connect()
        return self.client
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and disconnect from sandbox"""
        self.client.disconnect()
        return False


def create_sandbox_client(workspace_id: str, **kwargs) -> SandboxAIClient:
    """
    Factory function to create a sandbox client
    
    Args:
        workspace_id: Unique identifier for the workspace
        **kwargs: Additional configuration options
        
    Returns:
        SandboxAIClient instance
    """
    return SandboxAIClient(workspace_id, **kwargs)


# Compatibility aliases for easier migration from Daytona
DaytonaClient = SandboxAIClient  # Alias for drop-in replacement
create_daytona_client = create_sandbox_client  # Alias for factory function
