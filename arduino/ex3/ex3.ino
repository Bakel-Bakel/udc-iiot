const uint8_t PWM_PIN = D2;

void setup(){
  pinMode(PWM_PIN, OUTPUT);
  analogWriteFreq(1000);
  analogWriteRange(1023);
}

void loop() {
  static uint8_t step = 0;                
  uint16_t duty = (step * 1023) / 5;      
  analogWrite(PWM_PIN, duty);
  delay(2000);
  step = (step + 1) % 6;
}