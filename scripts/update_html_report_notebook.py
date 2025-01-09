import os
from datetime import datetime

# Pfad zur Logdatei
LOG_FILE = "results/logs/test_notebooks.log"
HTML_FILE = "docs/index_notebook.html"

def parse_logs(log_file):
    """Parst die Logdatei und extrahiert relevante Informationen."""
    if not os.path.exists(log_file):
        return []
    
    results = []
    with open(log_file, "r") as file:
        for line in file:
            # Beispiel: 2025-01-09 10:12:06 - SUCCESS - demos/workspaces/demo-create-workspace.ipynb
            parts = line.strip().split(" - ")
            if len(parts) >= 3:
                timestamp, status, notebook = parts
                results.append({"timestamp": timestamp, "status": status, "notebook": notebook})
    return results

def generate_html_report(results):
    """Generiert eine HTML-Seite basierend auf den Testergebnissen."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Notebook Test Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f4f4f4; }}
            .success {{ color: green; }}
            .failure {{ color: red; }}
            .skipped {{ color: orange; }}
        </style>
    </head>
    <body>
        <h1>Notebook Test Report</h1>
        <p>Generated on {timestamp}</p>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Status</th>
                    <th>Notebook</th>
                </tr>
            </thead>
            <tbody>
    """
    for result in results:
        status_class = result["status"].lower()  # e.g., success, failure, skipped
        html_content += f"""
        <tr>
            <td>{result['timestamp']}</td>
            <td class="{status_class}">{result['status']}</td>
            <td>{result['notebook']}</td>
        </tr>
        """
    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """
    return html_content

def main():
    # Logs parsen
    results = parse_logs(LOG_FILE)

    # HTML-Bericht erstellen
    html_report = generate_html_report(results)

    # HTML-Datei speichern
    os.makedirs(os.path.dirname(HTML_FILE), exist_ok=True)
    with open(HTML_FILE, "w") as file:
        file.write(html_report)

if __name__ == "__main__":
    main()
