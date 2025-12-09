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

        prev_cell = (prev[4], prev[5], prev[6], prev[7])
        curr_cell = (curr[4], curr[5], curr[6], curr[7])

        if prev_cell != curr_cell:
            mid_lat = (prev[0] + curr[0]) / 2
            mid_lng = (prev[1] + curr[1]) / 2

            handovers.append({
                "from": {
                    "mcc": prev[4],
                    "mnc": prev[5],
                    "pci": prev[6],
                    "earfcn": prev[7],
                },
                "to": {
                    "mcc": curr[4],
                    "mnc": curr[5],
                    "pci": curr[6],
                    "earfcn": curr[7],
                },
                "position": {
                    "latitude": mid_lat,
                    "longitude": mid_lng
                }
            })

    return handovers

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

        route_points = []
        for row in rows:
            lat, lon, ts, rsrp, *_ = row
            route_points.append({
                "latitude": lat,
                "longitude": lon,
                "timestamp": ts,
                "rsrp": rsrp
            })

        cell_groups = {}

        for row in rows:
            lat, lon, ts, rsrp, mcc, mnc, pci, earfcn = row
            key = (mcc, mnc, pci, earfcn)

            if key not in cell_groups:
                cell_groups[key] = []

            cell_groups[key].append((lat, lon, rsrp))

        base_stations = []

        for (mcc, mnc, pci, earfcn), pts in cell_groups.items():
            valid = [p for p in pts if p[2] is not None]
            if not valid:
                continue

            avg_lat = sum(p[0] for p in valid) / len(valid)
            avg_lon = sum(p[1] for p in valid) / len(valid)
            avg_rsrp = sum(p[2] for p in valid) / len(valid)

            base_stations.append({
                "latitude": avg_lat,
                "longitude": avg_lon,
                "mcc": mcc,
                "mnc": mnc,
                "pci": pci,
                "earfcn": earfcn,
                "point_count": len(pts),
                "avg_rsrp": avg_rsrp
            })

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
