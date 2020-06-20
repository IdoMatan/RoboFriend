#include <Servo.h>
Servo myservo1; 
Servo myservo2;
String inByte1;
String inByte2;
int pos1;
int pos2;

void setup() {
 
  myservo1.attach(10);
  myservo2.attach(9);
  Serial.begin(9600);
}

void loop()
{    
  if(Serial.available())  // if data available in serial port
    { 
    inByte1 = Serial.readStringUntil(','); // read data until ,
    inByte2 = Serial.readStringUntil('\n'); // read data until newline

    pos1 = inByte1.toInt();   // change datatype from string to integer
    pos2 = inByte2.toInt();   // change datatype from string to integer
            
    myservo1.write(pos1);     // move servo
    myservo2.write(pos2);     // move servo
    
    Serial.print("Servo in position 1: ");  
    Serial.println(inByte1);
    Serial.print("Servo in position 2: ");  
    Serial.println(inByte2);
    }
    delay(50);

}
