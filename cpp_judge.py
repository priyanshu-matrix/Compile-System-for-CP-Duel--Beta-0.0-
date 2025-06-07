import subprocess
import os
import sys
import json





def run_cpp_in_isolate(code: str, test_input: str):
    box_id = "0"
    # base_dir_host = f"/app" # This line is replaced
    # box_dir_host = os.path.join(base_dir_host, "box") # This line is replaced

    # Set box_dir_host to the actual path used by isolate for the box's content directory,
    # based on the described structure /run/isolate/<box_id>/box
    # box_dir_host = f"/run/isolate/{box_id}/box" # Incorrect path
    box_dir_host = f"/var/local/lib/isolate/{box_id}/box"  # Corrected path for isolate

    cpp_file_name = "main.cpp"
    input_file_name = "input.txt"
    output_file_name = "output.txt"
    error_file_name = "error.txt"
    meta_file_name = "meta.txt"
    executable_name = "main"

    cpp_file_path = os.path.join(box_dir_host, cpp_file_name)
    input_file_path = os.path.join(box_dir_host, input_file_name)
    output_file_path = os.path.join(box_dir_host, output_file_name)
    error_file_path = os.path.join(box_dir_host, error_file_name)
    meta_file_path = os.path.join(box_dir_host, meta_file_name)

    subprocess.run(["isolate", "--box-id", box_id, "--init"], capture_output=True)

    try:
        os.makedirs(box_dir_host, exist_ok=True)
        with open(cpp_file_path, "w") as f:
            f.write(code)
        with open(input_file_path, "w") as f:
            f.write(test_input)

        # Compile the code inside isolate
        compile_cmd = [
            "isolate",
            "--box-id",
            box_id,
            "--processes=10",
            "--wall-time=1",  # Compilation wall time limit (seconds)
            "--time=1",       # Compilation CPU time limit (seconds)
            "--mem=524288",    # Compilation memory limit (KB)
            "--share-net",
            "--env=PATH=/usr/bin:/bin:/usr/local/bin",  # Corrected format for setting env var
            "--run",
            "--",
            "/usr/bin/g++",
            cpp_file_name,
            "-o",
            executable_name,
            "-std=c++17",
            "-O2",
            "-march=native",
        ]
        compile_result = subprocess.run(compile_cmd, capture_output=True, text=True)

        if compile_result.returncode != 0:
            return {
            "status": "Compilation Error",
            "output": "",
            "error": compile_result.stderr.strip() or compile_result.stdout.strip(),
            "meta": {},
            }

        # Run the compiled program
        run_cmd = [
            "isolate",
            "--box-id",
            box_id,
            f"--stdin={input_file_name}",
            f"--stdout={output_file_name}",
            f"--stderr={error_file_name}",
            f"--meta={meta_file_name}",
            "--time=1",        # ⭐ EXECUTION TIME LIMIT: CPU time in seconds (increased from 10 to 30)
            "--wall-time=1",   # ⭐ EXECUTION WALL TIME LIMIT: Real time in seconds (increased from 20 to 60)
            "--mem=2097152",    # ⭐ EXECUTION MEMORY LIMIT: Memory in KB (2 GB, increased from 1 GB)
            "--fsize=20480",    # File size limit (KB) (doubled)
            "--processes=5",    # Process limit (increased from 3 to 5)
            "--share-net",      # Re-added to fix network interface configuration error
            "--run",
            "--",
            f"/box/{executable_name}",
        ]
        run_result = subprocess.run(run_cmd, capture_output=True, text=True)

        # ✅ Now read the outputs
        output = (
            open(output_file_path).read().strip()
            if os.path.exists(output_file_path)
            else ""
        )
        # This 'error_from_program_file' is from the program's stderr file.
        error_from_program_file = (
            open(error_file_path).read().strip()
            if os.path.exists(error_file_path)
            else ""
        )
        meta = {}
        if os.path.exists(meta_file_path):
            with open(meta_file_path) as f:
                for line in f:
                    if ":" in line:
                        k, v = line.strip().split(":", 1)
                        meta[k] = v

        # Determine status and final error string
        current_status = "Runtime Error"  # Default status
        final_error_to_report = (
            error_from_program_file  # Default error is program's stderr
        )

        meta_status_val = meta.get("status")
        if meta_status_val == "OK":
            current_status = "Success"
        elif meta_status_val == "TO":
            current_status = "Time Limit Exceeded"
        elif meta_status_val == "SG":
            current_status = "Runtime Error (Signal)"
            # Add signal number if available
            if "exitsig" in meta:
                current_status = f"Runtime Error (Signal {meta.get('exitsig')})"
        elif meta_status_val == "RE":
            current_status = f"Runtime Error ({meta.get('message', 'Generic')})"
        elif meta_status_val == "ML":
            current_status = "Memory Limit Exceeded"

        # Fallback logic if meta didn't set a definitive status, or meta is empty
        if current_status == "Runtime Error":  # If status is still the default
            if run_result.returncode == 0:
                if (
                    not error_from_program_file
                ):  # Program exited 0, no stderr from program
                    current_status = "Success"
                # else: Program exited 0, but wrote to stderr. Status remains "Runtime Error"
                # (or could be "Success with program stderr" depending on desired behavior)
            else:  # run_result.returncode != 0 (isolate reported an error for the run itself)
                current_status = "Runtime Error (Execution Failed)"
                # If program's stderr is empty, use isolate's stderr for more info
                if not final_error_to_report:
                    final_error_to_report = (
                        run_result.stderr.strip()
                        or run_result.stdout.strip()
                        or "Unknown execution error"
                    )

        # For cases where meta *did* set a status (e.g., TO, SG),
        # final_error_to_report is already error_from_program_file. This is generally desired.

        return {
            "output": output,
            "status": current_status,
            "error": final_error_to_report,
            "meta": meta,
        }

    finally:
        subprocess.run(
            ["isolate", "--box-id", box_id, "--cleanup"], capture_output=True
        )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <code.cpp> <input.txt>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        code = f.read()
    with open(sys.argv[2]) as f:
        input_data = f.read()

    result = run_cpp_in_isolate(code, input_data)
    print(json.dumps(result, indent=4))
