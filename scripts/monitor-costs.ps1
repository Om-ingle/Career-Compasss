# GKE Cost Monitoring Script (Windows PowerShell)
Write-Host "GKE Cost Optimization Monitor" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green

Write-Host "Cluster Status:" -ForegroundColor Cyan
gcloud container clusters list --format="table(name,location,status,currentNodeCount,currentMasterVersion)"

Write-Host "`nNode Pool Details:" -ForegroundColor Cyan
gcloud container node-pools list --cluster=careercompass-cluster --zone=us-central1-a --format="table(name,machineType,diskSizeGb,diskType,preemptible,autoscaling.enabled,autoscaling.minNodeCount,autoscaling.maxNodeCount)"

Write-Host "`nPod Resource Usage:" -ForegroundColor Cyan
kubectl top pods --all-namespaces

Write-Host "`nHorizontal Pod Autoscaler Status:" -ForegroundColor Cyan
kubectl get hpa

Write-Host "`nEstimated Monthly Costs:" -ForegroundColor Yellow
Write-Host "• e2-micro node (preemptible): ~$1.50/month" -ForegroundColor White
Write-Host "• Standard disk (20GB): ~$0.80/month" -ForegroundColor White
Write-Host "• Load balancer: ~$18/month" -ForegroundColor White
Write-Host "• Total estimated: ~$20-25/month" -ForegroundColor Green

Write-Host "`nCost Optimization Tips:" -ForegroundColor Yellow
Write-Host "• Use preemptible instances (60-80% cheaper)" -ForegroundColor White
Write-Host "• Scale to minimum when not in use" -ForegroundColor White
Write-Host "• Use smallest machine types" -ForegroundColor White
Write-Host "• Monitor resource usage regularly" -ForegroundColor White