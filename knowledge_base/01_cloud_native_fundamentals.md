# Cloud-Native Fundamentals

## What "cloud-native" means
Cloud-native is an approach to building and running applications that fully exploits the elasticity, on-demand provisioning, and managed services of cloud platforms. The Cloud Native Computing Foundation (CNCF) defines cloud-native technologies as those that empower organizations to build and run scalable applications in modern, dynamic environments such as public, private, and hybrid clouds. Containers, service meshes, microservices, immutable infrastructure, and declarative APIs are the representative techniques.

The core properties of a cloud-native system are: elasticity (scale out and in with demand), resilience (survive partial failure), observability (you can infer internal state from external outputs), and automation (no manual, hand-crafted deployment steps).

## The twelve-factor app
The twelve-factor methodology is the canonical checklist for cloud-native services:
1. Codebase — one codebase tracked in version control, many deploys.
2. Dependencies — explicitly declare and isolate dependencies.
3. Config — store configuration in the environment, never in code.
4. Backing services — treat databases, queues, caches as attached resources bound by URL.
5. Build, release, run — strictly separate these stages.
6. Processes — execute the app as one or more stateless processes.
7. Port binding — export services via port binding; the app is self-contained.
8. Concurrency — scale out by running more processes, not bigger ones.
9. Disposability — fast startup and graceful shutdown maximize robustness.
10. Dev/prod parity — keep development, staging, and production as similar as possible.
11. Logs — treat logs as event streams written to stdout.
12. Admin processes — run admin/management tasks as one-off processes.

## Statelessness and externalized state
Cloud-native processes should be stateless and share-nothing. Any data that must persist goes to a backing service (database, object store, cache). This is what lets an orchestrator kill and recreate a pod anywhere in the cluster without data loss, and lets you scale horizontally by simply adding identical replicas.

## Immutable infrastructure
Instead of patching running servers in place, you build a new immutable artifact (a container image) for every change and replace the running instances. This eliminates configuration drift and makes rollbacks trivial: you just redeploy the previous image tag.

## Declarative APIs and desired state
Cloud-native platforms are driven by declarative APIs: you describe the desired end state (for example, "run three replicas of version 2.1") and a control loop continuously reconciles reality toward that state. This is the opposite of imperative scripting, where you specify each step. Kubernetes is the archetype of this reconciliation-loop model.
