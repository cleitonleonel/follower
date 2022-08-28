import websocket
import json
import time

close_ws = False
result_dict = None


WSS_BASE = "wss://api-v2.blaze.com"
WSS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/87.0.4280.88 Safari/537.36"
}


def get_ws_result():
    return result_dict


def set_ws_closed(status):
    global close_ws
    close_ws = status


def get_color(number):
    colors = {
        0: "branco",
        1: "vermelho",
        2: "preto"
    }
    return colors.get(number, )


def on_message(ws, message):
    global result_dict
    global close_ws
    if "double.tick" in message:
        result_dict = json.loads(message[2:])[1]["payload"]

    if close_ws:
        ws.close()


def on_error(ws, error):
    pass


def on_close(ws, close_status_code, close_msg):
    time.sleep(1)
    connect_websocket()


def on_ping(ws, message):
    pass


def on_pong(ws, message):
    ws.send("2")


def on_open(ws):
    time.sleep(0.1)
    message = '%d["cmd", {"id": "subscribe", "payload": {"room": "double_v2"}}]' % 421
    ws.send(message)


def connect_websocket():
    ws = websocket.WebSocketApp(f"{WSS_BASE}/replication/?EIO=3&transport=websocket",
                                header=WSS_HEADERS,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close,
                                on_ping=on_ping,
                                on_pong=on_pong
                                )

    ws.run_forever(ping_interval=24, ping_timeout=5, ping_payload="2")
