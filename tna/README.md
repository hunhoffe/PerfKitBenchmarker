# Using PKB for TNA Netperf Pod-to-Pod tests


## Setup
Clone this repo/branch:
```
cd $HOME
git clone https://github.com/hunhoffe/PerfKitBenchmarker.git
cd $HOME/PerfKitBenchmarker
git checkout --track origin/netperf-docker-image
```

On the prinary node of the tnak8s profile, install dependencies and config with:
```bash
cd $HOME/PerfKitBenchmarker/tna
./setup.sh
```


### Image Setup
This shouldn't be necessary, but if you need to rebuild the image for whatever reason:
```bash
cd $HOME/PerfKitBenchmarker/tna
docker build -t <user>/<name> .
```


## Run Experiments


#### Intra-node

Disable scheduling on one worker so as to force them to run on a single worker:
```
kubectl cordon <node name>
```

With one pair:
```bash
./pkb.py --cloud=Kubernetes --benchmarks=netperf --kubectl=/usr/bin/kubectl --kubeconfig=/users/hunhoffe/.kube/config --image=hunhoffe/pkb-netperf --nokubernetes_anti_affinity --nouse_k8s_vm_node_selectors
```

Re-enable the worker with:
```
kubectl uncordon <node name>
```


#### Inter-node

With one pair:
```bash
./pkb.py --cloud=Kubernetes --benchmarks=netperf --kubectl=/usr/bin/kubectl --kubeconfig=/users/hunhoffe/.kube/config --image=hunhoffe/pkb-netperf
```


## Plotting Experimental Data


#### Throughput

TODO


#### Latency CDF

Run with:
```
$HOME/PerfKitBenchmarker/latency_cdf.py /my/results/from/running/test.json
```
This will output a CSV file which can be used to plot the CDF using matplotlib or similar.


## Notes on Configuration

Note that the number of histogram buckets is baked into the image, so that parameter is no longer functional.

Some other parameters of interest: 
```
`--netperf_benchmarks`: The netperf benchmark(s) to run.
    (default: 'TCP_RR,TCP_CRR,TCP_STREAM')
    (a comma separated list)

`--netperf_max_iter`: Maximum number of iterations to run during confidence interval estimation. If unset, a single iteration will be run.
    (an integer in the range [3, 30])

`--netperf_max_iter`: Maximum number of iterations to run during confidence interval estimation. If unset, a single iteration will be run.
    (an integer in the range [3, 30])

`--netperf_mss`: Sets the Maximum Segment Size (in bytes) for netperf TCP tests to use. The effective MSS will be slightly smaller than the value specified here. If you try to set an MSS higher than the current MTU, the MSS will be set to the highest possible value for that
    MTU. If you try to set the MSS lower than 88 bytes, the default MSS will be used.
    (an integer)

`--netperf_num_streams`: Number of netperf processes to run. Netperf will run once for each value in the list.
    (default: '1')
    (A comma-separated list of integers or integer ranges. Ex: -1,3,5:7 is read as -1,3,5,6,7.)

`--netperf_tcp_stream_send_size_in_bytes`: Send size to use for TCP_STREAM tests (netperf -m flag)
    (default: '131072')
    (an integer)

`--netperf_test_length`: netperf test length, in seconds
    (default: '60')
    (a positive integer)

`--netperf_histogram_buckets`: The number of buckets per bucket array in a netperf histogram. Netperf keeps one array for latencies in the single usec range, one for the 10-usec range, one for the 100-usec range, and so on until the 10-sec range. The default value that
    netperf uses is 100. Using more will increase the precision of the histogram samples that the netperf benchmark produces.
    (default: '100')
    (an integer)

`--[no]use_k8s_vm_node_selectors`: Whether to require node selectors to be present when creating K8s VMs. Disable this if you are using a pre-existing k8s cluster without labels.
    (default: 'true')
```

This documentation here (https://github.com/GoogleCloudPlatform/PerfKitBenchmarker/wiki/PerfKitBenchmarker-Configurations) shows 
