import os
import nbformat
from datetime import datetime
from nbformat.reader import NotJSONError
import subprocess

NOTEBOOK_DIR = "notebooks"
LOG_DIR = "results/logs"
LOG_FILE = os.path.join(LOG_DIR, "test_notebooks.log")
VENV_DIR = ".venv"

def setup_log_directory():
    """Ensure the log directory exists."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

def log_message(notebook_path, status, details=""):
    """Log messages in a consistent format."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    notebook_relative_path = os.path.relpath(notebook_path, NOTEBOOK_DIR)
    log_entry = f"{timestamp} - {status} - {details} - {notebook_relative_path}"
    print(log_entry)
    with open(LOG_FILE, "a") as log:
        log.write(log_entry + "\n")

def setup_virtual_environment():
    """Create and activate a virtual environment, then install dependencies."""
    if not os.path.exists(VENV_DIR):
        try:
            subprocess.check_call(["python", "-m", "venv", VENV_DIR])
            print(f"Virtual environment created in {VENV_DIR}")
        except subprocess.CalledProcessError as e:
            print(f"Error creating virtual environment: {e}")
            return False
    try:
        pip_path = os.path.join(VENV_DIR, "bin", "pip")  
        if os.name == "nt":  # Windows
            pip_path = os.path.join(VENV_DIR, "Scripts", "pip")
        subprocess.check_call([pip_path, "install", "--upgrade", "pip"])
        subprocess.check_call([pip_path, "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False
    return True

def extract_imports_from_notebook(notebook_path):
    """Extract all import statements from a Jupyter notebook."""
    try:
        with open(notebook_path, 'r', encoding='utf-8') as nb_file:
            notebook = nbformat.read(nb_file, as_version=4)
        
        imports = []
        for cell in notebook.cells:
            if cell.cell_type == 'code':
                for line in cell.source.split("\n"):
                    stripped_line = line.strip()
                    if stripped_line.startswith("import ") or stripped_line.startswith("from "):
                        imports.append(stripped_line)
        return imports
    except NotJSONError:
        log_message(notebook_path, "INVALID", "Not a valid JSON notebook")
        return None

def check_notebook(notebook_path):
    """Check a notebook for import errors."""
    imports = extract_imports_from_notebook(notebook_path)
    
    if imports is None:
        return
    elif imports:
        try:
            for statement in imports:
                exec(statement)
            log_message(notebook_path, "SUCCESS", "All imports executed successfully")
        except Exception as e:
            log_message(notebook_path, "FAILURE", f"Import Error: {str(e)}")
    else:
        log_message(notebook_path, "SKIPPED", "No imports found in notebook")

def main():
    setup_log_directory()

    if not setup_virtual_environment():
        log_message("Environment Setup", "ERROR", "Failed to create or set up virtual environment")
        return

    if not os.path.exists(NOTEBOOK_DIR):
        log_message(NOTEBOOK_DIR, "ERROR", "Notebook directory does not exist")
        return

    for root, _, files in os.walk(NOTEBOOK_DIR):
        for file in files:
            if file.endswith(".ipynb"):
                notebook_path = os.path.join(root, file)
                check_notebook(notebook_path)

if __name__ == "__main__":
    main()
