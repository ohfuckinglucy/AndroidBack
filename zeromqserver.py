import zmq
import json
import psycopg2

def get_connection():
    return psycopg2.connect(
        dbname="telecom_data",
        user="postgres",
        password="242486",
        host="localhost",
        port="5432"
    )

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:8080")

try:
    while True:
        data = socket.recv_string()
        print("Raw data:", data)

        try:
            parsed = json.loads(data)

            # LTE формат
            if "location" in parsed and "cellInfoLte" in parsed:
                loc = parsed["location"]
                cell = parsed["cellInfoLte"][0]
                ident = cell.get("cellIdentity", {})
                sig = cell.get("signalStrength", {})

                lat = loc.get("latitude")
                lon = loc.get("longitude")
                timestamp = loc.get("timestamp")
                altitude = loc.get("altitude")
                speed = loc.get("speed")
                accuracy = loc.get("accuracy")

                cell_identity = ident.get("cellIdentity")
                pci = ident.get("pci")
                tac = ident.get("tac")
                earfcn = ident.get("earfcn")
                mcc = ident.get("mcc")
                mnc = ident.get("mnc")
                band = ident.get("band")
                rsrp = sig.get("rsrp")
                rsrq = sig.get("rsrq")
                rssnr = sig.get("rssnr")
                rssi = sig.get("rssi")
                cqi = sig.get("cqi")
                asu_level = sig.get("asuLevel")
                timing_advance = sig.get("timingAdvance")

            # GPS формат
            elif "lat" in parsed and "lon" in parsed and "time" in parsed:
                lat = parsed.get("lat")
                lon = parsed.get("lon")
                timestamp = parsed.get("time")
                altitude = None
                speed = parsed.get("speed")
                accuracy = parsed.get("acc")

                cell_identity = pci = tac = earfcn = mcc = mnc = band = None
                rsrp = rsrq = rssnr = rssi = cqi = asu_level = timing_advance = None

            else:
                print("Bad format:", parsed)
                socket.send_string("Bad format")
                continue

            values = (
                lat, lon, altitude, timestamp, speed, accuracy,
                cell_identity, pci, tac, earfcn, mcc, mnc, band,
                rsrp, rsrq, rssnr, rssi, cqi, asu_level, timing_advance
            )

            print("Inserting:", values)

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO measurements (
                            latitude, longitude, altitude, timestamp, speed, accuracy,
                            cell_identity, pci, tac, earfcn, mcc, mnc, band,
                            rsrp, rsrq, rssnr, rssi, cqi, asu_level, timing_advance
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, values)
                    conn.commit()

            socket.send_string("Принял")

        except Exception as e:
            print("Ошибка парсинга или БД:", e)
            socket.send_string("Error")

except KeyboardInterrupt:
    print("Ctrl + C")
    socket.close()
    context.term()
