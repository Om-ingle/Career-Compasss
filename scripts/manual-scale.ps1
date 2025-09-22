# Manual Scaling Script for Cost Optimization (Windows PowerShell)
param(
    [string]$Action = "help"
)

Write-Host "GKE Manual Cost Optimization" -ForegroundColor Green
Write-Host "============================" -ForegroundColor Green

if ($Action -eq "down") {
    Write-Host "Scaling down for cost savings..." -ForegroundColor Yellow
    kubectl scale deployment mock-data-api --replicas=1
    kubectl scale deployment ai-agent --replicas=1
    Write-Host "Scaled down to minimum replicas" -ForegroundColor Green
    Write-Host "Estimated cost savings: 50%" -ForegroundColor Cyan
}
elseif ($Action -eq "up") {
    Write-Host "Scaling up for high usage..." -ForegroundColor Yellow
    kubectl scale deployment mock-data-api --replicas=2
    kubectl scale deployment ai-agent --replicas=2
    Write-Host "Scaled up for better performance" -ForegroundColor Green
    Write-Host "Higher costs but better performance" -ForegroundColor Yellow
}
elseif ($Action -eq "status") {
    Write-Host "Current Deployment Status:" -ForegroundColor Cyan
    kubectl get deployments
    Write-Host ""
    Write-Host "Current Pod Status:" -ForegroundColor Cyan
    kubectl get pods
    Write-Host ""
    Write-Host "Resource Usage:" -ForegroundColor Cyan
    kubectl top pods
}
elseif ($Action -eq "schedule") {
    Write-Host "Setting up scheduled scaling..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To automatically scale down during off-hours:" -ForegroundColor White
    Write-Host "1. Open Task Scheduler" -ForegroundColor White
    Write-Host "2. Create Basic Task" -ForegroundColor White
    Write-Host "3. Set trigger: Daily at 10:00 PM" -ForegroundColor White
    Write-Host "4. Action: Start a program" -ForegroundColor White
    Write-Host "5. Program: powershell.exe" -ForegroundColor White
    Write-Host "6. Arguments: -File `"$PSScriptRoot\manual-scale.ps1`" down" -ForegroundColor White
}
else {
    Write-Host "Usage: .\manual-scale.ps1 {down|up|status|schedule}" -ForegroundColor White
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor White
    Write-Host "  down     - Scale down to save costs" -ForegroundColor Green
    Write-Host "  up       - Scale up for performance" -ForegroundColor Green
    Write-Host "  status   - Check current status" -ForegroundColor Green
    Write-Host "  schedule - Show Windows Task Scheduler setup" -ForegroundColor Green
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor White
    Write-Host "  .\manual-scale.ps1 down      # Save costs" -ForegroundColor Cyan
    Write-Host "  .\manual-scale.ps1 up        # Better performance" -ForegroundColor Cyan
    Write-Host "  .\manual-scale.ps1 status    # Check status" -ForegroundColor Cyan
}