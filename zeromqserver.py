import zmq
import json

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:8080")

print("Сервер запущен на порту 8080")

try:
    while True:
        msg = socket.recv_string()
        print(f"Получено: {msg}")

        try:
            data = json.loads(msg)
            lat = data.get("latitude")
            lon = data.get("longitude")
            print(f"Координаты: {lat}, {lon}")
            response = "Координаты успешно получены"
        except Exception as e:
            response = f"Ошибка парсинга JSON: {str(e)}"

        socket.send_string(response)

except KeyboardInterrupt:
    print("Остановка сервера...")

finally:
    socket.close()
    context.term()