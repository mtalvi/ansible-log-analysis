# Annotation Interface Helm Chart

This Helm chart deploys the Ansible Log Data Annotation Interface, a Gradio-based web application for annotating pipeline outputs.

## Overview

The annotation interface is a Python application that provides a web-based UI for reviewing and annotating Ansible log analysis results. It includes feedback collection capabilities and data persistence.

## Components

This Helm chart includes the following Kubernetes resources:

### Core Resources
- **Deployment**: Runs the annotation interface application
- **Service**: Exposes the application on port 7861
- **ServiceAccount**: Provides identity for the pods
- **ConfigMap**: Contains application configuration
- **PersistentVolumeClaim**: Provides persistent storage for data and feedback

### Autoscaling & Monitoring
- **HorizontalPodAutoscaler**: Automatically scales pods based on CPU/memory usage
- **Ingress**: Optional external access configuration

### Testing
- **Test Connection**: Validates service connectivity

## Configuration

### Key Values

```yaml
# Application image
image:
  repository: annotation-interface
  tag: latest

# Service configuration
service:
  type: ClusterIP
  port: 7861
  targetPort: 7861

# Resource limits
resources:
  limits:
    cpu: 500m
    memory: 1Gi
  requests:
    cpu: 250m
    memory: 512Mi

# Autoscaling
autoscaling:
  enabled: true
  minReplicas: 1
  maxReplicas: 3
  targetCPUUtilizationPercentage: 80
  targetMemoryUtilizationPercentage: 80

# Persistent storage
persistence:
  enabled: true
  accessMode: ReadWriteOnce
  size: 10Gi
```

### Application Configuration

```yaml
appConfig:
  dataFile: "/app/data/logs/failed_lines_extracted_with_summaries.json"
  feedbackDir: "/app/data"
  serverName: "0.0.0.0"
  serverPort: 7861
```

## Installation

```bash
# Install the chart
helm install annotation-interface ./annotation-interface

# Install with custom values
helm install annotation-interface ./annotation-interface -f custom-values.yaml

# Upgrade the release
helm upgrade annotation-interface ./annotation-interface
```

## Access

After installation, the application will be available:

### Local Access (ClusterIP)
```bash
# Port forward to access locally
kubectl port-forward service/annotation-interface 7861:7861

# Then access at http://localhost:7861
```

### External Access (Ingress)
Enable ingress in values.yaml:
```yaml
ingress:
  enabled: true
  hosts:
    - host: annotation.example.com
      paths:
        - path: /
          pathType: ImplementationSpecific
```

## Storage

The chart creates a PersistentVolumeClaim for data storage:
- Input data files are mounted at `/app/data`
- Annotation feedback is stored persistently
- ConfigMap configuration is mounted at `/app/config`

## Monitoring

The application includes:
- Liveness and readiness probes
- Resource monitoring for autoscaling
- Structured logging

## Environment Variables

The chart sets the following environment variables:
- `GRADIO_SERVER_NAME`: Server bind address
- `GRADIO_SERVER_PORT`: Server port
- `PYTHONPATH`: Python module path

## Security

The chart follows security best practices:
- Non-root container execution
- Service account with minimal permissions
- Resource limits and requests
- Security context configuration

## Troubleshooting

### Check pod status
```bash
kubectl get pods -l app.kubernetes.io/name=annotation-interface
```

### View logs
```bash
kubectl logs deployment/annotation-interface
```

### Check storage
```bash
kubectl get pvc annotation-interface-data
```

### Scale manually
```bash
kubectl scale deployment annotation-interface --replicas=2
```

## Dependencies

- Kubernetes 1.19+
- Helm 3.0+
- Persistent Volume provisioner (for storage)

## Notes

- The application runs on port 7861 internally
- Data persistence requires a storage class that supports ReadWriteOnce
- Autoscaling is enabled by default
- The application expects input data at the configured data file path
