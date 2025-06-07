import subprocess
import tempfile
import os
import json
import sys

def run_cpp_directly(code_str, input_str=""):
    """
    Compile and run C++ code directly without using isolate
    """
    result = {
        "status": "Unknown",
        "output": "",
        "error": "",
        "meta": {}
    }
    
    # Create temporary files
    with tempfile.TemporaryDirectory() as temp_dir:
        cpp_file = os.path.join(temp_dir, "main.cpp")
        exe_file = os.path.join(temp_dir, "main")
        input_file = os.path.join(temp_dir, "input.txt")
        
        # Write code and input to files
        with open(cpp_file, "w") as f:
            f.write(code_str)
        
        with open(input_file, "w") as f:
            f.write(input_str)
        
        # Compile the code
        compile_cmd = ["g++", cpp_file, "-o", exe_file, "-std=c++17", "-O2"]
        compile_result = subprocess.run(compile_cmd, capture_output=True, text=True)
        
        if compile_result.returncode != 0:
            result["status"] = "Compilation Error"
            result["error"] = compile_result.stderr
            return result
        
        # Run the executable
        try:
            with open(input_file, "r") as input_f:
                run_result = subprocess.run(
                    [exe_file], 
                    stdin=input_f,
                    capture_output=True, 
                    text=True,
                    timeout=5  # 5 second timeout
                )
            
            result["status"] = "Success" if run_result.returncode == 0 else "Runtime Error"
            result["output"] = run_result.stdout
            result["error"] = run_result.stderr
            result["meta"] = {"exitcode": run_result.returncode}
            
        except subprocess.TimeoutExpired:
            result["status"] = "Time Limit Exceeded"
            result["error"] = "Execution timed out after 5 seconds"
        
        except Exception as e:
            result["status"] = "Error"
            result["error"] = str(e)
    
    return result

if __name__ == "__main__":
    # Use the same sample code from test_run.py
    sample_code = """
    #include <iostream>
    using namespace std;
    int main() {
        int a = 2, b = 3;
        cout << a + b << endl;
        return 0;
    }
    """
    
    # Handle arguments if provided, otherwise use sample code
    if len(sys.argv) > 1:
        # Check if we're using file or string input
        if os.path.exists(sys.argv[1]):
            with open(sys.argv[1], "r") as f:
                code = f.read()
        else:
            code = sys.argv[1]
            
        # Handle optional input
        input_data = ""
        if len(sys.argv) > 2:
            if os.path.exists(sys.argv[2]):
                with open(sys.argv[2], "r") as f:
                    input_data = f.read()
            else:
                input_data = sys.argv[2]
    else:
        code = sample_code
        input_data = ""
    
    # Run the code and print the result
    result = run_cpp_directly(code, input_data)
    print(json.dumps(result, indent=4))
