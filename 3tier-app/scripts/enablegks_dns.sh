#!/bin/bash

cluster_name="cluster-1"
cluster_zone="europe-central2-a"

gcloud beta container clusters update $cluster_name \
--cluster-dns clouddns --cluster-dns-scope cluster  --zone $cluster_zone

  