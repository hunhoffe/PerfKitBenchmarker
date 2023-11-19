# The TNA profile uses Ubuntu20.04 so we will too
FROM ubuntu:20.04

# Non interactive (no prompts)
ARG DEBIAN_FRONTEND=noninteractive

# Update apt
RUN apt update && apt -y upgrade

# Install packages
RUN apt install -y iproute2

# Setup install directories
RUN mkdir -p /tmp/pkb && mkdir -p /opt/pkb && chmod a+rwxt /opt/pkb

# From code: See https://bugs.launchpad.net/snappy/+bug/1659719.
RUN sed -i "1 i\export PATH=$PATH:/snap/bin" ~/.bashrc
RUN sed -i "1 i\export PATH=$PATH:/snap/bin" /etc/bash.bashrc

# Install more things
RUN apt -y install ubuntu-minimal ubuntu-server ubuntu-standard

# idk why this is deleted
RUN rm -f /usr/lib/python3*/EXTERNALLY-MANAGED

# Install python dependencies
RUN apt -y install python3-distutils python3-dev

# Install other build tools
RUN apt -y install build-essential git libtool autoconf automake curl

# Setup up pip
RUN curl https://bootstrap.pypa.io/pip/get-pip.py -o get_pip.py && python3 get_pip.py
RUN mkdir -p /opt/pkb && pip3 freeze | tee /opt/pkb/requirements.txt

# Use pip to install python packages
RUN pip3 install absl-py

# Get netperf code, unpack it
RUN curl https://github.com/HewlettPackard/netperf/archive/netperf-2.7.0.tar.gz -L -o /opt/pkb/netperf-2.7.0.tar.gz
RUN cd /opt/pkb && tar xvzf netperf-2.7.0.tar.gz

# Apply netperf patches
RUN git clone https://github.com/GoogleCloudPlatform/PerfKitBenchmarker.git /PerfKitBenchmarker
RUN cp /PerfKitBenchmarker/perfkitbenchmarker/data/netperf.patch netperf.patch
RUN mv netperf.patch /opt/pkb/netperf-netperf-2.7.0/netperf.patch && chmod 755 /opt/pkb/netperf-netperf-2.7.0/netperf.patch
RUN cd /opt/pkb/netperf-netperf-2.7.0 && patch -l -p1 < netperf.patch

# Build netperf - TODO: will break some features such as # of buckets & if histogram enabled
RUN cd /opt/pkb/netperf-netperf-2.7.0 && CFLAGS=-DHIST_NUM_OF_BUCKET=100 ./configure --enable-burst --enable-demo --enable-histogram && make && make install
RUN cd /opt/pkb/netperf-netperf-2.7.0/doc/examples/ && chmod +x runemomniaggdemo.sh&& chmod +x find_max_burst.sh
