# -*- coding: utf-8 -*-

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
import paho.mqtt.client as mqtt
import serial
import serial.tools.list_ports
from typing import Optional, List
from datetime import datetime

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
MAX_NICKNAME_LENGTH = 20
MAX_MESSAGE_LENGTH = 200  # Aumentato per gestire il messaggio completo

# Store in memoria per i messaggi
message_history = []
MAX_HISTORY_SIZE = 100

class Message(BaseModel):
    message: str
    nickname: str

    @field_validator('message')
    def validate_message(cls, v):
        if not v:
            raise ValueError('Il messaggio non può essere vuoto')
        if len(v) > MAX_MESSAGE_LENGTH:
            raise ValueError(f'Il messaggio non può superare i {MAX_MESSAGE_LENGTH} caratteri')
        return v.strip()

    @field_validator('nickname')
    def validate_nickname(cls, v):
        if not v:
            raise ValueError('Il nickname non può essere vuoto')
        if len(v) > MAX_NICKNAME_LENGTH:
            raise ValueError(f'Il nickname non può superare i {MAX_NICKNAME_LENGTH} caratteri')
        return v.strip()

class StoredMessage(BaseModel):
    message: str
    nickname: str
    timestamp: datetime
    display_text: str  # Testo effettivamente mostrato sul display

def format_display_message(nickname: str, message: str) -> str:
    """
    Formatta il messaggio per il display LCD.
    Il formato è 'nickname: messaggio' ma assicura che sia ottimizzato per il display
    """
    # Rimuovi spazi extra e caratteri non necessari
    nickname = nickname.strip()
    message = message.strip()
    
    # Formatta il messaggio
    display_text = f"{nickname}: {message}"
    
    return display_text

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
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "arduino/matteo/display/message"

mqtt_client = mqtt.Client(protocol=mqtt.MQTTv5)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"Connesso al broker MQTT: {MQTT_BROKER}")
    else:
        print(f"Errore di connessione al broker MQTT. Codice: {rc}")

def on_disconnect(client, userdata, rc, properties=None):
    print(f"Disconnesso dal broker MQTT con codice: {rc}")

mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect

try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"Errore nella connessione MQTT: {e}")

setup_serial()

def add_to_history(message: Message, display_text: str):
    """Aggiunge un messaggio alla cronologia"""
    stored_message = StoredMessage(
        message=message.message,
        nickname=message.nickname,
        timestamp=datetime.now(),
        display_text=display_text
    )
    message_history.append(stored_message)
    
    # Mantieni solo gli ultimi MAX_HISTORY_SIZE messaggi
    if len(message_history) > MAX_HISTORY_SIZE:
        message_history.pop(0)

@app.get("/")
async def read_root():
    return FileResponse('index.html')

@app.post("/api/arduino-message")
async def send_message(message: Message):
    try:
        # Formatta il messaggio per il display
        display_text = format_display_message(message.nickname, message.message)
        
        # Pubblica su MQTT
        result = mqtt_client.publish(MQTT_TOPIC, display_text)
        result.wait_for_publish()
        print(f"Pubblicazione messaggio MQTT: '{display_text}' sul topic: {MQTT_TOPIC}")
        
        # Invia sulla porta seriale
        if serial_port and serial_port.is_open:
            try:
                serial_message = display_text + '\n'
                serial_port.write(serial_message.encode())
                print(f"Messaggio inviato sulla porta seriale: {display_text}")
            except Exception as e:
                print(f"Errore nell'invio seriale: {e}")
                setup_serial()
        else:
            print("Porta seriale non disponibile")
            setup_serial()
        
        # Aggiungi alla cronologia
        add_to_history(message, display_text)
        
        return {
            "success": True,
            "message": "Messaggio inviato con successo",
            "details": {
                "display_text": display_text,
                "length": len(display_text),
                "topic": MQTT_TOPIC,
                "mqtt_broker": MQTT_BROKER,
                "serial_connected": bool(serial_port and serial_port.is_open)
            }
        }
    
    except Exception as e:
        print(f"Errore durante l'invio del messaggio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/messages", response_model=List[StoredMessage])
async def get_messages():
    """Recupera la cronologia dei messaggi"""
    return message_history

@app.delete("/api/messages")
async def clear_messages():
    """Cancella la cronologia dei messaggi"""
    global message_history
    message_history = []
    return {"success": True, "message": "Cronologia messaggi cancellata"}

@app.get("/api/status")
async def check_status():
    return {
        "mqtt_connected": mqtt_client.is_connected(),
        "mqtt_broker": MQTT_BROKER,
        "mqtt_topic": MQTT_TOPIC,
        "serial_connected": bool(serial_port and serial_port.is_open),
        "max_message_length": MAX_MESSAGE_LENGTH,
        "max_nickname_length": MAX_NICKNAME_LENGTH,
        "message_count": len(message_history)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)