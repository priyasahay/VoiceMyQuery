# Microservices Architecture

## From monolith to microservices
A monolith packages all functionality in a single deployable unit. Microservices decompose the system into small, independently deployable services, each owning a single business capability and its own data. The benefits are independent deployability, technology heterogeneity, fault isolation, and team autonomy. The costs are operational complexity, network latency, distributed data management, and harder end-to-end testing.

## Decomposition strategies
Services are typically bounded by business capability or by Domain-Driven Design bounded contexts. Each service should be loosely coupled and highly cohesive. A good heuristic: if two services must always be deployed together, they probably belong together. Avoid the "distributed monolith" anti-pattern, where services are physically separate but so tightly coupled that they cannot change independently.

## Database per service
Each microservice owns its data and exposes it only through its API. No other service reads its tables directly. This preserves encapsulation and lets each service pick the datastore that fits its access pattern (polyglot persistence). The trade-off is that queries and transactions spanning services become distributed problems.

## Synchronous vs asynchronous communication
Synchronous (request/response over REST or gRPC) is simple and immediate but creates temporal coupling: the caller is blocked and fails if the callee is down. Asynchronous (messaging over a broker such as Kafka or RabbitMQ) decouples services in time, improving resilience and enabling event-driven flows, at the cost of eventual consistency and harder reasoning about ordering.

## Event-driven architecture
In event-driven systems, services publish events ("OrderPlaced") that other services subscribe to, rather than calling each other directly. This yields loose coupling and natural scalability. Event sourcing stores state as an append-only log of events; CQRS (Command Query Responsibility Segregation) separates the write model from optimized read models.

## The saga pattern
Because you cannot hold a distributed ACID transaction across services, long-running business transactions use sagas: a sequence of local transactions where each step publishes an event triggering the next, and failures trigger compensating transactions that undo prior steps. Sagas can be choreographed (services react to each other's events) or orchestrated (a central coordinator drives the steps).

## Service discovery
In a dynamic cluster, service instances come and go with changing IP addresses, so clients cannot hardcode locations. A service registry (such as Consul, etcd, or Kubernetes' built-in DNS) tracks healthy instances. Client-side discovery has the client query the registry and load-balance; server-side discovery puts a load balancer or the platform in between.

## The strangler fig pattern
To migrate a monolith incrementally, you place a facade in front of it and route individual capabilities to new microservices one at a time, gradually "strangling" the monolith until it can be retired. This avoids a risky big-bang rewrite.
