#include <LiquidCrystal.h>

// Inizializza la libreria con i pin collegati
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

String messaggioPrecedente = "";
unsigned long tempoUltimoScroll = 0;
const int VELOCITA_SCROLL = 300;  // Velocità di scorrimento in millisecondi

void setup() {
  // Imposta il numero di colonne e righe del display
  lcd.begin(16, 2);
  // Avvia la comunicazione seriale a 115200 baud
  Serial.begin(115200);
  // Stampa un messaggio iniziale sul display
  lcd.print("In attesa...");
}

// Funzione per estrarre il nickname dal messaggio
String getNickname(String messaggio) {
  int pos = messaggio.indexOf(':');
  if (pos > 0) {
    return messaggio.substring(0, pos);
  }
  return "";
}

// Funzione per estrarre il contenuto del messaggio
String getContenuto(String messaggio) {
  int pos = messaggio.indexOf(':');
  if (pos > 0) {
    return messaggio.substring(pos + 1).trim();
  }
  return messaggio;
}

void visualizzaMessaggio(String nickname, String contenuto) {
  lcd.clear();
  
  // Visualizza il nickname sulla prima riga
  if (nickname.length() <= 16) {
    lcd.setCursor(0, 0);
    lcd.print(nickname);
  } else {
    lcd.setCursor(0, 0);
    lcd.print(nickname.substring(0, 13) + "...");
  }

  // Visualizza il contenuto sulla seconda riga
  if (contenuto.length() <= 16) {
    lcd.setCursor(0, 1);
    lcd.print(contenuto);
  } else {
    // Se il contenuto è più lungo di 16 caratteri, lo fa scorrere
    int startPos = (millis() - tempoUltimoScroll) / VELOCITA_SCROLL;
    startPos = startPos % (contenuto.length() + 4);  // Aggiungi spazio alla fine
    
    String testoScroll = contenuto + "    " + contenuto.substring(0, 16);
    lcd.setCursor(0, 1);
    
    if (startPos < testoScroll.length() - 16) {
      lcd.print(testoScroll.substring(startPos, startPos + 16));
    }
  }
}

void loop() {
  // Controlla se ci sono dati disponibili sulla seriale
  if (Serial.available() > 0) {
    // Leggi la stringa inviata tramite seriale
    String messaggio = Serial.readStringUntil('\n');
    
    // Se il messaggio è diverso dal precedente
    if (messaggio != messaggioPrecedente) {
      messaggioPrecedente = messaggio;
      tempoUltimoScroll = millis();  // Resetta il timer dello scroll
      
      // Estrai nickname e contenuto
      String nickname = getNickname(messaggio);
      String contenuto = getContenuto(messaggio);
      
      // Visualizza il messaggio
      visualizzaMessaggio(nickname, contenuto);
    }
    
    Serial.print("OK");
  }
  
  // Se il messaggio corrente è più lungo di 16 caratteri, aggiorna lo scroll
  if (messaggioPrecedente.length() > 0) {
    String contenuto = getContenuto(messaggioPrecedente);
    if (contenuto.length() > 16) {
      visualizzaMessaggio(getNickname(messaggioPrecedente), contenuto);
    }
  }
}