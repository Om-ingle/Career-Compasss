#!/bin/bash

# Manual Scaling Script for Cost Optimization
echo "💰 GKE Manual Cost Optimization"
echo "==============================="

# Function to scale down (save costs)
scale_down() {
    echo "📉 Scaling down for cost savings..."
    
    # Scale deployments to minimum
    kubectl scale deployment mock-data-api --replicas=1
    kubectl scale deployment ai-agent --replicas=1
    
    echo "✅ Scaled down to minimum replicas"
    echo "💰 Estimated cost savings: 50%"
}

# Function to scale up (for high usage)
scale_up() {
    echo "📈 Scaling up for high usage..."
    
    # Scale deployments for better performance
    kubectl scale deployment mock-data-api --replicas=2
    kubectl scale deployment ai-agent --replicas=2
    
    echo "✅ Scaled up for better performance"
    echo "⚠️  Higher costs but better performance"
}

# Function to check current status
check_status() {
    echo "📊 Current Deployment Status:"
    kubectl get deployments
    echo ""
    echo "📈 Current Pod Status:"
    kubectl get pods
    echo ""
    echo "💰 Resource Usage:"
    kubectl top pods
}

# Function to schedule scaling (cron job setup)
setup_schedule() {
    echo "⏰ Setting up scheduled scaling..."
    echo ""
    echo "To automatically scale down during off-hours, add these to your crontab:"
    echo ""
    echo "# Scale down at 10 PM (22:00) daily"
    echo "0 22 * * * /path/to/your/script/manual-scale.sh down"
    echo ""
    echo "# Scale up at 8 AM (08:00) daily"
    echo "0 8 * * * /path/to/your/script/manual-scale.sh up"
    echo ""
    echo "Run: crontab -e"
    echo "Add the lines above"
}

# Main script logic
case "$1" in
    "down")
        scale_down
        ;;
    "up")
        scale_up
        ;;
    "status")
        check_status
        ;;
    "schedule")
        setup_schedule
        ;;
    *)
        echo "Usage: $0 {down|up|status|schedule}"
        echo ""
        echo "Commands:"
        echo "  down     - Scale down to save costs"
        echo "  up       - Scale up for performance"
        echo "  status   - Check current status"
        echo "  schedule - Show cron job setup"
        echo ""
        echo "Examples:"
        echo "  $0 down      # Save costs"
        echo "  $0 up        # Better performance"
        echo "  $0 status    # Check status"
        ;;
esac
