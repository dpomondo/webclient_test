import machine
from machine import Pin, I2C, RTC
import socket
import time
import ssd1306
import binascii
from umqtt.robust import MQTTClient
import ntptime
# import dht
import credentials
import device

# using default address 0x3C
i2c = I2C(sda=Pin(4), scl=Pin(5))
display = ssd1306.SSD1306_I2C(device.DISPL_WIDTH, device.DISPL_HEIGHT, i2c)
display.rotate(True)
text_width = int(device.DISPL_WIDTH / 6)
# d = dht.DHT11(Pin(4))
LED_builtin = Pin(2, Pin.OUT)
CLIENT_ID = binascii.hexlify(machine.unique_id())
TOPIC = b"test/webserver"
# SUB_TOPIC = b"test/littleguy"
SUB_TOPIC = b"test/littleguy"

rtc = RTC()

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
    message = [f"ip: {wlan.ifconfig()[0]}", f"connect: {wlan.isconnected()}"]
    print(message[0] + " " + message[1])
    display.fill(0)
    for index in range(len(message)):
        display.text(message[index], 0, (10 * index), 1)
    display.rotate(True)
    display.show()


def subscribe_callback(topic, message):
    output = f"{message.decode()}<--recv"
    print(output)
    display.fill_rect(0, 23, 128, 33, 0)
    display.text(output, 3, 23, 1)
    display.show()


def mqtt_loop(server=credentials.PI_IP_ADDRESS, port=1883):
    # c = MQTTClient(CLIENT_ID, "192.168.10.67")
    c = MQTTClient(CLIENT_ID, server)
    c.connect()
    c.set_callback(subscribe_callback)
    c.subscribe(SUB_TOPIC)
    print(f"connected to {server}, subscribed to {SUB_TOPIC.decode()}")
    try:
        while True:
            for loops in range(1000):
                # (year, month, day, weekday, hours, minutes, seconds, subseconds)                
                n = rtc.datetime()
                now_iso = f"{n[0]}-{n[1]:02}-{n[2]:02}" + \
                    f" {n[4]:02}:{n[5]:02}:{n[6]:02}"
                send = str({"timestamp": {"time:": now_iso, "tz": "UTC"},
                            "device": device.DEVICE_NAME,
                           "temp": {"result": loops, "sensor": "aht20"}})
                print(f"Sending {loops}")
                display.fill(0)
                display.text(f"{loops}", 3, 3, 1)
                display.text(f"{now_iso} UTC", 3, 13, 1)
                display.rotate(True)
                display.show()
                c.publish(TOPIC, send.encode())
                for i in range(8):
                    c.check_msg()
                    time.sleep_ms(1000)
    finally:
        c.disconnect()


def get_dht_results():
    pass


def run_the_stuff():
    do_connect()
    print("Setting time...")
    ntptime.settime()
    print(f"time is {rtc.datetime()} UTC")

    mqtt_loop()


if __name__ == "__main__":
    run_the_stuff()
