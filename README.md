# Sistema di Messaggistica Arduino con Display LCD

## 📑 Indice
- [Sistema di Messaggistica Arduino con Display LCD](#sistema-di-messaggistica-arduino-con-display-lcd)
  - [📑 Indice](#-indice)
  - [🔧 Componenti del Sistema](#-componenti-del-sistema)
    - [1. Frontend Web (HTML/JavaScript)](#1-frontend-web-htmljavascript)
    - [2. Backend (Python)](#2-backend-python)
    - [3. Arduino Handler (Python)](#3-arduino-handler-python)
    - [4. Sketch Arduino](#4-sketch-arduino)
  - [🚀 Come funziona](#-come-funziona)
  - [📦 Dipendenze](#-dipendenze)
  - [🔌 Setup](#-setup)
  - [🔍 Debugging](#-debugging)
  - [📝 Note tecniche](#-note-tecniche)

Questo progetto implementa un sistema di messaggistica che permette agli utenti di inviare messaggi attraverso un'interfaccia web, visualizzandoli su un display LCD collegato ad Arduino. Il sistema è composto da quattro componenti principali: frontend web, backend FastAPI, Arduino handler e sketch Arduino.

## 🔧 Componenti del Sistema

### 1. Frontend Web (HTML/JavaScript)
L'interfaccia utente web offre le seguenti funzionalità:
- Gestione del nickname dell'utente
- Invio di messaggi (max 100 caratteri)
- Visualizzazione della cronologia messaggi
- Cancellazione della cronologia

**Caratteristiche principali:**
- Design moderno con effetto "glass morphism"
- Feedback in tempo reale per le azioni dell'utente
- Aggiornamento automatico della cronologia messaggi ogni 2 secondi
- Validazione dell'input utente
- Contatore di caratteri per i messaggi

### 2. Backend (Python)
Il server API (`api_server.py`) gestisce:
- API REST per la gestione dei messaggi
- Pubblicazione dei messaggi su broker MQTT
- Gestione della cronologia messaggi

**Endpoint API:**
- `GET /`: Serve l'interfaccia web
- `POST /api/arduino-message`: Riceve e processa nuovi messaggi
- `GET /api/messages`: Recupera la cronologia messaggi
- `DELETE /api/messages`: Cancella la cronologia
- `GET /api/status`: Fornisce lo stato del sistema

### 3. Arduino Handler (Python)
Il gestore Arduino (`arduino_handler.py`) si occupa di:
- Comunicazione seriale con Arduino
- Sottoscrizione ai messaggi MQTT
- Gestione della coda messaggi
- Invio dei messaggi al display LCD

### 4. Sketch Arduino
Gestisce il display LCD 16x2 e implementa la logica di visualizzazione dei messaggi.

**Funzionalità principali:**
- Parsing dei messaggi in nickname e contenuto
- Gestione automatica dello scroll per messaggi lunghi
- Troncamento automatico dei nickname lunghi
- Buffer per evitare duplicati di messaggi

**Pin utilizzati:**
- LCD RS pin -> 12
- LCD Enable pin -> 11
- LCD D4 pin -> 5
- LCD D5 pin -> 4
- LCD D6 pin -> 3
- LCD D7 pin -> 2

## 🚀 Come funziona

1. **Flusso dei messaggi:**
   - L'utente inserisce il nickname e lo salva
   - Scrive un messaggio e lo invia
   - Il backend (`api_server.py`) riceve il messaggio e:
     - Lo formatta (`nickname: messaggio`)
     - Lo pubblica su MQTT
     - Lo salva nella cronologia
   - L'Arduino handler (`arduino_handler.py`):
     - Riceve il messaggio da MQTT
     - Lo inserisce nella coda
     - Lo invia ad Arduino via seriale
   - Arduino riceve il messaggio e:
     - Lo visualizza sul display LCD

2. **Gestione del display:**
   - Nickname > 16 caratteri: troncato con "..."
   - Contenuto > 16 caratteri: scorre automaticamente
   - Velocità scroll: 500ms per carattere
   - Buffer anti-duplicati per evitare flickering

3. **Sicurezza e validazione:**
   - Validazione lato client e server
   - Sanitizzazione degli input
   - Protezione contro messaggi vuoti
   - Limiti di lunghezza per nickname e messaggi

## 📦 Dipendenze

**Python:**
```
fastapi>=0.109.0
uvicorn>=0.27.0
paho-mqtt>=1.6.1
pydantic>=2.5.0
python-multipart>=0.0.6
aiofiles>=23.2.1
pyserial>=3.5
```

**Arduino:**
```cpp
#include <LiquidCrystal.h>
```

## 🔌 Setup

1. **Arduino:**
   - Collegare il display LCD secondo lo schema dei pin
   - Caricare lo sketch Arduino
   - Verificare la porta seriale

2. **Backend:**
   - Installare le dipendenze Python: `pip install -r requirements.txt`
   - Avviare l'API server: `python api_server.py`
   - In un altro terminale, avviare l'Arduino handler: `python arduino_handler.py`

3. **Frontend:**
   - Verrà servito automaticamente dal backend
   - Accessibile su `http://localhost:8000`

## 🔍 Debugging
- Monitor seriale Arduino: 115200 baud
- Log backend: visualizza stato MQTT
- Log Arduino handler: visualizza stato seriale
- Status API: `/api/status` per diagnostica
- Messaggi di errore UI: feedback visivo per l'utente

## 📝 Note tecniche
- Sistema diviso in componenti indipendenti
- Comunicazione asincrona tramite MQTT
- Gestione separata di web API e comunicazione Arduino
- Frontend implementa polling per aggiornamenti
- CORS abilitato per sviluppo cross-origin