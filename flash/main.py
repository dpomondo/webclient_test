import machine
from machine import Pin, I2C
import socket
import time
import ssd1306
import binascii
from umqtt.simple import MQTTClient
# import dht
import credentials
import device

# using default address 0x3C
i2c = I2C(sda=Pin(4), scl=Pin(5))
display = ssd1306.SSD1306_I2C(device.DISPL_WIDTH, device.DISPL_HEIGHT, i2c)
text_width = int(device.DISPL_WIDTH / 6)
# d = dht.DHT11(Pin(4))
LED_builtin = Pin(2, Pin.OUT)
CLIENT_ID = binascii.hexlify(machine.unique_id())
TOPIC = b"test/webserver"

def do_connect():
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        message = 'connecting to network...'
        print(message)
        message_new = message.split(' ')
        for index in range(len(message_new)):
            display.text(message_new[index], 0, (10 * index), 1)
        display.show()

        wlan.connect(credentials.WIFI_SSID, credentials.WIFI_PASSWORD)
        while not wlan.isconnected():
            LED_builtin.value(~LED_builtin.value())
    # message = f"network config: {wlan.ifconfig('addr4')}"
    message = f"ip: {wlan.ifconfig()[0]} connect: {wlan.isconnected()}"
    print(message)
    message_new = message.split(' ')
    display.fill(0)
    for index in range(len(message_new)):
        display.text(message_new[index], 0, (10 * index), 1)
    display.show()


def http_get(url, port):
    _, _, host, path = url.split('/', 3)
    # addr = socket.getaddrinfo(host, 5000)[0][-1]
    addr = socket.getaddrinfo(host, port)[0][-1]
    s = socket.socket()
    s.connect(addr)
    s.send(bytes('GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))
    while True:
        data = s.recv(100)
        if data:
            print(str(data, 'utf8'), end='')
        else:
            break
    s.close()


loops = 0


def mqtt_loop(server=credentials.PI_IP_PORT, port=1883):
    global loops
    c = MQTTClient(CLIENT_ID, "192.168.10.67")
    c.connect()
    print("Connected to %s, waiting for button presses" % server)
    while True:
        for loops in range(1000):
            print(f"Sending {loops}")
            display.fill(0)
            display.text(f"{loops}-->", 3, 3, 1)
            display.text(f"   {TOPIC}", 3, 13, 1)
            display.show()
            c.publish(TOPIC, f"{loops}")
            time.sleep_ms(1000 * 8)

    c.disconnect()


def connect_to_pi(data):
    # pi_addr = "192.168.0.24"
    # pi_port = 80
    # addr = socket.getaddrinfo(pi_addr, 5000)[0][-1]
    addr = socket.getaddrinfo(
        credentials.PI_IP_ADDRESS, credentials.PI_IP_PORT)[0][-1]
    sock = socket.socket()
    try:
        sock.connect(addr)
    except OSError as ERROR:
        print(
            "failed to connect to socket: bad port maybe" +
            f"{credentials.PI_IP_PORT}\n{ERROR}")
        return
    sock.send(bytes(
        f"GET /query-data?data={data} HTTP/1.0\r\nHost: " +
        f"{credentials.PI_IP_ADDRESS}\r\n\r\n",
        'utf-8'))
    display.fill(0)
    display.text(f"{data}", 0, 0, 1)
    while True:
        received = sock.recv(500)
        if received:
            received = str(received, 'utf8')
            print(received,  end='')
            if device.DISPL_WIDTH <= 64:
                received.replace('\r', ' ').replace('\n', ' ')
                message_new = received.split(' ')
            else:
                message_new = received.split('\n')
                message_new = received.split('\r')
            # I have no idea why this works, but it does
            # without the `- 1` in the range the data overwrites the first
            # characters of the first line. ALso, bare lengths in the
            # range(..) cause index out of range errors

            # for index in range(len(message_new) - 1):
            for index in range(min(3, len(message_new)) - 1):
                displ_temp = f"{message_new[index]}"
                print(displ_temp)
                display.text(displ_temp, 0, 11 + (10 * index), 1)
            # display.text(f"{message_new[0][:8]}", 0, 10, 1)
            # display.show()
        else:
            break
    display.show()
    sock.close()


def get_dht_results():
    pass


def run_the_stuff():
    do_connect()
    mqtt_loop()
    # http_get('http://micropython.org/ks/test.html')
    # d.measure()
    # print(f"temp: {d.temperature()}\thumidity: {d.humidity()}")
    while False:
        for i in range(1000):
            connect_to_pi(i)
            time.sleep(10)


if __name__ == "__main__":
    run_the_stuff()
