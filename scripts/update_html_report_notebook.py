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
        <title>Notebook Test Status</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                padding: 0;
                box-sizing: border-box;
            }}
            .pageContainer {{
                max-width: 800px;
                margin: auto;
            }}
            .headline {{
                display: flex;
                align-items: center;
                gap: 20px;
                margin-bottom: 30px;
            }}
            .headline img {{
                width: 150px;
            }}
            .headline span {{
                font-size: 24px;
                font-weight: bold;
            }}
            .statusContainer {{
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 15px;
                background-color: #f9f9f9;
            }}
            .statusHeader {{
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .statusTitle {{
                font-size: 18px;
                margin: 0;
            }}
            .statusHeadline {{
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
            }}
            .success {{
                color: white;
                background-color: green;
            }}
            .failure {{
                color: white;
                background-color: red;
            }}
            .statusSubtitle {{
                margin-top: 10px;
                font-size: 14px;
                color: #555;
            }}
            footer {{
                text-align: center;
                margin-top: 20px;
                font-size: 12px;
                color: #aaa;
            }}
        </style>
    </head>
    <body>
        <div class="pageContainer">
            <div class="headline">
                <img src="eodc_logo2025.png" alt="Company Logo" />
                <span>Notebook Test Status</span>
            </div>
            <div id="reports" class="reportContainer">
    """

    for notebook in notebook_status:
        status_class = "success" if notebook["status"] == "SUCCESS" else "failure"
        error_message = notebook["error"] or "N/A"
        html_content += f"""
            <div class="statusContainer">
                <div class="statusHeader">
                    <h6 class="statusTitle">{notebook['notebook']}</h6>
                    <div class="{status_class} statusHeadline">{notebook['status']}</div>
                </div>
                <div class="statusSubtitle">
                    <div><strong>Timestamp:</strong> {notebook['timestamp']}</div>
                    <div><strong>Error:</strong> {error_message}</div>
                </div>
            </div>
        """

    html_content += f"""
            </div>
            <footer>
                Generated on {timestamp}.
                <br />
                Forked from
                <a href="https://github.com/statsig-io/statuspage/">
                    Statsig's Open-Source Status Page</a>.
            </footer>
        </div>
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
