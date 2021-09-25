#!/bin/bash

cluster_name=$1
cluster_zone=northamerica-northeast1-a

gcloud beta container clusters update $cluster_name \   
  --zone $cluster_zone  --cluster-dns clouddns --cluster-dns-scope cluster

  