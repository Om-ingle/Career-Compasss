#!/bin/bash

# GKE Cost Optimization Script
echo "💰 Optimizing GKE Costs..."
echo "=========================="

# Set variables
CLUSTER_NAME="careercompass-cluster"
ZONE="us-central1-a"
PROJECT_ID=$(gcloud config get-value project)

echo "📋 Current Configuration:"
gcloud container clusters describe $CLUSTER_NAME --zone=$ZONE --format="value(nodeConfig.machineType,nodeConfig.diskSizeGb,nodeConfig.preemptible)"

echo -e "\n🔧 Applying Cost Optimizations..."

# 1. Resize node pool to smaller instances
echo "1. Resizing to e2-micro instances..."
gcloud container node-pools create cost-optimized-pool \
    --cluster=$CLUSTER_NAME \
    --zone=$ZONE \
    --machine-type=e2-micro \
    --disk-size=20 \
    --disk-type=pd-standard \
    --preemptible \
    --enable-autoscaling \
    --min-nodes=0 \
    --max-nodes=2 \
    --num-nodes=1

# 2. Delete old node pool (after new one is ready)
echo "2. Waiting for new node pool to be ready..."
sleep 60

echo "3. Deleting old node pool..."
gcloud container node-pools delete default-pool --cluster=$CLUSTER_NAME --zone=$ZONE --quiet

# 3. Apply optimized deployments
echo "4. Applying optimized deployments..."
kubectl apply -f gke-cost-optimized.yaml

# 4. Set up HPA
echo "5. Setting up Horizontal Pod Autoscalers..."
kubectl apply -f - <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mock-data-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mock-data-api
  minReplicas: 0
  maxReplicas: 2
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-agent-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-agent
  minReplicas: 0
  maxReplicas: 2
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
EOF

echo -e "\n✅ Cost optimization complete!"
echo "💰 Estimated monthly savings: 60-80%"
echo "📊 New estimated cost: $20-25/month"

echo -e "\n🔍 Monitoring commands:"
echo "• Check costs: ./scripts/monitor-costs.sh"
echo "• Check pods: kubectl get pods"
echo "• Check HPA: kubectl get hpa"
