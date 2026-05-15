#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);  // Change 0x27 to your actual I2C address if different
const int buzzer_Pin = 8;
const int led_Pin = 9;
const int safe_LED_Pin = 10;  // New LED for "Safe" indication

char sleep_status = 0;
unsigned long lastReceivedTime = 0;
bool alerting = false;

void setup() {
  Serial.begin(9600);
  pinMode(buzzer_Pin, OUTPUT);
  pinMode(led_Pin, OUTPUT);
  pinMode(safe_LED_Pin, OUTPUT);  // Initialize new safe LED pin

  lcd.init();                // Initialize the LCD
  lcd.backlight();           // Turn on the backlight

  lcd.setCursor(0, 0);
  lcd.print("Driver Sleep");
  lcd.setCursor(0, 1);
  lcd.print("Detection Ready");
  
  digitalWrite(buzzer_Pin, LOW);
  digitalWrite(led_Pin, LOW);
  digitalWrite(safe_LED_Pin, LOW);
}

void loop() {
  if (Serial.available() > 0) {
    sleep_status = Serial.read();
    lastReceivedTime = millis();  // update time on data receive

    if (sleep_status == 'a') {
      alerting = true;
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Please Wake Up!");
      lcd.setCursor(0, 1);
      lcd.print("You are Drowsy");
      digitalWrite(buzzer_Pin, HIGH);
      digitalWrite(led_Pin, HIGH);
      digitalWrite(safe_LED_Pin, LOW);  // Turn off safe LED during alert
    } 
    else if (sleep_status == 'b') {
      alerting = false;
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("All OK");
      lcd.setCursor(0, 1);
      lcd.print("Drive Safe :)");
      digitalWrite(buzzer_Pin, LOW);
      digitalWrite(led_Pin, LOW);
      digitalWrite(safe_LED_Pin, HIGH);  // Turn on safe LED when status is OK
    }
  }

  // Failsafe: Stop buzzer if no data for 3 seconds
  if (alerting && millis() - lastReceivedTime > 10000) {
    alerting = false;
    digitalWrite(buzzer_Pin, LOW);
    digitalWrite(led_Pin, LOW);
    digitalWrite(safe_LED_Pin, HIGH);  // Assuming safe LED on if no active alert
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Signal Lost");
    lcd.setCursor(0, 1);
    lcd.print("Drive Carefully");
  }
}
