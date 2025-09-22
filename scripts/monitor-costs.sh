#!/bin/bash

# GKE Cost Monitoring Script
echo "🔍 GKE Cost Optimization Monitor"
echo "================================"

# Check cluster status
echo "📊 Cluster Status:"
gcloud container clusters list --format="table(name,location,status,currentNodeCount,currentMasterVersion)"

# Check node pool details
echo -e "\n🖥️  Node Pool Details:"
gcloud container node-pools list --cluster=careercompass-cluster --zone=us-central1-a --format="table(name,machineType,diskSizeGb,diskType,preemptible,autoscaling.enabled,autoscaling.minNodeCount,autoscaling.maxNodeCount)"

# Check pod resource usage
echo -e "\n📈 Pod Resource Usage:"
kubectl top pods --all-namespaces

# Check HPA status
echo -e "\n⚖️  Horizontal Pod Autoscaler Status:"
kubectl get hpa

# Cost estimation
echo -e "\n💰 Estimated Monthly Costs:"
echo "• e2-micro node (preemptible): ~$1.50/month"
echo "• Standard disk (20GB): ~$0.80/month"
echo "• Load balancer: ~$18/month"
echo "• Total estimated: ~$20-25/month"

echo -e "\n💡 Cost Optimization Tips:"
echo "• Use preemptible instances (60-80% cheaper)"
echo "• Scale to zero when not in use"
echo "• Use smallest machine types"
echo "• Monitor resource usage regularly"
