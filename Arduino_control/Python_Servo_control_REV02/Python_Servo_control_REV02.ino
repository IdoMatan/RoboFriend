#include <math.h>
#include <Servo.h>

Servo roll_servo;
Servo pitch_servo;
Servo left_servo;
Servo right_servo;

String roll_byte;
String pitch_byte;
String left_byte;
String right_byte;

int roll_pos = 90;
int pitch_pos = 90;
int left_pos = 75;
int right_pos = 105;

int roll_pos_last = 90;
int pitch_pos_last = 90;
int left_pos_last = 75;
int right_pos_last = 105;


float delta_roll;
float delta_pitch;
float delta_left;
float delta_right;

void setup() {

  roll_servo.attach(10);
  pitch_servo.attach(9);
  left_servo.attach(5);
  right_servo.attach(6);
  Serial.begin(9600);
}

void loop()
{
  if (Serial.available()) // if data available in serial port
  {
    update_last_pose();

    roll_byte = Serial.readStringUntil('r'); // read data until ,
    pitch_byte = Serial.readStringUntil('p'); // read data until ,
    left_byte = Serial.readStringUntil('l'); // read data until ,
    right_byte = Serial.readStringUntil('\n'); // read data until newline

    int roll = roll_byte.toInt();   // change datatype from string to integer
    int pitch = pitch_byte.toInt();   // change datatype from string to integer
    int left = left_byte.toInt();   // change datatype from string to integer
    int right = right_byte.toInt();   // change datatype from string to integer

    mapping_position(roll, pitch, left, right);

    update_pose();


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

  right_pos = (left - 25) + 75;
  left_pos= ((right - 25) * -1) + 105;

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

  if (roll_pos > max_head) roll_pos = max_head;
  if (roll_pos < min_head) roll_pos = min_head;
  if (pitch_pos > max_head) pitch_pos = max_head;
  if (pitch_pos < min_head) pitch_pos = min_head;

  if (left_pos > max_left) left_pos = max_left;
  if (left_pos < min_left) left_pos = min_left;
  if (right_pos > max_right) right_pos = max_right;
  if (right_pos < min_right) right_pos = min_right;

  //  return roll, pitch, left, right;

}

void update_pose()
{
  float sigmo;
  float delta_pos;
  int temp;

  delta();

  for (float i = -6; i <= 6; i += 0.1 )
  {
    sigmo = sigmoid(i);

//    roll_servo.write(roll_pos_last + sigmo * delta_roll);
//    pitch_servo.write(int (pitch_pos_last + sigmo * delta_pitch));
//    left_servo.write(int (left_pos_last + sigmo * delta_left));
//    right_servo.write(int (right_pos_last + sigmo * delta_right));

    roll_servo.write(roll_pos_last + sigmo * delta_roll);
    pitch_servo.write(pitch_pos_last + sigmo * delta_pitch);
    left_servo.write(left_pos_last + sigmo * delta_left);
    right_servo.write(right_pos_last + sigmo * delta_right);
    
    
    delay(10);

  }
//  temp = left_pos_last + sigmo * delta_left;
//    Serial.println(temp);   
}


void update_last_pose() {

  roll_pos_last = roll_pos;
  pitch_pos_last = pitch_pos;
  left_pos_last = left_pos;
  right_pos_last = right_pos;
}


void delta() {
  delta_roll = roll_pos - roll_pos_last;
  delta_pitch = pitch_pos - pitch_pos_last;
  delta_left = left_pos - left_pos_last;
  delta_right = right_pos - right_pos_last;
}

float sigmoid(float x)
{
  float exp_value;
  float return_value;

  exp_value = exp((double) - x);

  /*** Final sigmoid value ***/
  return_value = 1 / (1 + exp_value);

  return return_value;
}
