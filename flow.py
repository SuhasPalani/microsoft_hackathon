import subprocess

def run_script(script_name):
    print(f"Running {script_name}...")
    result = subprocess.run(["python3", script_name], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"{script_name} completed successfully.\n")
    else:
        print(f"Error in {script_name}:\n{result.stderr}")
        exit(result.returncode)  # stop execution if a script fails

if __name__ == "__main__":
    scripts = [
        "simulate_data.py",
        "extract_policy.py",
        "main.py",
        "retri.py"
    ]

    for script in scripts:
        run_script(script)
