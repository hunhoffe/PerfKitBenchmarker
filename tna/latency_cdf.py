#!/usr/bin/env python3

# Modified from https://github.com/GoogleCloudPlatform/PerfKitBenchmarker/wiki/Plotting-Netperf-CDFs
import collections
import json
import re
import sys


def main():
  if len(sys.argv) != 2:
      print("usage: %s samples_file.json" % sys.argv[0])
      sys.exit(1)
  latency_histogram_by_zone = collections.defaultdict(
          lambda : collections.defaultdict(int))
  total_samples = collections.defaultdict(int)
  with open(sys.argv[1]) as samples_file:
    for line in samples_file.readlines():
      sample = json.loads(line)
      if sample['metric'] == 'TCP_RR_Latency_Histogram':
        labels = sample['labels']
        zone = re.search(r'\|sending_zone:(.*?)\|', labels).group(1)
        histogram = json.loads(
                re.search(r'\|histogram:(.*?)\|', labels).group(1))
        for bucket, count in histogram.items():
          latency_histogram_by_zone[zone][float(bucket)] += int(count)
          total_samples[zone] += int(count)
  print(','.join(["zone", "bucket", "percentile"]))
  for zone, histogram in latency_histogram_by_zone.items():
    running_count = 0
    for bucket in sorted(histogram):
      running_count += histogram[bucket]
      percentile = 100.0 * running_count / total_samples[zone]
      print(','.join((zone, str(bucket), str(percentile))))


if __name__ == "__main__":
    main()
