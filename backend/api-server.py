# api_server.py
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
import paho.mqtt.client as mqtt

# Configurazione costanti
MAX_NICKNAME_LENGTH = 20
MAX_MESSAGE_LENGTH = 200
MAX_HISTORY_SIZE = 100

# Store in memoria per i messaggi
message_history = []

# Configurazione MQTT per invio messaggi
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "arduino/matteo/display/message"

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
    display_text: str

def format_display_message(nickname: str, message: str) -> str:
    """Formatta il messaggio per il display LCD."""
    nickname = nickname.strip()
    message = message.strip()
    return f"{nickname}: {message}"

def add_to_history(message: Message, display_text: str):
    """Aggiunge un messaggio alla cronologia"""
    stored_message = StoredMessage(
        message=message.message,
        nickname=message.nickname,
        timestamp=datetime.now(),
        display_text=display_text
    )
    message_history.append(stored_message)
    
    if len(message_history) > MAX_HISTORY_SIZE:
        message_history.pop(0)

# Inizializzazione client MQTT
mqtt_client = mqtt.Client(protocol=mqtt.MQTTv5)
try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"Errore nella connessione MQTT: {e}")

@app.get("/")
async def read_root():
    return FileResponse('index.html')

@app.post("/api/arduino-message")
async def send_message(message: Message):
    try:
        display_text = format_display_message(message.nickname, message.message)
        
        # Pubblica su MQTT
        result = mqtt_client.publish(MQTT_TOPIC, display_text)
        result.wait_for_publish()
        print(f"Pubblicazione messaggio MQTT: '{display_text}' sul topic: {MQTT_TOPIC}")
        
        # Aggiungi alla cronologia
        add_to_history(message, display_text)
        
        return {
            "success": True,
            "message": "Messaggio inviato con successo",
            "details": {
                "display_text": display_text,
                "length": len(display_text),
                "topic": MQTT_TOPIC,
                "mqtt_broker": MQTT_BROKER
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
        "max_message_length": MAX_MESSAGE_LENGTH,
        "max_nickname_length": MAX_NICKNAME_LENGTH,
        "message_count": len(message_history)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)