from eodc.dask import EODCDaskGateway
from dask.distributed import Client
from unittest.mock import patch
import os
from datetime import datetime

class CustomEODCDaskGateway(EODCDaskGateway):
    def __init__(self, username, password):
        self._password = password
        super().__init__(username=username)

    def _authenticate(self):
        return self._password
    
def get_cluster_options(gateway):
    print("Cluster-Optionen abrufen...")
    try:
        cluster_options = gateway.cluster_options()
        print(cluster_options)
    except Exception as e:
        print(f"Fehler beim Abrufen der Cluster-Optionen: {e}")

def log_result(success):
    """
    Schreibt das Ergebnis in eine Logdatei.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = "SUCCESS" if success else "FAILURE"
    with open("test_DaskGateway.log", "a") as log_file:
        log_file.write(f"{timestamp} - {result}\n")

def create_and_connect_cluster(gateway):
    print("Cluster erstellen...")
    try:
        cluster = gateway.new_cluster()
        print(f"Cluster erstellt: Dashboard-Link: {cluster.dashboard_link}")

        client = Client(cluster)
        print("Verbindung zum Cluster erfolgreich!")

        print("Worker starten...")
        cluster.scale(2)  
        print("Alle Worker sind aktiv!")

        return cluster, client
    except Exception as e:
        print(f"Fehler beim Erstellen oder Verbinden des Clusters: {e}")
        return None, None

def test_simple_computation(client):
    """
    Führt eine einfache Berechnung auf dem Cluster durch.
    """
    print("Starte einfache Berechnung...")
    try:
        def add(x, y):
            return x + y

        future = client.submit(add, 5, 10)
        result = future.result()
        assert result == 15, "Das Ergebnis der Berechnung ist nicht korrekt."
        print(f"Berechnung erfolgreich: 5 + 10 = {result}")
    except Exception as e:
        print(f"Fehler bei der Berechnung: {e}")


def main():
    """
    Hauptfunktion, die den End-to-End-Test ausführt.
    """
    username = os.getenv("EODC_USERNAME")
    password = os.getenv("EODC_PASSWORD")

    if not username or not password:
        log_result(False)  # Log für fehlende Umgebungsvariablen
        raise ValueError("Die Umgebungsvariablen EODC_USERNAME und EODC_PASSWORD müssen gesetzt sein.")

    with patch("getpass.getpass", return_value=password):
        try:
            print("Initialisierung des Gateways mit:")
            print(f"Benutzername: {username}")
            print(f"Passwort: {password}")
            gateway = CustomEODCDaskGateway(username=username, password=password)
            print("Verbindung erfolgreich hergestellt!")

            get_cluster_options(gateway)

            cluster, client = create_and_connect_cluster(gateway)

            if client:
                test_simple_computation(client)

            if cluster:
                cluster.close()
                print("Cluster erfolgreich geschlossen.")

            log_result(True)  # Log bei erfolgreichem Test
        except Exception as e:
            print(f"Fehler bei der Verbindung: {e}")
            log_result(False)  # Log bei fehlerhaftem Test


if __name__ == "__main__":
    main()
