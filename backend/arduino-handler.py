# arduino_handler.py
import serial
import serial.tools.list_ports
import time
import paho.mqtt.client as mqtt
from collections import deque

# Inizializzazione della coda messaggi
messages = deque()

def find_arduino_port():
    """Cerca la porta seriale dell'Arduino"""
    ports = list(serial.tools.list_ports.comports())
    for portA in ports:
        if "USB Serial Device" in portA.description or "CH340" in portA.description:
            return portA.device
    return None

# Configurazione seriale
port = find_arduino_port()
serial_baudrate = 115200
serial_timeout = 1
arduino = serial.Serial(port, serial_baudrate, timeout=serial_timeout) if port else None

def send_to_arduino(msg):
    """Invia un messaggio all'Arduino"""
    if arduino and arduino.is_open:
        arduino.write((msg + "\n").encode('utf-8'))
        print(f"Sent: {msg}")
    else:
        print("No Arduino device found or serial port not open")

def on_message(client, userdata, message):
    """Callback per i messaggi MQTT ricevuti"""
    msg = message.payload.decode("utf-8")
    print(f"Received MQTT message: {msg}")
    messages.append(msg)

def main():
    global arduino, messages
    
    # Configurazione MQTT
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5)
    client.on_message = on_message
    
    mqtt_broker = "broker.hivemq.com"
    mqtt_topic = "arduino/matteo/display/message"
    mqtt_port = 1883
    mqtt_keepalive = 60
    
    try:
        # Connessione al broker MQTT
        client.connect(mqtt_broker, mqtt_port, mqtt_keepalive)
        client.subscribe(mqtt_topic)
        client.loop_start()
        
        # Loop principale
        while True:
            if arduino and arduino.in_waiting > 0:
                response = arduino.readline().decode('utf-8').strip()
                if response == "OK" and messages:
                    send_to_arduino(messages.popleft())
            elif messages:
                send_to_arduino(messages.popleft())
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("Programma terminato dall'host")
        client.loop_stop()
    except Exception as e:
        print(f"Errore: {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()