# Module 6: Service Discovery, Readiness & Recovery

This lab deploys an Inventory service with two replicas and a client that calls the service through the stable Kubernetes DNS name `inventory`, never through a Pod IP or Pod name.

## Architecture

```text
                         ClusterIP Service
Client Pod  ───────────►  inventory:8080
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
             inventory Pod A     inventory Pod B
             /inventory          /inventory
             /ready              /ready
```

## Prerequisites

- Docker
- `kubectl`
- Minikube, kind, or Docker Desktop Kubernetes

## Deploy with Minikube

```bash
minikube start
eval $(minikube docker-env)
docker build -t k8s-inventory:1.0 inventory/
docker build -t k8s-inventory-client:1.0 client/
kubectl apply -f k8s/inventory.yaml
kubectl apply -f k8s/client.yaml
kubectl rollout status deployment/inventory
kubectl rollout status deployment/inventory-client
```

For kind, build the images locally and load them before applying the manifests:

```bash
kind create cluster
docker build -t k8s-inventory:1.0 inventory/
docker build -t k8s-inventory-client:1.0 client/
kind load docker-image k8s-inventory:1.0 k8s-inventory-client:1.0
kubectl apply -f k8s/
```

## Evidence 1: Service discovery and two replicas

Show both Pods and the Service:

```bash
kubectl get pods -l app=inventory -o wide
kubectl get service inventory
kubectl get endpoints inventory
```

The client uses `http://inventory:8080/inventory` from `k8s/client.yaml`. View client logs:

```bash
kubectl logs deployment/inventory-client --tail=30
```

The `pod` field in the responses should show both inventory Pod names across repeated requests. Example evidence:

```text
status=200 response={"service": "inventory", "pod": "inventory-abc123", ...}
status=200 response={"service": "inventory", "pod": "inventory-def456", ...}
```

## Evidence 2: Readiness failure and recovery

Choose one Pod and turn off its readiness:

```bash
POD=$(kubectl get pods -l app=inventory -o jsonpath='{.items[0].metadata.name}')
kubectl exec "$POD" -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8080/toggle-readiness').read().decode())"
kubectl get pods -l app=inventory
kubectl get endpoints inventory
```

The Pod remains `Running` but becomes `0/1 Ready` and disappears from the Service endpoints. The other Pod remains ready and the client continues receiving successful responses.

Restore readiness:

```bash
kubectl exec "$POD" -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8080/toggle-readiness').read().decode())"
kubectl get pods -l app=inventory
kubectl get endpoints inventory
```

After the readiness probe succeeds again, the Pod returns to the Service endpoints.

## Evidence 3: Pod deletion and replacement

```bash
OLD_POD=$(kubectl get pods -l app=inventory -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod "$OLD_POD"
kubectl get pods -l app=inventory -w
```

Press `Ctrl+C` after the replacement appears. Kubernetes creates a new Pod with a different name while the Service name remains `inventory`:

```bash
kubectl get service inventory
kubectl logs deployment/inventory-client --tail=20
```

The client continues using the unchanged DNS name `inventory:8080` throughout the replacement.

## Reflection

A stable Service name gives clients one reliable DNS endpoint even when individual Pods are recreated. The Service continuously tracks only ready Pods and load-balances requests across them. This prevents clients from storing fragile Pod IP addresses or names. As a result, readiness failures and Pod replacement can happen without requiring a client configuration change.
