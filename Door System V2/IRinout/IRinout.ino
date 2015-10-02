/*
Read the input from two IR proximity sensors and ouput the direction
 by Alex Klimaj
 */

const int sensitivity = 180; //How far to detect movement (140 = 1m) (175 = 0.75m)
const int delaytime = 1100; //How long in ms for the output to be high
const int timebetweenreadings = 2; //Time in ms to wait between readings

int led1 = 2;
int led2 = 3;

boolean sensor1 = false;
boolean sensor2 = false;

int reading1 = 0;
int reading2 = 0;

int inputPin1 = A0;
int inputPin2 = A1;

void setup()
{
  pinMode(led1, OUTPUT);
  pinMode(led2, OUTPUT);
  // initialize serial communication with computer:
  //Serial.begin(9600);
  digitalWrite(led1, LOW);
  digitalWrite(led2, LOW);
}

void loop() {

  // read from the sensor:  
  reading1 = analogRead(inputPin1);       
  // read from the sensor:  
  reading2 = analogRead(inputPin2); 

  //Serial.println("Reading 1");
  //Serial.println(reading1);
  //Serial.println("Reading 2");
  //Serial.println(reading2);

  if (reading1 > sensitivity && reading2 > sensitivity) {
  }

  else if (reading1 > sensitivity) {
    delay(timebetweenreadings);
    reading1 = analogRead(inputPin1);
    if (reading1 > sensitivity){
      for(int i = 0; i<1000; i++){
        reading2 = analogRead(inputPin2);
        if (reading2 > sensitivity) {
          delay(timebetweenreadings);
          reading2 = analogRead(inputPin2);
          if (reading2 > sensitivity) {
            //Serial.println("IN");
            digitalWrite(led1, HIGH);
            delay(delaytime*0.1);
            digitalWrite(led1, LOW);
            delay(delaytime*0.9);
            break;
          }
        }
      }
    }
  }

  else if (reading2 > sensitivity) {
    delay(timebetweenreadings);
    reading2 = analogRead(inputPin2);
    if (reading2 > sensitivity){
      for(int i = 0; i<1000; i++){
        reading1 = analogRead(inputPin1);
        if (reading1 > sensitivity) {
          delay(timebetweenreadings);
          reading1 = analogRead(inputPin1);
          if (reading1 > sensitivity) {
            //Serial.println("OUT");
            digitalWrite(led2, HIGH);
            delay(delaytime*0.1);
            digitalWrite(led2, LOW);
            delay(delaytime*0.9);
            break;
          }
        }
      }
    }
  }  

  delay(timebetweenreadings);        // delay in between reads for stability            
}

