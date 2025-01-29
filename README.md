# Sistema di Messaggistica Arduino con Display LCD

## 📑 Indice
- [Sistema di Messaggistica Arduino con Display LCD](#sistema-di-messaggistica-arduino-con-display-lcd)
  - [📑 Indice](#-indice)
  - [🔧 Componenti del Sistema](#-componenti-del-sistema)
    - [1. Frontend Web (HTML/JavaScript)](#1-frontend-web-htmljavascript)
      - [Caratteristiche principali:](#caratteristiche-principali)
    - [2. Backend FastAPI (Python)](#2-backend-fastapi-python)
      - [Endpoint API:](#endpoint-api)
      - [Configurazioni:](#configurazioni)
    - [3. Sketch Arduino](#3-sketch-arduino)
      - [Funzionalità principali:](#funzionalità-principali)
      - [Pin utilizzati:](#pin-utilizzati)
  - [🚀 Come funziona](#-come-funziona)
  - [📦 Dipendenze](#-dipendenze)
    - [Backend Python:](#backend-python)
    - [Arduino:](#arduino)
  - [🔌 Setup](#-setup)
  - [🔍 Debugging](#-debugging)
  - [📝 Note tecniche](#-note-tecniche)

Questo progetto implementa un sistema di messaggistica che permette agli utenti di inviare messaggi attraverso un'interfaccia web, visualizzandoli su un display LCD collegato ad Arduino. Il sistema è composto da tre componenti principali: frontend web, backend FastAPI e sketch Arduino.

## 🔧 Componenti del Sistema

### 1. Frontend Web (HTML/JavaScript)
L'interfaccia utente web offre le seguenti funzionalità:
- Gestione del nickname dell'utente
- Invio di messaggi (max 100 caratteri)
- Visualizzazione della cronologia messaggi
- Cancellazione della cronologia

#### Caratteristiche principali:
- Design moderno con effetto "glass morphism"
- Feedback in tempo reale per le azioni dell'utente
- Aggiornamento automatico della cronologia messaggi ogni 2 secondi
- Validazione dell'input utente
- Contatore di caratteri per i messaggi

### 2. Backend FastAPI (Python)
Il server gestisce la logica di business e la comunicazione con Arduino attraverso:
- API REST per la gestione dei messaggi
- Comunicazione seriale con Arduino
- Pubblicazione dei messaggi su broker MQTT

#### Endpoint API:
- `GET /`: Serve l'interfaccia web
- `POST /api/arduino-message`: Riceve e processa nuovi messaggi
- `GET /api/messages`: Recupera la cronologia messaggi
- `DELETE /api/messages`: Cancella la cronologia
- `GET /api/status`: Fornisce lo stato del sistema

#### Configurazioni:
- Limite messaggi: 200 caratteri
- Limite nickname: 20 caratteri
- Cronologia: max 100 messaggi
- Baud rate seriale: 115200
- MQTT broker: broker.hivemq.com
- MQTT topic: arduino/matteo/display/message

### 3. Sketch Arduino
Gestisce il display LCD 16x2 e implementa la logica di visualizzazione dei messaggi.

#### Funzionalità principali:
- Parsing dei messaggi in nickname e contenuto
- Gestione automatica dello scroll per messaggi lunghi
- Troncamento automatico dei nickname lunghi
- Buffer per evitare duplicati di messaggi

#### Pin utilizzati:
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
   - Il backend riceve il messaggio e:
     - Lo formatta (`nickname: messaggio`)
     - Lo pubblica su MQTT
     - Lo invia ad Arduino via seriale
     - Lo salva nella cronologia
   - Arduino riceve il messaggio e:
     - Estrae nickname e contenuto
     - Visualizza il nickname sulla prima riga
     - Visualizza il contenuto sulla seconda riga (con scroll se necessario)

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

### Backend Python:
```
fastapi>=0.109.0
uvicorn>=0.27.0
paho-mqtt>=1.6.1
pydantic>=2.5.0
python-multipart>=0.0.6
aiofiles>=23.2.1
```

### Arduino:
```cpp
#include <LiquidCrystal.h>
```

## 🔌 Setup

1. **Arduino:**
   - Collegare il display LCD secondo lo schema dei pin
   - Caricare lo sketch Arduino
   - Verificare la porta seriale

2. **Backend:**
   - Installare le dipendenze Python
   - Configurare la porta seriale corretta
   - Avviare il server: `uvicorn main:app --host 0.0.0.0 --port 8000`

3. **Frontend:**
   - Verrà servito automaticamente dal backend
   - Accessibile su `http://localhost:8000`

## 🔍 Debugging

- Monitor seriale Arduino: 115200 baud
- Log backend: visualizza stato MQTT e seriale
- Status API: `/api/status` per diagnostica
- Messaggi di errore UI: feedback visivo per l'utente

## 📝 Note tecniche

- Lo scroll dei messaggi è implementato con un timer millis()
- Il sistema usa un approccio event-driven
- La comunicazione è asincrona su tutti i livelli
- Il frontend implementa polling per aggiornamenti
- CORS abilitato per sviluppo cross-origin