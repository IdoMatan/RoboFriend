#!/bin/bash

echo Hello World!
#conda init powershell
export PATH=/home/matanweks/anaconda3/bin:$PATH
#export PATH=/home/matanweks/Apps/RoboFriend:$PATH
source /home/matanweks/anaconda3/etc/profile.d/conda.sh

conda init bash
#activate /home/matanweks/anaconda3/envs/robo_friend
conda activate /home/matanweks/anaconda3/envs/robo_friend

#activate ./anaconda3/envs/robo_friend
#source activate /home/matanweks/anaconda3/envs/robo_friend
#conda env list
#echo Hello World 2!
#conda init bash
#echo Hello World 3!
#mkdir -p /home/matanweks/Apps/RoboFriend
#mkdir -p /home/matanweks/Apps/RoboFriend/BearApp && touch /home/matanweks/Apps/RoboFriend
#mkdir -p /RoboFriend
cd ..
#cd services
#python ./BearApp.py
python ./init_services_v2.py

#python /home/matanweks/Apps/RoboFriend/services/TestService.py

#echo Hello World 4!
