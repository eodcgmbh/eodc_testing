import os
from datetime import datetime

LOG_FILE = "results/logs/latest_test.log"
HTML_FILE = "docs/index.html"

def parse_logs(log_file):
    """Parse the log file and return a dictionary of collections with their statuses."""
    collections_status = {}

    if not os.path.exists(log_file):
        print(f"Log file not found: {log_file}")
        return collections_status

    with open(log_file, "r") as file:
        for line in file:
            parts = line.strip().split(", ")
            if len(parts) < 3:
                continue

            timestamp = parts[0]
            status = parts[1]
            collection_info = [p.split(": ")[1] for p in parts if p.startswith("collection")]
            collection_id = collection_info[0] if collection_info else "Unknown"

            # Update or add collection status
            collections_status[collection_id] = {
                "status": status,
                "last_tested": timestamp
            }

    return collections_status

def generate_html(collections_status, html_file):
    """Generate an HTML file displaying the collections and their statuses."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logo_path = "eodc_logo_2025.png"  # Adjust the path if necessary

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>STAC API Test Results</title>
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
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
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
                <span>STAC API Test Results</span>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Collection</th>
                        <th>Status</th>
                        <th>Last Tested</th>
                    </tr>
                </thead>
                <tbody>
    """

    for collection, data in collections_status.items():
        status_class = "success" if data["status"] == "success" else "failure"
        html_content += f"""
        <tr>
            <td>{collection}</td>
            <td class="{status_class}">{data['status']}</td>
            <td>{data['last_tested']}</td>
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
    collections_status = parse_logs(LOG_FILE)
    if not collections_status:
        print("No collections data found. Exiting.")
        return

    generate_html(collections_status, HTML_FILE)
    print(f"HTML report generated: {HTML_FILE}")

if __name__ == "__main__":
    main()
