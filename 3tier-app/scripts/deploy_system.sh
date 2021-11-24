#!/bin/bash

gcloud container clusters get-credentials cluster-1 --zone northamerica-northeast1-a --project my-project-1509758122771

kubectl apply -f ../monitor/deploy.yaml
kubectl apply -f ../services/monitor.yaml
sleep 2

kubectl apply -f ../tier1/deploy.yaml
kubectl apply -f ../tier2/deploy.yaml
#kubectl apply -f ../controller/deploy.yaml
kubectl apply -f ../services/tier1.yaml
kubectl apply -f ../services/tier2.yaml
kubectl apply -f ../services/monitor-ext.yaml
#kubectl apply -f ../services/ctrl-ext.yaml
kubectl apply -f ../services/tier1-ext.yaml

kubectl apply -f ../services/tier1-mntext.yaml
kubectl apply -f ../services/tier2-mntext.yaml
kubectl apply -f ../services/client-mntext.yaml

kubectl apply -f ../controller/vpa_tier1.yaml
kubectl apply -f ../controller/vpa_tier2.yaml

sleep 3
kubectl apply -f ../client/deploy.yaml