import os
from datetime import datetime

LOG_FILE = "results/logs/test_notebooks.log"
HTML_FILE = "docs/index_notebook.html"

def parse_logs(log_file):
    """Parse the log file and extract notebook statuses."""
    notebook_status = []
    
    if not os.path.exists(log_file):
        print(f"Log file not found: {log_file}")
        return notebook_status

    with open(log_file, "r") as file:
        for line in file:
            # Split log line into parts
            parts = line.strip().split(" - ", maxsplit=4)

            if len(parts) == 3:  # SUCCESS or SKIPPED
                _, status, notebook_path = parts
                notebook_status.append({
                    "notebook": notebook_path,
                    "status": status,
                    "error": None,  # No error for SUCCESS or SKIPPED
                })
            elif len(parts) == 4:  # FAILURE
                _, status, error_message, notebook_path = parts
                notebook_status.append({
                    "notebook": notebook_path,
                    "status": status,
                    "error": error_message,
                })
            else:
                print(f"Skipping malformed line: {line.strip()}")

    return notebook_status

def generate_html(notebook_status, html_file):
    """Generate an HTML report displaying the notebook statuses."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Count statuses for summary
    summary = {"SUCCESS": 0, "FAILURE": 0, "SKIPPED": 0}
    for notebook in notebook_status:
        summary[notebook["status"]] = summary.get(notebook["status"], 0) + 1

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Notebook Test Status</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ text-align: center; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f4f4f4; }}
            .success {{ color: green; font-weight: bold; }}
            .failure {{ color: red; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>Notebook Test Status</h1>
        <p><strong>Test Time:</strong> {timestamp}</p>
        <table>
            <tr>
                <th>Notebook</th>
                <th>Status</th>
                <th>Error</th>
            </tr>
    """

    for notebook in notebook_status:
        status_class = "success" if notebook["status"] in {"SUCCESS", "SKIPPED"} else "failure"
        error_message = notebook["error"] or "N/A"
        
        html_content += f"""
            <tr>
                <td>{notebook['notebook']}</td>
                <td class="{status_class}">{notebook['status']}</td>
                <td>{error_message}</td>
            </tr>
        """

    html_content += """
        </table>
    </body>
    </html>
    """

    with open(html_file, "w") as file:
        file.write(html_content)

def main():
    notebook_status = parse_logs(LOG_FILE)
    if not notebook_status:
        print("No notebook data found. Exiting.")
        return
    
    generate_html(notebook_status, HTML_FILE)
    print(f"HTML report generated: {HTML_FILE}")

if __name__ == "__main__":
    main()
