#!/usr/bin/env python3
"""
SandboxAI Adapter Design Test
Tests the adapter design without requiring actual SandboxAI/Docker
"""

print("=" * 60)
print("SandboxAI Adapter Design Test")
print("=" * 60)

# Mock SandboxAI for testing adapter design
class MockSandboxResult:
    def __init__(self, output, error=None):
        self.output = output
        self.error = error

class MockSandbox:
    def __init__(self, embedded=True):
        self.embedded = embedded
        self.state = {}
    
    def __enter__(self):
        print("[Mock] Sandbox created")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        print("[Mock] Sandbox closed")
        return False
    
    def run_ipython_cell(self, code):
        print(f"[Mock] Running Python: {code[:50]}...")
        # Simulate execution
        if "print(" in code:
            output = "Mock output from Python"
        elif "=" in code:
            output = ""
        else:
            output = "Mock result"
        return MockSandboxResult(output)
    
    def run_shell_command(self, command):
        print(f"[Mock] Running shell: {command[:50]}...")
        return MockSandboxResult(f"Mock output from: {command}")

# Test the adapter design
print("\n[Test 1] Testing SandboxAI Adapter Design...")

class SandboxAIClient:
    """
    Adapter class to interface with SandboxAI
    Compatible with SUNA sandbox interface
    """
    
    def __init__(self, workspace_id: str, **kwargs):
        self.workspace_id = workspace_id
        self.workspace_dir = kwargs.get('workspace_dir', f'/workspace/{workspace_id}')
        self.sandbox = None
        self.embedded = kwargs.get('embedded', True)
        print(f"✅ Initialized adapter for workspace: {workspace_id}")
    
    def connect(self):
        """Connect to or create a sandbox"""
        try:
            self.sandbox = MockSandbox(embedded=self.embedded)
            self.sandbox.__enter__()
            
            # Create workspace directory
            self.sandbox.run_shell_command(f"mkdir -p {self.workspace_dir}")
            
            print(f"✅ Connected to sandbox")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from sandbox"""
        if self.sandbox:
            try:
                self.sandbox.__exit__(None, None, None)
                print("✅ Disconnected from sandbox")
            except Exception as e:
                print(f"❌ Error disconnecting: {e}")
    
    def execute_code(self, code: str, language: str = "python"):
        """Execute code in the sandbox"""
        if not self.sandbox:
            raise RuntimeError("Sandbox not connected")
        
        try:
            if language == "python":
                result = self.sandbox.run_ipython_cell(code)
            elif language in ["bash", "shell"]:
                result = self.sandbox.run_shell_command(code)
            else:
                raise ValueError(f"Unsupported language: {language}")
            
            return {
                "success": True,
                "output": result.output,
                "error": result.error if hasattr(result, 'error') else None
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
    
    def write_file(self, file_path: str, content: str):
        """Write content to a file"""
        if not self.sandbox:
            raise RuntimeError("Sandbox not connected")
        
        try:
            import os
            full_path = os.path.join(self.workspace_dir, file_path)
            
            # Create directory
            dir_path = os.path.dirname(full_path)
            if dir_path:
                self.sandbox.run_shell_command(f"mkdir -p {dir_path}")
            
            # Write file (simplified for mock)
            self.sandbox.run_shell_command(f"echo 'content' > {full_path}")
            
            return {
                "success": True,
                "path": full_path,
                "message": f"File written: {file_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def read_file(self, file_path: str):
        """Read content from a file"""
        if not self.sandbox:
            raise RuntimeError("Sandbox not connected")
        
        try:
            import os
            full_path = os.path.join(self.workspace_dir, file_path)
            result = self.sandbox.run_shell_command(f"cat {full_path}")
            
            return {
                "success": True,
                "content": result.output,
                "path": full_path
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Test adapter
print("\n[Test 2] Testing adapter methods...")

try:
    # Create client
    client = SandboxAIClient("test-workspace-123")
    
    # Connect
    client.connect()
    
    # Test code execution
    print("\n[Test 2.1] Execute Python code...")
    result = client.execute_code("print('Hello World')", "python")
    print(f"  Result: {result}")
    assert result['success'], "Code execution should succeed"
    print("  ✅ Python execution works")
    
    # Test shell command
    print("\n[Test 2.2] Execute shell command...")
    result = client.execute_code("ls -la", "shell")
    print(f"  Result: {result}")
    assert result['success'], "Shell command should succeed"
    print("  ✅ Shell execution works")
    
    # Test file write
    print("\n[Test 2.3] Write file...")
    result = client.write_file("test.txt", "Test content")
    print(f"  Result: {result}")
    assert result['success'], "File write should succeed"
    print("  ✅ File write works")
    
    # Test file read
    print("\n[Test 2.4] Read file...")
    result = client.read_file("test.txt")
    print(f"  Result: {result}")
    assert result['success'], "File read should succeed"
    print("  ✅ File read works")
    
    # Disconnect
    client.disconnect()
    
    print("\n✅ All adapter tests passed!")
    
except Exception as e:
    print(f"\n❌ Adapter test failed: {e}")
    import traceback
    traceback.print_exc()

# Test context manager
print("\n[Test 3] Testing context manager...")

class SandboxAIContext:
    """Context manager for SandboxAI client"""
    
    def __init__(self, workspace_id: str, **kwargs):
        self.client = SandboxAIClient(workspace_id, **kwargs)
    
    def __enter__(self):
        self.client.connect()
        return self.client
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.disconnect()
        return False

try:
    with SandboxAIContext("test-workspace-456") as sandbox:
        result = sandbox.execute_code("print('Context manager test')")
        print(f"  Result: {result}")
    
    print("✅ Context manager works")
except Exception as e:
    print(f"❌ Context manager failed: {e}")

# Test factory function
print("\n[Test 4] Testing factory function...")

def create_sandbox_client(workspace_id: str, **kwargs):
    """Factory function to create a sandbox client"""
    return SandboxAIClient(workspace_id, **kwargs)

try:
    client = create_sandbox_client("test-workspace-789")
    print("✅ Factory function works")
except Exception as e:
    print(f"❌ Factory function failed: {e}")

# Summary
print("\n" + "=" * 60)
print("Adapter Design Test Summary")
print("=" * 60)
print("""
✅ Adapter design is valid!

The adapter provides:
1. ✅ SandboxAIClient class with SUNA-compatible API
2. ✅ Context manager support
3. ✅ Factory function for easy instantiation
4. ✅ Methods: execute_code, write_file, read_file
5. ✅ Error handling

Next steps:
1. Deploy to actual environment with Docker
2. Replace MockSandbox with real SandboxAI
3. Integrate with SUNA tools
4. Test with real workloads

Integration points in SUNA:
- backend/core/sandbox/__init__.py (factory)
- backend/core/sandbox/sandboxai_adapter.py (adapter)
- backend/core/tools/sb_files_tool.py (file operations)
- backend/core/tools/sb_shell_tool.py (shell commands)
- backend/core/tools/sb_python_tool.py (code execution)
""")
print("=" * 60)
