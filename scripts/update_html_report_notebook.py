import os
from datetime import datetime

LOG_FILE = "results/logs/latest_test.log"
HTML_FILE = "docs/index.html"

def parse_logs(log_file):
    """Parse the log file and return a dictionary of notebooks with their statuses and errors."""
    notebooks_status = {}

    if not os.path.exists(log_file):
        print(f"Log file not found: {log_file}")
        return notebooks_status

    with open(log_file, "r") as file:
        for line in file:
            parts = line.strip().split(", ")
            if len(parts) < 3:
                continue

            notebook_name = parts[0]
            status = parts[1]
            error_message = parts[2] if len(parts) > 2 else "N/A"

            # Update or add notebook status
            notebooks_status[notebook_name] = {
                "status": status,
                "error": error_message,
            }

    return notebooks_status

def generate_html(notebooks_status, html_file):
    """Generate an HTML file displaying the notebooks and their statuses and errors."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logo_path = "eodc_logo_2025.png"  # Adjust the path if necessary

    # Count statuses for summary
    summary = {"SUCCESS": 0, "FAILURE": 0}
    for data in notebooks_status.values():
        summary[data["status"].upper()] = summary.get(data["status"].upper(), 0) + 1

    total = len(notebooks_status)
    success_percentage = (summary["SUCCESS"] / total) * 100 if total else 0
    failure_percentage = (summary["FAILURE"] / total) * 100 if total else 0

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Notebook Test Results</title>
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
            table {{
                width: 100%;
                max-width: 600px;
                border-collapse: collapse;
                margin-top: 20px;
                margin-left: auto;
                margin-right: auto;
            }}
            th, td {{
                padding: 10px;
                text-align: left;
                border: 1px solid #ddd;
            }}
            th {{
                background-color: #f4f4f4;
            }}
            .success {{
                color: green;
                font-weight: bold;
            }}
            .failure {{
                color: red;
                font-weight: bold;
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
                <img src="{logo_path}" alt="Company Logo">
                <span>Notebook Test Results</span>
            </div>
            <div class="chartContainer">
                <div class="chartBar">
                    <div class="barLabel">Success</div>
                    <div class="bar success" style="width: {success_percentage}%;"></div>
                    <span>{summary['SUCCESS']} Success</span>
                </div>
                <div class="chartBar">
                    <div class="barLabel">Failure</div>
                    <div class="bar failure" style="width: {failure_percentage}%;"></div>
                    <span>{summary['FAILURE']} Failure</span>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Notebook</th>
                        <th>Status</th>
                        <th>Error Message</th>
                    </tr>
                </thead>
                <tbody>
    """

    for notebook, data in notebooks_status.items():
        status_class = "success" if data["status"].lower() == "success" else "failure"
        error_message = data["error"] or "N/A"
        html_content += f"""
        <tr>
            <td>{notebook}</td>
            <td class="{status_class}">{data['status']}</td>
            <td>{error_message}</td>
        </tr>
        """

    html_content += f"""
                </tbody>
            </table>
            <footer>
                Generated on {timestamp}.
            </footer>
        </div>
    </body>
    </html>
    """

    with open(html_file, "w") as file:
        file.write(html_content)

def main():
    notebooks_status = parse_logs(LOG_FILE)
    if not notebooks_status:
        print("No notebook data found. Exiting.")
        return

    generate_html(notebooks_status, HTML_FILE)
    print(f"HTML report generated: {HTML_FILE}")

if __name__ == "__main__":
    main()
