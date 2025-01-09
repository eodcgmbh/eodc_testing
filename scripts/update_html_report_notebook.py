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
            parts = line.strip().split(" - ", maxsplit=3)
            if len(parts) < 3:
                print(f"Skipping malformed line: {line.strip()}")
                continue
            
            timestamp = parts[0]
            status = parts[1]
            notebook_path = parts[2]
            error_message = parts[3] if len(parts) == 4 else None

            notebook_status.append({
                "timestamp": timestamp,
                "status": status,
                "notebook": notebook_path,
                "error": error_message,
            })

    return notebook_status

def generate_html(notebook_status, html_file):
    """Generate an HTML report displaying the notebook statuses."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Notebook Test Results</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 10px; text-align: left; border: 1px solid #ddd; }}
            th {{ background-color: #f4f4f4; }}
            .success {{ color: green; font-weight: bold; }}
            .failure {{ color: red; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>Notebook Test Results</h1>
        <p>Report generated on: {timestamp}</p>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Status</th>
                    <th>Notebook</th>
                    <th>Error</th>
                </tr>
            </thead>
            <tbody>
    """

    for notebook in notebook_status:
        status_class = "success" if notebook["status"] == "SUCCESS" else "failure"
        error_message = notebook["error"] or "N/A"
        html_content += f"""
        <tr>
            <td>{notebook['timestamp']}</td>
            <td class="{status_class}">{notebook['status']}</td>
            <td>{notebook['notebook']}</td>
            <td>{error_message}</td>
        </tr>
        """

    html_content += """
            </tbody>
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
