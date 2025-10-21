
const uint8_t LED_PIN = D3;
const unsigned long ON_TIME = 2000;
const unsigned long OFF_TIME = 2000;
const unsigned long MAX_DELAY_MS = 5000;
const float AO_MAX = 3.30;
const uint16_t ADC_MAX = 1023;

void setup() {
  // put your setup code here, to run once:
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  Serial.begin(115200);
  while (!Serial){

  }
  Serial.println("Task 2");

}

void loop() {
  
  uint16_t raw = analogRead(A0);
  float volts = (raw * AO_MAX) / ADC_MAX;

  unsigned long time = (unsigned long)((raw * (float)MAX_DELAY_MS)/ADC_MAX);

  Serial.print("A0 raw: ");
  Serial.print(raw);
  Serial.print("  |  V: ");
  Serial.print(volts, 3);
  Serial.print(" V  |  Blink ON/OFF: ");
  Serial.print(time);
  Serial.println(" ms");

  digitalWrite(LED_PIN, HIGH);  
  delay(time);
  digitalWrite(LED_PIN, LOW);  
  delay(time);

}
