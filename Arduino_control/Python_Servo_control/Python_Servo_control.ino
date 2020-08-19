#include <Servo.h>
Servo roll_servo; 
Servo pitch_servo;
Servo left_servo;
Servo right_servo;

String roll_byte;
String pitch_byte;
String left_byte;
String right_byte;

int roll_pos;
int pitch_pos;
int left_pos;
int right_pos;

void setup() {
 
  roll_servo.attach(10);
  pitch_servo.attach(9);
  left_servo.attach(5);
  right_servo.attach(6);
  Serial.begin(9600);
  
  // Head (both servos):
  // Send [0,100] -> translate to -50 +50 

  // Right Hand:
  // Send [0,50] -> translate to -25 +25. Center @ 75 (greater angles are "opening hand")
    
  // Left Hand:
  // Send [0,50] -> translate to -25 +25. Center @ 105 (greater angles are "closing hand")
}

void loop()
{    
  if(Serial.available())  // if data available in serial port
    { 
    roll_byte = Serial.readStringUntil('r'); // read data until ,
    pitch_byte = Serial.readStringUntil('p'); // read data until ,
    left_byte = Serial.readStringUntil('l'); // read data until ,
    right_byte = Serial.readStringUntil('\n'); // read data until newline

    int roll = roll_byte.toInt();   // change datatype from string to integer
    int pitch = pitch_byte.toInt();   // change datatype from string to integer
    int left = left_byte.toInt();   // change datatype from string to integer
    int right = right_byte.toInt();   // change datatype from string to integer

//    roll_pos, pitch_pos, left_pos, right_pos = mapping_position(roll_pos, pitch_pos, left_pos, right_pos);
    mapping_position(roll, pitch, left, right);
    
    
    roll_servo.write(roll_pos);     // move servo
    pitch_servo.write(pitch_pos);     // move servo
    left_servo.write(left_pos);     // move servo
    right_servo.write(right_pos);     // move servo
    
//    Serial.println(String("roll Servo in position: ") + roll_pos);
//    Serial.println(String("Pitch Servo in position: ") + pitch_pos);
//    Serial.println(String("left Servo in position: ") + left_pos);
//    Serial.println(String("right Servo in position: ") + right_pos);
    
    }
    delay(50);

}


void mapping_position(float roll, float pitch, float left, float right)
{
   // Head (both servos):
  // Send [0,100] -> translate to -50 +50 

  // Right Hand:
  // Send [0,50] -> translate to -25 +25. Center @ 75 (greater angles are "opening hand")
    
  // Left Hand:
  // Send [0,50] -> translate to -25 +25. Center @ 105 (greater angles are "closing hand")

  roll_pos = ((roll - 50) / 50) * 45 + 90;
  pitch_pos = ((pitch - 50) / 50) * 45 + 90;  

  left_pos = (left - 25) + 75;
  right_pos = ((right - 25) * -1) + 105;
  
  limitation();
//  return roll, pitch, left, right;
}



void limitation()
{
  int max_head = 135;
  int min_head = 45;
  int max_left = 120;
  int min_left = 80;
  int max_right = 90;
  int min_right = 60;

  if (roll_pos > max_head) roll_pos= max_head;
  if (roll_pos < min_head) roll_pos= min_head;
  if (pitch_pos > max_head) pitch_pos = max_head;
  if (pitch_pos < min_head) pitch_pos = min_head;

  if (left_pos > max_left) left_pos = max_left;
  if (left_pos < min_left) left_pos = min_left;
  if (right_pos > max_right) right_pos = max_right;
  if (right_pos < min_right) right_pos = min_right;

//  return roll, pitch, left, right;

}
