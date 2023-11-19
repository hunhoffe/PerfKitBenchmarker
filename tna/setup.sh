#!/bin/bash

# Install dependencies
sudo apt update
sudo apt install python3-pip
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.9
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 10
pip3 install numpy==1.22.4

# Install PerfKitBenchmarker
cd $HOME
git clone https://github.com/hunhoffe/PerfKitBenchmarker.git
cd $HOME/PerfKitBenchmarker
git checkout --track origin/netperf-docker-image
pip3 install -r $HOME/PerfKitBenchmarker/requirements.txt

# Label nodes
NODE2=$(kubectl get nodes -o=custom-columns=NAME:.metadata.name | grep node2)
NODE3=$(kubectl get nodes -o=custom-columns=NAME:.metadata.name | grep node3)
kubectl label nodes $NODE2 pkb_nodepool=vm1
kubectl label nodes $NODE3 pkb_nodepool=vm2
