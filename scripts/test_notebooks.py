import os
import nbformat
from datetime import datetime
from nbformat.reader import NotJSONError

NOTEBOOK_DIR = "notebooks"
LOG_DIR = "results/logs"
LOG_FILE = os.path.join(LOG_DIR, "test_notebooks.log")

def setup_log_directory():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

def log_message(notebook_path, status):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    notebook_relative_path = os.path.relpath(notebook_path, NOTEBOOK_DIR)
    log_entry = f"{timestamp} - {status} - {notebook_relative_path}"
    print(log_entry)
    with open(LOG_FILE, "a") as log:
        log.write(log_entry + "\n")

def extract_imports_from_notebook(notebook_path):
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
        log_message(notebook_path, "INVALID - Not a valid JSON notebook")
        return None

def check_notebook(notebook_path):
    imports = extract_imports_from_notebook(notebook_path)
    
    if imports is None:
        return
    elif imports:
        try:
            for statement in imports:
                exec(statement)
            log_message(notebook_path, "SUCCESS")
        except Exception as e:
            log_message(notebook_path, f"FAILURE - Import Error: {str(e)}")
    else:
        log_message(notebook_path, "SKIPPED - No Imports Found")

def main():
    setup_log_directory()

    if not os.path.exists(NOTEBOOK_DIR):
        log_message(NOTEBOOK_DIR, "ERROR - Notebook directory does not exist.")
        return

    for root, _, files in os.walk(NOTEBOOK_DIR):
        for file in files:
            if file.endswith(".ipynb"):
                notebook_path = os.path.join(root, file)
                check_notebook(notebook_path)

if __name__ == "__main__":
    main()
