#!/usr/bin/env python3
"""
SandboxAI Proof of Concept Test Script
Tests basic functionality of SandboxAI for SUNA integration
"""

import time
import sys

print("=" * 60)
print("SandboxAI Proof of Concept Test")
print("=" * 60)

# Test 1: Check if sandboxai-client is installed
print("\n[Test 1] Checking sandboxai-client installation...")
try:
    from sandboxai import Sandbox
    print("✅ sandboxai-client is installed")
except ImportError as e:
    print(f"❌ sandboxai-client is NOT installed: {e}")
    print("\nTo install, run:")
    print("  pip3 install sandboxai-client")
    sys.exit(1)

# Test 2: Check Docker availability
print("\n[Test 2] Checking Docker availability...")
import subprocess
try:
    result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(f"✅ Docker is available: {result.stdout.strip()}")
    else:
        print(f"❌ Docker command failed: {result.stderr}")
        sys.exit(1)
except FileNotFoundError:
    print("❌ Docker is NOT installed")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error checking Docker: {e}")
    sys.exit(1)

# Test 3: Basic Python code execution
print("\n[Test 3] Testing Python code execution...")
try:
    start_time = time.time()
    with Sandbox(embedded=True) as box:
        result = box.run_ipython_cell("print('Hello from SandboxAI!')")
        elapsed = time.time() - start_time
        
        if "Hello from SandboxAI!" in result.output:
            print(f"✅ Python execution works ({elapsed:.2f}s)")
            print(f"   Output: {result.output.strip()}")
        else:
            print(f"❌ Unexpected output: {result.output}")
except Exception as e:
    print(f"❌ Python execution failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Shell command execution
print("\n[Test 4] Testing shell command execution...")
try:
    with Sandbox(embedded=True) as box:
        result = box.run_shell_command("echo 'Shell test successful'")
        
        if "Shell test successful" in result.output:
            print("✅ Shell execution works")
            print(f"   Output: {result.output.strip()}")
        else:
            print(f"❌ Unexpected output: {result.output}")
except Exception as e:
    print(f"❌ Shell execution failed: {e}")

# Test 5: File operations
print("\n[Test 5] Testing file operations...")
try:
    with Sandbox(embedded=True) as box:
        # Write file
        box.run_ipython_cell("""
with open('/tmp/test_file.txt', 'w') as f:
    f.write('Test content from SandboxAI')
""")
        
        # Read file
        result = box.run_shell_command("cat /tmp/test_file.txt")
        
        if "Test content from SandboxAI" in result.output:
            print("✅ File operations work")
            print(f"   File content: {result.output.strip()}")
        else:
            print(f"❌ File read failed: {result.output}")
except Exception as e:
    print(f"❌ File operations failed: {e}")

# Test 6: Multiple operations in same sandbox
print("\n[Test 6] Testing multiple operations...")
try:
    with Sandbox(embedded=True) as box:
        # Operation 1
        box.run_ipython_cell("x = 42")
        
        # Operation 2 (should remember x)
        result = box.run_ipython_cell("print(f'The answer is {x}')")
        
        if "The answer is 42" in result.output:
            print("✅ State persistence works")
            print(f"   Output: {result.output.strip()}")
        else:
            print(f"❌ State not persisted: {result.output}")
except Exception as e:
    print(f"❌ Multiple operations failed: {e}")

# Test 7: Performance test
print("\n[Test 7] Performance test...")
try:
    iterations = 3
    total_time = 0
    
    for i in range(iterations):
        start_time = time.time()
        with Sandbox(embedded=True) as box:
            box.run_ipython_cell("import numpy as np; np.array([1,2,3])")
        elapsed = time.time() - start_time
        total_time += elapsed
        print(f"   Iteration {i+1}: {elapsed:.2f}s")
    
    avg_time = total_time / iterations
    print(f"✅ Average time: {avg_time:.2f}s")
    
    if avg_time < 5:
        print("   ⚡ Performance is good!")
    elif avg_time < 10:
        print("   ⚠️  Performance is acceptable")
    else:
        print("   ⚠️  Performance might be slow for production")
except Exception as e:
    print(f"❌ Performance test failed: {e}")

# Test 8: Error handling
print("\n[Test 8] Testing error handling...")
try:
    with Sandbox(embedded=True) as box:
        result = box.run_ipython_cell("1 / 0")  # This should raise ZeroDivisionError
        
        if "ZeroDivisionError" in result.output or "division by zero" in result.output.lower():
            print("✅ Error handling works")
            print(f"   Error captured: {result.output[:100]}...")
        else:
            print(f"⚠️  Error not captured as expected: {result.output}")
except Exception as e:
    print(f"✅ Exception raised as expected: {type(e).__name__}")

# Summary
print("\n" + "=" * 60)
print("Test Summary")
print("=" * 60)
print("""
✅ All basic tests completed!

Next steps:
1. Review test results above
2. If all tests passed, proceed with adapter development
3. If tests failed, check:
   - Docker is running: docker ps
   - Docker permissions: sudo usermod -aG docker $USER
   - SandboxAI installation: pip3 install sandboxai-client

For SUNA integration:
- See: /home/ubuntu/sandboxai_implementation_plan.md
- Adapter code: backend/core/sandbox/sandboxai_adapter.py
""")
print("=" * 60)
