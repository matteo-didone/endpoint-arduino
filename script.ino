#include <LiquidCrystal.h>

// Inizializza la libreria con i pin collegati
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

String messaggioPrecedente = "";

void setup() {
  // Imposta il numero di colonne e righe del display
  lcd.begin(16, 2);
  
  // Avvia la comunicazione seriale a 115200 baud
  Serial.begin(115200);
  
  // Stampa un messaggio iniziale sul display
  lcd.print("In attesa...");
}

void loop() {
  // Controlla se ci sono dati disponibili sulla seriale
  if (Serial.available() > 0) {
    // Leggi la stringa inviata tramite seriale
    String messaggio = Serial.readStringUntil('\n');
    
    // Se il messaggio è diverso dal precedente, pulisci il display
    if (messaggio != messaggioPrecedente) {
      lcd.clear();
      messaggioPrecedente = messaggio;
    }
    
    // Se il messaggio è più corto o uguale a 16 caratteri, lo stampa direttamente
    if (messaggio.length() <= 16) {
      lcd.print(messaggio);
    } else {
      // Scorrimento del testo se più lungo di 16 caratteri
      for (int i = 0; i <= messaggio.length() - 16; i++) {
        lcd.setCursor(0, 0);
        lcd.print(messaggio.substring(i, i + 16));
        delay(200); // Regola la velocità dello scorrimento (più veloce)
      }
    }
    Serial.print("OK");
  }
}