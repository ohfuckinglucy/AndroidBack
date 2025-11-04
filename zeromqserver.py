import zmq, json, psycopg2

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
            parsed_data = json.loads(data)
            print("Parsed data:", parsed_data)
            loc = parsed_data.get("location", {})
            cell = parsed_data.get("cellInfoLte", [{}])[0]
            ident = cell.get("cellIdentity", {})
            sig = cell.get("signalStrength", {})

            values = (
                loc.get("latitude"),
                loc.get("longitude"),
                loc.get("altitude"),
                loc.get("timestamp"),
                loc.get("speed"),
                loc.get("accuracy"),
                ident.get("cellIdentity"),
                ident.get("pci"),
                ident.get("tac"),
                ident.get("earfcn"),
                ident.get("mcc"),
                ident.get("mnc"),
                ident.get("band"),
                sig.get("rsrp"),
                sig.get("rsrq"),
                sig.get("rssnr"),
                sig.get("rssi"),
                sig.get("cqi"),
                sig.get("asuLevel"),
                sig.get("timing_advance")
            )

            print("Values to insert:", values)

            with get_connection() as connect:
                with connect.cursor() as cur:
                    cur.execute("""
                        INSERT INTO measurements (
                            latitude, longitude, altitude, timestamp, speed, accuracy, cell_identity,
                            pci, tac, earfcn, mcc, mnc, band, rsrp, rsrq, rssnr, rssi, cqi, asu_level, timing_advance
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", values)
                    connect.commit()

        except Exception as e:
            print("Ошибка парса:", e)

        socket.send_string("Принял")

except KeyboardInterrupt:
    print("Ctrl + c")
    socket.close()
    context.term()