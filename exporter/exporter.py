from flask import Flask, Response
from prometheus_client import Gauge, generate_latest
import requests
import time
import threading
import collections

app = Flask(__name__)

# Metriky
total_vehicles = Gauge('tollgate_vehicles_total', 'Total vehicles per gate', ['gate'])
vehicle_type_total = Gauge('tollgate_vehicle_type_total', 'Total vehicles by type per gate', ['gate', 'type'])

API_URL = 'http://tollgate_api:8001/prujezdy'

# Interní úložiště
counts = collections.defaultdict(lambda: {'total': 0, 'types': collections.defaultdict(int)})

def update_metrics():
    while True:
        try:
            # Načítání dat z API
            response = requests.get(API_URL)
            data = response.json()

            # Reset mezi dotazy
            counts.clear()

            # Zpracování dat z každé brány
            for entry in data['prujezdy']:
                gate = entry.get('brana')
                vehicle_counts = entry.get('pocty', {})

                if gate and vehicle_counts:
                    # Celkový počet vozidel na bráně
                    total_vehicles_count = sum(vehicle_counts.values())
                    counts[gate]['total'] += total_vehicles_count

                    # Počet vozidel podle typu
                    for vtype, count in vehicle_counts.items():
                        counts[gate]['types'][vtype] += count

            # Aktualizace Prometheus metrik
            for gate, gate_data in counts.items():
                total_vehicles.labels(gate=gate).set(gate_data['total'])
                for vtype, count in gate_data['types'].items():
                    vehicle_type_total.labels(gate=gate, type=vtype).set(count)

        except Exception as e:
            print("❌ Chyba při načítání/průchodu dat:", e)

        time.sleep(15)  # odpovídá Prometheus scrape_interval

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')

if __name__ == '__main__':
    t = threading.Thread(target=update_metrics)
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', port=8000)
