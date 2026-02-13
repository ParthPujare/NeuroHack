import os
import sys
import subprocess
import shutil
import platform

def print_step(step):
    print(f"\n\033[1;36m[STEP] {step}\033[0m")

def print_success(msg):
    print(f"\033[1;32m[SUCCESS] {msg}\033[0m")

def print_warning(msg):
    print(f"\033[1;33m[WARNING] {msg}\033[0m")

def print_error(msg):
    print(f"\033[1;31m[ERROR] {msg}\033[0m")

def run_command(command, cwd=None):
    try:
        # Use shell=True if the command is a string, otherwise shell=False for list
        is_shell = isinstance(command, str)
        subprocess.check_call(command, cwd=cwd, shell=is_shell)
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {command}")
        sys.exit(1)
    except FileNotFoundError:
        cmd_name = command[0] if isinstance(command, list) else command.split()[0]
        print_error(f"Command not found: {cmd_name}")
        sys.exit(1)

def check_requirements():
    print_step("Checking prerequisites...")
    
    # Check Python
    python_version = sys.version.split()[0]
    print(f"Python version: {python_version}")
    if sys.version_info < (3, 9):
        print_error("Python 3.9+ is required.")
        sys.exit(1)

    # Check Node.js
    try:
        node_version_raw = subprocess.check_output(["node", "-v"], text=True).strip()
        print(f"Node.js version: {node_version_raw}")
        
        # Simple version check (v18+)
        major_version = int(node_version_raw.lstrip('v').split('.')[0])
        if major_version < 18:
            print_warning("Node.js v18+ is recommended. Your version might cause issues.")
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError):
        print_error("Node.js is not installed. Please install Node.js (v18+ recommended).")
        sys.exit(1)

def setup_python_env():
    print_step("Setting up Python virtual environment...")
    
    venv_dir = ".venv"
    if not os.path.exists(venv_dir):
        print("Creating .venv...")
        run_command([sys.executable, "-m", "venv", venv_dir])
    else:
        print(".venv already exists.")

    # Determine pip path
    if platform.system() == "Windows":
        pip_cmd = os.path.join(venv_dir, "Scripts", "pip")
    else:
        pip_cmd = os.path.join(venv_dir, "bin", "pip")

    print_step("Installing Python dependencies...")
    if os.path.exists("requirements.txt"):
        run_command([pip_cmd, "install", "-r", "requirements.txt"])
        print_success("Python dependencies installed.")
    else:
        print_warning("requirements.txt not found. Skipping dependency installation.")

def setup_env_file():
    print_step("Configuring environment variables...")
    
    env_vars = [
        "GOOGLE_API_KEY",
        "NEO4J_URI",
        "NEO4J_PASSWORD",
        "NEO4J_USER",
        "GROQ_API_KEY",
        "DB_USER",
        "DB_PASSWORD",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME"
    ]

    current_env = {}
    if os.path.exists(".env"):
        print("Loading existing .env...")
        with open(".env", "r") as f:
            for line in f:
                if "=" in line:
                    key, val = line.strip().split("=", 1)
                    current_env[key] = val

    new_env = {}
    for var in env_vars:
        default_val = current_env.get(var, "")
        user_input = input(f"{var} [{default_val}]: ").strip()
        new_env[var] = user_input if user_input else default_val

    with open(".env", "w") as f:
        for key, val in new_env.items():
            f.write(f"{key}={val}\n")
    
    print_success(".env file updated.")

def setup_frontend():
    print_step("Setting up Frontend...")
    
    frontend_dir = "frontend"
    if not os.path.exists(frontend_dir):
        print_error(f"Frontend directory '{frontend_dir}' not found.")
        return

    # Detect package manager
    pkg_manager = "npm"
    if shutil.which("pnpm"):
        pkg_manager = "pnpm"
    elif shutil.which("yarn"):
        pkg_manager = "yarn"
    
    print(f"Using package manager: {pkg_manager}")
    
    # Install dependencies
    print("Installing frontend dependencies...")
    run_command([pkg_manager, "install"], cwd=frontend_dir)
    print_success("Frontend dependencies installed.")

def main():
    print("\n===========================================")
    print("   Sekhmet (NeuroHack) Installer Setup   ")
    print("===========================================\n")
    
    check_requirements()
    setup_python_env()
    setup_env_file()
    setup_frontend()
    
    print("\n===========================================")
    print("   Installation Complete!   ")
    print("===========================================\n")
    print("To start the application:")
    
    print("\n1. Start the Backend (in a new terminal):")
    if platform.system() == "Windows":
        print("   .venv\\Scripts\\activate")
    else:
        print("   source .venv/bin/activate")
    print("   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload")
    
    print("\n2. Start the Frontend (in a separate terminal):")
    print("   cd frontend")
    print("   npm run dev  # or pnpm dev / yarn dev")
    print("\n===========================================")

if __name__ == "__main__":
    main()
