#!/bin/bash

cluster_name="cluster-1"
cluster_zone="northamerica-northeast1-a"

gcloud beta container clusters update $cluster_name \
--cluster-dns clouddns --cluster-dns-scope cluster  --zone $cluster_zone

  