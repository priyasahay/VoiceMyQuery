# Containers and Kubernetes

## Containers and Docker
A container packages an application with all its dependencies into a single portable, isolated unit that runs identically across environments. Unlike a virtual machine, a container shares the host operating system kernel and isolates only the process space, so it is lightweight and starts in milliseconds. Docker popularized containers with a simple build/ship/run workflow. A Dockerfile is the declarative recipe that builds an image layer by layer; the image is an immutable artifact and a container is a running instance of it. Multi-stage builds keep final images small by discarding build-time tooling.

## Container registries
Images are stored in and pulled from registries (Docker Hub, GitHub Container Registry, cloud provider registries). Tags identify versions; using immutable digests rather than mutable tags like "latest" guarantees you deploy exactly the image you tested.

## Why orchestration
Running containers by hand does not scale: you need scheduling across many hosts, self-healing, scaling, rolling updates, service discovery, and secret management. Kubernetes is the de-facto orchestration platform that provides all of this through a declarative, reconciliation-loop model.

## Kubernetes core objects
- Pod: the smallest deployable unit, one or more tightly coupled containers sharing network and storage.
- ReplicaSet: keeps a specified number of identical pod replicas running.
- Deployment: manages ReplicaSets and provides declarative rolling updates and rollbacks.
- Service: a stable virtual IP and DNS name that load-balances across a changing set of pods.
- Ingress: HTTP/S routing from outside the cluster to Services, with host/path rules and TLS.
- ConfigMap and Secret: inject configuration and sensitive data into pods as env vars or files.
- Namespace: a virtual cluster for isolating and organizing resources.
- StatefulSet: manages stateful pods with stable identities and persistent volumes.
- DaemonSet: runs one pod per node, used for agents like log or metric collectors.

## The control loop
Kubernetes controllers continuously compare desired state (from your YAML manifests stored in etcd) with actual state and take action to converge them. If a pod dies, the ReplicaSet controller notices the shortfall and schedules a replacement. This self-healing is the essence of the platform.

## Scaling
Horizontal Pod Autoscaler (HPA) adds or removes pod replicas based on CPU, memory, or custom metrics. Vertical Pod Autoscaler adjusts resource requests. Cluster Autoscaler adds or removes nodes. Requests and limits let the scheduler pack pods efficiently and protect nodes from resource exhaustion.

## Health probes
Kubernetes uses three probes: a liveness probe restarts a container that is deadlocked, a readiness probe removes a pod from the Service load balancer until it can serve traffic, and a startup probe protects slow-starting apps from being killed prematurely. Correct probes are essential for zero-downtime deployments.

## Service mesh
A service mesh (such as Istio or Linkerd) adds a sidecar proxy next to every service to handle service-to-service concerns transparently: mutual TLS, retries, timeouts, circuit breaking, traffic splitting for canaries, and fine-grained telemetry. It moves these cross-cutting concerns out of application code and into the platform data plane, controlled by a central control plane.
