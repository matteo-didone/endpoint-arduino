#include <LiquidCrystal.h>

// Inizializza la libreria con i pin collegati
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

// Variabili per la gestione dei messaggi
String messaggioPrecedente = "";
String messaggioScroll = "";
int posizioneScroll = 0;
unsigned long ultimoAggiornamentoScroll = 0;
const int VELOCITA_SCROLL = 500;  // Velocità di scorrimento in millisecondi

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
    String contenuto = messaggio.substring(pos + 1);
    // Rimuovi spazi all'inizio e alla fine manualmente
    while (contenuto.length() > 0 && contenuto.charAt(0) == ' ') {
      contenuto = contenuto.substring(1);
    }
    while (contenuto.length() > 0 && contenuto.charAt(contenuto.length() - 1) == ' ') {
      contenuto = contenuto.substring(0, contenuto.length() - 1);
    }
    return contenuto;
  }
  return messaggio;
}

void visualizzaMessaggio(String nickname, String contenuto) {
  // Visualizza il nickname sulla prima riga (solo se è cambiato)
  static String lastNickname = "";
  if (nickname != lastNickname) {
    lcd.setCursor(0, 0);
    if (nickname.length() <= 16) {
      lcd.print(nickname);
      // Pulisci eventuali caratteri rimanenti
      for (int i = nickname.length(); i < 16; i++) {
        lcd.print(" ");
      }
    } else {
      lcd.print(nickname.substring(0, 13) + "...");
    }
    lastNickname = nickname;
  }

  // Gestione contenuto con scroll
  if (contenuto.length() <= 16) {
    // Contenuto corto, visualizza normalmente
    lcd.setCursor(0, 1);
    lcd.print(contenuto);
    // Pulisci eventuali caratteri rimanenti
    for (int i = contenuto.length(); i < 16; i++) {
      lcd.print(" ");
    }
    messaggioScroll = "";  // Reset scroll
  } else {
    // Contenuto lungo, gestisci lo scroll
    if (messaggioScroll != contenuto) {
      // Nuovo messaggio da far scorrere
      messaggioScroll = contenuto;
      posizioneScroll = 0;
      ultimoAggiornamentoScroll = millis();
      // Visualizza i primi 16 caratteri
      lcd.setCursor(0, 1);
      lcd.print(contenuto.substring(0, 16));
    } else {
      // Aggiorna lo scroll solo se è passato abbastanza tempo
      if (millis() - ultimoAggiornamentoScroll >= VELOCITA_SCROLL) {
        ultimoAggiornamentoScroll = millis();
        
        // Calcola la stringa da visualizzare
        String testoVisibile;
        if (posizioneScroll + 16 <= contenuto.length()) {
          testoVisibile = contenuto.substring(posizioneScroll, posizioneScroll + 16);
        } else {
          // Gestisci il wrap-around aggiungendo spazi e l'inizio del messaggio
          String temp = contenuto.substring(posizioneScroll) + "    " + contenuto;
          testoVisibile = temp.substring(0, 16);
        }
        
        lcd.setCursor(0, 1);
        lcd.print(testoVisibile);
        
        // Incrementa la posizione e gestisci il wrap-around
        posizioneScroll++;
        if (posizioneScroll > contenuto.length() + 4) {  // +4 per gli spazi extra
          posizioneScroll = 0;
        }
      }
    }
  }
}

void loop() {
  // Controlla se ci sono dati disponibili sulla seriale
  if (Serial.available() > 0) {
    String messaggio = Serial.readStringUntil('\n');
    
    // Se il messaggio è diverso dal precedente
    if (messaggio != messaggioPrecedente) {
      messaggioPrecedente = messaggio;
      // Resetta le variabili di scroll
      messaggioScroll = "";
      posizioneScroll = 0;
      
      // Estrai e visualizza il messaggio
      String nickname = getNickname(messaggio);
      String contenuto = getContenuto(messaggio);
      visualizzaMessaggio(nickname, contenuto);
    }
    Serial.print("OK");
  }
  
  // Aggiorna lo scroll se necessario
  if (messaggioPrecedente.length() > 0) {
    String nickname = getNickname(messaggioPrecedente);
    String contenuto = getContenuto(messaggioPrecedente);
    visualizzaMessaggio(nickname, contenuto);
  }
}