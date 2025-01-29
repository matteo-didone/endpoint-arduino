# -*- coding: utf-8 -*-

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
import paho.mqtt.client as mqtt
import serial
import serial.tools.list_ports
from typing import Optional

# Configurazione FastAPI
app = FastAPI()

# Abilita CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurazione Serial
BAUD_RATE = 115200
serial_port = None

def find_arduino():
    """Cerca la porta seriale dell'Arduino"""
    ports = list(serial.tools.list_ports.comports())
    print("Porte seriali disponibili:")
    for port in ports:
        print(f"- {port.device} ({port.description})")
        if 'arduino' in port.description.lower() or 'usbmodem' in port.device.lower():
            return port.device
    return None

def setup_serial():
    """Configura la connessione seriale con l'Arduino"""
    global serial_port
    try:
        arduino_port = find_arduino()
        if arduino_port:
            print(f"Arduino trovato su: {arduino_port}")
            serial_port = serial.Serial(arduino_port, BAUD_RATE, timeout=1)
            return True
        else:
            print("Arduino non trovato")
            return False
    except Exception as e:
        print(f"Errore nella configurazione seriale: {e}")
        return False

# Configurazione MQTT
MQTT_BROKER = "broker.hivemq.com"  # Broker pubblico
MQTT_PORT = 1883
MQTT_TOPIC = "arduino/matteo/display/message"  # Topic personalizzato per evitare conflitti
MAX_MESSAGE_LENGTH = 256

# Configura il client MQTT
mqtt_client = mqtt.Client(protocol=mqtt.MQTTv5)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"Connesso al broker MQTT: {MQTT_BROKER}")
    else:
        print(f"Errore di connessione al broker MQTT. Codice: {rc}")

def on_disconnect(client, userdata, rc, properties=None):
    print(f"Disconnesso dal broker MQTT con codice: {rc}")

# Assegna i callback
mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect

# Connetti al broker MQTT
try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"Errore nella connessione MQTT: {e}")

# Setup iniziale seriale
setup_serial()

# Modello per il messaggio
class Message(BaseModel):
    message: str

    @field_validator('message')
    def validate_message_length(cls, v):
        if len(v) > MAX_MESSAGE_LENGTH:
            raise ValueError(f'Il messaggio non puo superare i {MAX_MESSAGE_LENGTH} caratteri')
        if len(v) == 0:
            raise ValueError('Il messaggio non puo essere vuoto')
        return v

# Route per la home page
@app.get("/")
async def read_root():
    return FileResponse('index.html')

# Route API
@app.post("/api/arduino-message")
async def send_message(message: Message):
    try:
        # Pubblica su MQTT
        result = mqtt_client.publish(MQTT_TOPIC, message.message)
        result.wait_for_publish()
        print(f"Pubblicazione messaggio MQTT: '{message.message}' sul topic: {MQTT_TOPIC}")
        
        # Invia sulla porta seriale
        if serial_port and serial_port.is_open:
            try:
                serial_message = message.message + '\n'
                serial_port.write(serial_message.encode())
                print(f"Messaggio inviato sulla porta seriale: {message.message}")
            except Exception as e:
                print(f"Errore nell'invio seriale: {e}")
                setup_serial()
        else:
            print("Porta seriale non disponibile")
            setup_serial()
        
        return {
            "success": True,
            "message": "Messaggio inviato con successo",
            "details": {
                "length": len(message.message),
                "topic": MQTT_TOPIC,
                "mqtt_broker": MQTT_BROKER,
                "serial_connected": bool(serial_port and serial_port.is_open)
            }
        }
    
    except Exception as e:
        print(f"Errore durante l'invio del messaggio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint per verificare lo stato
@app.get("/api/status")
async def check_status():
    return {
        "mqtt_connected": mqtt_client.is_connected(),
        "mqtt_broker": MQTT_BROKER,
        "mqtt_topic": MQTT_TOPIC,
        "serial_connected": bool(serial_port and serial_port.is_open),
        "max_message_length": MAX_MESSAGE_LENGTH
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)