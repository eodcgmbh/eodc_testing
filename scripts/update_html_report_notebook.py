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
            if len(parts) < 4:
                print(f"Skipping malformed line: {line.strip()}")
                continue
            
            timestamp = parts[0]
            status = parts[1]
            error_message = parts[2] if status == "FAILURE" else None
            notebook_path = parts[3] if status == "FAILURE" else parts[2]

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

    # Count statuses for summary
    summary = {"SUCCESS": 0, "FAILURE": 0, "SKIPPED": 0}
    for notebook in notebook_status:
        summary[notebook["status"]] = summary.get(notebook["status"], 0) + 1

    total = sum(summary.values())
    success_percentage = (summary["SUCCESS"] / total) * 100 if total > 0 else 0
    failure_percentage = (summary["FAILURE"] / total) * 100 if total > 0 else 0
    skipped_percentage = (summary["SKIPPED"] / total) * 100 if total > 0 else 0

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
            .chartContainer {{
                margin: 20px 0;
            }}
            .chartBar {{
                display: flex;
                align-items: center;
                margin-bottom: 10px;
            }}
            .barLabel {{
                width: 100px;
                font-weight: bold;
            }}
            .bar {{
                height: 20px;
                border-radius: 5px;
            }}
            .bar.success {{
                background-color: green;
            }}
            .bar.failure {{
                background-color: red;
            }}
            .bar.skipped {{
                background-color: gray;
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
            .skipped {{
                color: white;
                background-color: gray;
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
                <img src="eodc_logo_2025.png" alt="Company Logo" />
                <span>Notebook Test Status</span>
            </div>
            <div class="chartContainer">
                <div class="chartBar">
                    <div class="barLabel">Success</div>
                    <div class="bar success" style="width: {success_percentage}%;">{summary['SUCCESS']} ({success_percentage:.1f}%)</div>
                </div>
                <div class="chartBar">
                    <div class="barLabel">Failure</div>
                    <div class="bar failure" style="width: {failure_percentage}%;">{summary['FAILURE']} ({failure_percentage:.1f}%)</div>
                </div>
                <div class="chartBar">
                    <div class="barLabel">Skipped</div>
                    <div class="bar skipped" style="width: {skipped_percentage}%;">{summary['SKIPPED']} ({skipped_percentage:.1f}%)</div>
                </div>
            </div>
            <div id="reports" class="reportContainer">
    """

    for notebook in notebook_status:
        status_class = (
            "success" if notebook["status"] == "SUCCESS" 
            else "failure" if notebook["status"] == "FAILURE" 
            else "skipped"
        )
        error_message = notebook["error"] or "N/A"
        display_title = notebook["error"] if notebook["status"] == "FAILURE" else notebook["notebook"]
        
        html_content += f"""
            <div class="statusContainer">
                <div class="statusHeader">
                    <h6 class="statusTitle">{display_title}</h6>
                    <div class="{status_class} statusHeadline">{notebook['status']}</div>
                </div>
                <div class="statusSubtitle">
                    <div><strong>Timestamp:</strong> {notebook['timestamp']}</div>
                    <div><strong>Notebook:</strong> {notebook['notebook']}</div>
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
