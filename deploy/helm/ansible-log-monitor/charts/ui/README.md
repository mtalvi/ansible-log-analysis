# Frontend Gradio UI Helm Chart

This Helm chart deploys the Ansible Logs Viewer Gradio UI application to Kubernetes.

## Overview

The chart provides a complete deployment for the Gradio-based web interface that allows users to view and analyze Ansible logs through an interactive dashboard.

## Features

- **Deployment**: Complete Kubernetes deployment with health checks
- **Service**: ClusterIP service exposing the Gradio app on port 7860
- **ConfigMap**: Environment configuration for backend connectivity
- **HPA**: Horizontal Pod Autoscaler for automatic scaling
- **Ingress**: Optional ingress configuration for external access
- **ServiceAccount**: Dedicated service account for the application

## Configuration

### Key Values

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Container image repository | `quay.io/ansible-logs/ui` |
| `image.tag` | Container image tag | `latest` |
| `service.port` | Service port | `7860` |
| `configMap.backendUrl` | Backend service URL | `http://backend:8000` |
| `autoscaling.enabled` | Enable HPA | `true` |
| `autoscaling.minReplicas` | Minimum replicas | `1` |
| `autoscaling.maxReplicas` | Maximum replicas | `5` |
| `resources.requests.cpu` | CPU request | `200m` |
| `resources.requests.memory` | Memory request | `512Mi` |
| `resources.limits.cpu` | CPU limit | `500m` |
| `resources.limits.memory` | Memory limit | `1Gi` |

### Environment Variables

The application is configured with the following environment variables:

- `BACKEND_URL`: URL of the backend service (from ConfigMap)
- `GRADIO_SERVER_NAME`: Server binding address (`0.0.0.0`)
- `GRADIO_SERVER_PORT`: Server port (`7860`)

## Installation

```bash
# Install the chart
helm install ansible-logs-ui .

# Install with custom values
helm install ansible-logs-ui . -f custom-values.yaml

# Upgrade the chart
helm upgrade ansible-logs-ui .
```

## Accessing the Application

### Port Forward (Development)
```bash
kubectl port-forward svc/ansible-logs-ui-ui 7860:7860
```
Then access http://localhost:7860

### Ingress (Production)
Enable ingress in values.yaml:
```yaml
ingress:
  enabled: true
  hosts:
    - host: ansible-logs-ui.your-domain.com
      paths:
        - path: /
          pathType: Prefix
```

## Health Checks

The application includes:
- **Liveness Probe**: HTTP GET on `/` with 30s initial delay
- **Readiness Probe**: HTTP GET on `/` with 5s initial delay

## Scaling

Horizontal Pod Autoscaler automatically scales based on:
- CPU utilization (target: 70%)
- Memory utilization (target: 80%)

## Testing

Run Helm tests:
```bash
helm test ansible-logs-ui
```

## Troubleshooting

Check pod status:
```bash
kubectl get pods -l app.kubernetes.io/name=ui
```

View logs:
```bash
kubectl logs -l app.kubernetes.io/name=ui
```

Check ConfigMap:
```bash
kubectl get configmap ansible-logs-ui-ui-config -o yaml
```
