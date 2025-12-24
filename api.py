from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2

app = Flask(__name__)
CORS(app)

def get_connection():
    return psycopg2.connect(
        dbname="telecom_data",
        user="postgres",
        password="242486",
        host="localhost",
        port="5432"
    )

def detect_handovers(points):
    handovers = []

    for i in range(1, len(points)):
        prev = points[i - 1]
        curr = points[i]

        prev_pci = prev[6] 
        curr_pci = curr[6]

        if prev_pci != curr_pci:
            mid_lat = (prev[0] + curr[0]) / 2
            mid_lng = (prev[1] + curr[1]) / 2

            handovers.append({
                "from": {"pci": prev_pci},
                "to": {"pci": curr_pci},
                "position": {"latitude": mid_lat, "longitude": mid_lng}
            })

    return handovers

def build_route_points(rows):
    return [
        {"latitude": lat, "longitude": lon, "timestamp": ts, "rsrp": rsrp}
        for lat, lon, ts, rsrp, *_ in rows
    ]

def build_base_stations(rows):
    base_stations = []
    seen_pci = set()
    for row in rows:
        lat, lon, ts, rsrp, mcc, mnc, pci, earfcn = row
        if pci in seen_pci:
            continue
        seen_pci.add(pci)
        base_stations.append({
            "latitude": lat,
            "longitude": lon,
            "pci": pci,
            "rsrp": rsrp
        })
    return base_stations

@app.route("/api/route", methods=["GET"])
def route():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT latitude, longitude, timestamp, rsrp,
                           mcc, mnc, pci, earfcn
                    FROM measurements
                    WHERE latitude IS NOT NULL
                      AND longitude IS NOT NULL
                    ORDER BY timestamp ASC
                """)
                rows = cur.fetchall()

        if not rows:
            return jsonify({
                "route": [],
                "base_stations": [],
                "handovers": []
            })

        route_points = build_route_points(rows)
        base_stations = build_base_stations(rows)
        handovers = detect_handovers(rows)

        return jsonify({
            "route": route_points,
            "base_stations": base_stations,
            "handovers": handovers
        })

    except Exception as e:
        print("API error:", e)
        return jsonify({
            "route": [],
            "base_stations": [],
            "handovers": []
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
