# Interactive RL-driven Teddy Bear
Ido & Matan

## Description
Design and implementation of a story-telling teddy-bear robot, with an RL-based algorithm for interaction control.
The robot monitors (locally) the attention of the children using image processing (ML gaze analysis) and sound analysis, while reading thru well-known children's books and learns to interact with the children as to maximise their engagement and hopefully their cognitive capabilities.

## Architecture (main idea)
The code architecture is based on our RabbitMQ ROS-like implementation of process control, allowing to simultaneously control the physical robots servos, camera, screen etc. and run the different algorithms.

On each page, the robot can decide on its next action (continue reading, ask a question, move head etc.) leveraging an Actor-Critic RL algorithm optimising the interactions.

Servo control is done using a Python-controlled Arduino and all hardware and mechanics were also built by us (so excuse us if its not product looking yet)

## Disclaimer
Project is not yet complete and is a work-in-progress so stay tuned for future updates

## Supervision
The project is done under the supervision of Prof. Tzipi-Horiwitz Kraus and Prof. Erez Karpas from the Technion and is a Masters final project in the Technion Autonomous Systems Program.
