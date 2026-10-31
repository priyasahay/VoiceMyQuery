"""Build the supervised fine-tuning dataset (Iteration 2).

Unlike RAG, fine-tuning bakes knowledge into the model weights, so we need
instruction/response pairs. These are hand-authored from the SAME knowledge
base the RAG index uses, so the two iterations can be compared fairly on
held-out questions.

    python -m finetune.prepare_dataset   ->  finetune/data/train.jsonl
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

# (question, answer) pairs grounded in knowledge_base/*.md
PAIRS: list[tuple[str, str]] = [
    ("What does cloud-native mean?",
     "Cloud-native is an approach to building and running applications that fully exploits cloud elasticity and managed services. Its core properties are elasticity, resilience, observability, and automation, typically realized with containers, microservices, and declarative APIs."),
    ("List the twelve-factor app principles.",
     "The twelve factors are: one codebase, explicit dependencies, config in the environment, backing services as attached resources, separate build/release/run stages, stateless processes, port binding, concurrency by process, disposability, dev/prod parity, logs as event streams, and admin tasks as one-off processes."),
    ("Why must cloud-native processes be stateless?",
     "Statelessness lets an orchestrator kill and recreate a process anywhere in the cluster without data loss and lets you scale horizontally by adding identical replicas. Any data that must persist is externalized to a backing service like a database, cache, or object store."),
    ("What is immutable infrastructure?",
     "Immutable infrastructure means you never patch a running server in place; instead you build a new immutable artifact, such as a container image, for every change and replace the running instances. This eliminates configuration drift and makes rollbacks trivial by redeploying the previous image."),
    ("What is a declarative API?",
     "A declarative API lets you describe the desired end state, such as running three replicas of version 2.1, while a control loop continuously reconciles reality toward that state. This contrasts with imperative scripting, where you specify each individual step. Kubernetes is the archetype."),
    ("What is the difference between PUT and PATCH?",
     "PUT replaces an entire resource and is idempotent, so repeating it has the same effect. PATCH applies a partial update to specific fields. Both differ from POST, which creates a subordinate resource and is neither safe nor idempotent."),
    ("Which HTTP methods are idempotent?",
     "GET, PUT, and DELETE are idempotent: performing them multiple times has the same effect as once. GET is also safe because it has no side effects. POST is neither safe nor idempotent, which is why write operations often use an idempotency key to make retries safe."),
    ("What does HTTP status code 429 mean?",
     "429 Too Many Requests means the client has exceeded its rate limit. The server ideally returns a Retry-After header telling the client when to try again. Rate limiting is usually enforced at the API gateway to protect backends from overload."),
    ("Compare REST and GraphQL.",
     "REST models resources with URIs and HTTP verbs and is easy to cache at the HTTP layer. GraphQL exposes a single endpoint with a typed schema so clients fetch exactly the fields they need in one request, avoiding over-fetching and under-fetching. GraphQL suits aggregating many backends and minimizing mobile payloads."),
    ("What is gRPC and when should I use it?",
     "gRPC is a high-performance RPC framework using HTTP/2 and Protocol Buffers for compact, strongly typed binary messages with streaming support. It is ideal for low-latency internal service-to-service calls. Because it is less browser-friendly, teams often put gRPC-Web or a REST gateway at the edge."),
    ("How should I version an API?",
     "Common strategies are URI versioning like /v1/orders, header versioning via the Accept header, and content negotiation. The golden rule is backward compatibility: additive changes such as new optional fields are safe, while removing or renaming fields or changing types is breaking and requires a new version."),
    ("What is an API gateway?",
     "An API gateway is the single entry point in front of many services. It centralizes cross-cutting concerns such as authentication, TLS termination, rate limiting, routing, response aggregation, caching, and request transformation, so individual services can focus on business logic."),
    ("What is idempotency and why does it matter?",
     "Idempotency means performing an operation multiple times has the same effect as performing it once. In distributed systems retries are inevitable, so write operations should accept an idempotency key to prevent a retried POST from creating duplicate records. It is essential for safe retries."),
    ("What is OpenAPI and contract-first design?",
     "OpenAPI is a machine-readable specification of a REST API. Contract-first design means writing the OpenAPI document before the code, then generating server stubs, client SDKs, mocks, and documentation from it. The contract becomes the single source of truth and enables parallel development."),
    ("What are microservices and their trade-offs?",
     "Microservices decompose a system into small, independently deployable services, each owning one business capability and its own data. Benefits are independent deployability, technology heterogeneity, fault isolation, and team autonomy. Costs are operational complexity, network latency, distributed data management, and harder end-to-end testing."),
    ("What is the database-per-service pattern?",
     "Each microservice owns its data and exposes it only through its API; no other service reads its tables directly. This preserves encapsulation and enables polyglot persistence, where each service picks the datastore that fits its needs. The trade-off is that cross-service queries and transactions become distributed problems."),
    ("Compare synchronous and asynchronous communication in microservices.",
     "Synchronous request/response over REST or gRPC is simple and immediate but creates temporal coupling, since the caller is blocked and fails if the callee is down. Asynchronous messaging over a broker like Kafka or RabbitMQ decouples services in time, improving resilience, at the cost of eventual consistency."),
    ("What is the saga pattern?",
     "A saga manages a long-running business transaction across services as a sequence of local transactions, where each step publishes an event triggering the next, and failures trigger compensating transactions that undo prior steps. Sagas can be choreographed via events or orchestrated by a central coordinator."),
    ("What is event-driven architecture?",
     "In event-driven architecture, services publish events like OrderPlaced that others subscribe to, rather than calling each other directly, which yields loose coupling and scalability. Event sourcing stores state as an append-only log of events, and CQRS separates the write model from optimized read models."),
    ("What is service discovery?",
     "In a dynamic cluster, instances come and go with changing IP addresses, so clients cannot hardcode locations. A service registry such as Consul, etcd, or Kubernetes DNS tracks healthy instances. Client-side discovery has the client query the registry and load-balance; server-side discovery uses a load balancer or the platform."),
    ("What is the strangler fig pattern?",
     "The strangler fig pattern migrates a monolith incrementally by placing a facade in front of it and routing individual capabilities to new microservices one at a time, gradually strangling the monolith until it can be retired. This avoids a risky big-bang rewrite."),
    ("What is a container and how does it differ from a VM?",
     "A container packages an application with all its dependencies into a portable, isolated unit. Unlike a virtual machine, a container shares the host operating system kernel and isolates only the process space, so it is lightweight and starts in milliseconds. Docker popularized the build, ship, and run workflow."),
    ("What is a Dockerfile?",
     "A Dockerfile is the declarative recipe that builds a container image layer by layer. The image is an immutable artifact and a container is a running instance of it. Multi-stage builds keep final images small by discarding build-time tooling."),
    ("What are the core Kubernetes objects?",
     "Key objects are the Pod, the smallest deployable unit; the ReplicaSet, which keeps a set number of replicas; the Deployment, which manages rolling updates; the Service, a stable virtual IP that load-balances across pods; Ingress for external HTTP routing; and ConfigMaps and Secrets for configuration."),
    ("How does Kubernetes self-heal?",
     "Kubernetes controllers run a reconciliation loop that continuously compares desired state, stored in etcd, with actual state and acts to converge them. If a pod dies, the ReplicaSet controller notices the shortfall and schedules a replacement, which is the essence of self-healing."),
    ("Explain Kubernetes health probes.",
     "Kubernetes uses three probes. A liveness probe restarts a deadlocked container. A readiness probe removes a pod from the Service load balancer until it can serve traffic. A startup probe protects slow-starting apps from being killed prematurely. Correct probes are essential for zero-downtime deployments."),
    ("How does autoscaling work in Kubernetes?",
     "The Horizontal Pod Autoscaler adds or removes pod replicas based on CPU, memory, or custom metrics. The Vertical Pod Autoscaler adjusts resource requests. The Cluster Autoscaler adds or removes nodes. Requests and limits let the scheduler pack pods efficiently and protect nodes from exhaustion."),
    ("What is a service mesh?",
     "A service mesh like Istio or Linkerd adds a sidecar proxy next to every service to transparently handle service-to-service concerns such as mutual TLS, retries, timeouts, circuit breaking, traffic splitting for canaries, and telemetry. It moves these concerns out of application code into the platform."),
    ("What is the difference between continuous delivery and continuous deployment?",
     "Continuous delivery keeps every change in a deployable state and makes releasing a one-click business decision. Continuous deployment goes further and automatically pushes every change that passes the pipeline to production with no human gate. The difference is whether a human approves the final promotion."),
    ("What are the stages of a CI/CD pipeline?",
     "A typical pipeline runs source, build, test, scan, publish, deploy, and verify stages. Code is compiled and containerized, tested at multiple levels, scanned for vulnerabilities, pushed to a registry, deployed to staging then production, and verified with smoke tests. Artifacts are built once and promoted unchanged."),
    ("What is GitOps?",
     "GitOps makes a Git repository the single source of truth for desired state. An in-cluster agent such as Argo CD or Flux continuously pulls the repo and reconciles the cluster to match it. Deployments happen by merging a pull request and rollbacks by reverting a commit, giving a full audit trail."),
    ("What is Infrastructure as Code?",
     "Infrastructure as Code manages infrastructure through declarative, version-controlled files rather than manual clicks. Tools like Terraform and Helm make infrastructure reproducible, reviewable, and auditable. Applying the same configuration always yields the same result, thanks to idempotency."),
    ("Compare blue-green and canary deployments.",
     "Blue-green runs two identical environments and switches all traffic from the old to the new at once, enabling instant rollback. Canary routes a small percentage of traffic to the new version, watches metrics, and progressively increases if healthy. Both reduce the blast radius of a bad release."),
    ("What are the DORA metrics?",
     "The DORA metrics measure software delivery performance: deployment frequency, lead time for changes, change failure rate, and mean time to recovery. They balance speed against stability and are the standard way to assess a team's delivery capability."),
    ("Explain OAuth 2.0 and OpenID Connect.",
     "OAuth 2.0 is an authorization framework where a client obtains a scoped access token from an authorization server to call a resource server on a user's behalf, with grant types such as authorization code and client credentials. OpenID Connect adds an identity layer on top, providing authentication and an ID token."),
    ("What is a JWT and how do I validate it?",
     "A JWT is a signed, self-contained token carrying claims, letting a resource server validate a request statelessly without a database lookup. You must always validate the signature, issuer, audience, and expiry before trusting it."),
    ("How does rate limiting work?",
     "Rate limiting caps how many requests a client may make in a time window to protect backends and ensure fair use. Common algorithms are the token bucket and the leaky bucket. When a client exceeds the limit the API returns 429 Too Many Requests, ideally with a Retry-After header, usually at the gateway."),
    ("What is a circuit breaker?",
     "A circuit breaker prevents cascading failure: after repeated failures to a dependency it opens the circuit and fails fast for a cooldown period, giving the dependency time to recover, then probes with a half-open state before closing again. It is a core resilience pattern in distributed systems."),
    ("Explain retries with exponential backoff and jitter.",
     "Retrying transient failures improves resilience, but naive immediate retries can overwhelm a recovering service. Exponential backoff increases the wait between attempts, and added random jitter spreads retries out to avoid a thundering herd where many clients retry in lockstep."),
    ("What is the bulkhead pattern?",
     "The bulkhead pattern isolates resources such as thread pools or connection pools so that one failing dependency cannot exhaust everything and take down the whole service. It is named after the watertight compartments in a ship's hull."),
    ("What are the three pillars of observability?",
     "The three pillars are logs, discrete timestamped event records; metrics, numeric time-series aggregates like request rate, error rate, and latency; and traces, which follow a single request across service boundaries. OpenTelemetry is the vendor-neutral standard for instrumenting all three."),
    ("What are SLIs, SLOs, and error budgets?",
     "A Service Level Indicator is a measured quantity such as the fraction of successful requests. A Service Level Objective is the target for that indicator, for example 99.9% availability. The error budget is the allowed shortfall; while it is not exhausted teams ship features, and when it is they prioritize reliability."),
    ("What are the RED and USE monitoring methods?",
     "The RED method monitors request-driven services by Rate, Errors, and Duration. The USE method monitors resources by Utilization, Saturation, and Errors. Together they give a practical starting point for what to measure in a cloud-native system."),
    ("What is defense in depth in cloud-native security?",
     "Defense in depth applies security controls at every layer: TLS everywhere including mutual TLS between services, least privilege for identities and network policies, secret management with a vault, image vulnerability scanning, and a zero-trust posture where no network location is implicitly trusted."),
    ("What is a distributed monolith and why is it bad?",
     "A distributed monolith is an anti-pattern where services are physically separate but so tightly coupled that they must be deployed together and cannot change independently. It combines the operational complexity of microservices with the rigidity of a monolith, so you pay the costs without the benefits."),
]


def main() -> None:
    config.FINETUNE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = config.FINETUNE_DATA_DIR / "train.jsonl"
    with out.open("w", encoding="utf-8") as fh:
        for q, a in PAIRS:
            record = {
                "messages": [
                    {"role": "system", "content": config.SYSTEM_PROMPT},
                    {"role": "user", "content": q},
                    {"role": "assistant", "content": a},
                ]
            }
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"[dataset] wrote {len(PAIRS)} examples to {out}")


if __name__ == "__main__":
    main()
