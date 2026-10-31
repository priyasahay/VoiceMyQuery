# API Design for Cloud-Native Solutions

## APIs as the contract
In a cloud-native system, every capability is exposed as an API. The API is the stable contract between independently deployed services and between the platform and its clients. Good API design decouples producers from consumers: the consumer depends only on the published contract, not on the internal implementation.

## REST
REST (Representational State Transfer) models everything as a resource identified by a URI and manipulated with a uniform set of HTTP verbs:
- GET retrieves a resource and must be safe and idempotent (no side effects).
- POST creates a subordinate resource and is neither safe nor idempotent.
- PUT replaces a resource and is idempotent.
- PATCH partially updates a resource.
- DELETE removes a resource and is idempotent.
Status codes carry meaning: 2xx success, 3xx redirection, 4xx client error (400 bad request, 401 unauthorized, 403 forbidden, 404 not found, 409 conflict, 429 too many requests), 5xx server error. Richardson's maturity model describes levels from plain RPC-over-HTTP up to hypermedia (HATEOAS).

## API versioning
Because consumers cannot all upgrade at once, APIs must be versioned. Common strategies: URI versioning (/v1/orders), header versioning (Accept: application/vnd.api.v2+json), and content negotiation. The golden rule is backward compatibility: additive changes (new optional fields, new endpoints) are safe; removing or renaming fields or changing types is a breaking change that requires a new version.

## GraphQL vs REST
GraphQL exposes a single endpoint with a typed schema; clients request exactly the fields they need in one round trip, which avoids the over-fetching and under-fetching common in REST. REST is simpler to cache at the HTTP layer and maps cleanly to resources. GraphQL shines for aggregating many backends behind one graph and for mobile clients that want to minimize payloads.

## gRPC
gRPC uses HTTP/2 and Protocol Buffers for compact binary, strongly typed, high-performance RPC. It supports unary and streaming calls and is popular for internal service-to-service communication where low latency and code-generated clients matter. It is less browser-friendly than REST/JSON, which is why gRPC-Web or a REST gateway is often placed at the edge.

## Idempotency and safety
Idempotency means performing an operation multiple times has the same effect as performing it once. In distributed systems, retries are inevitable, so write operations should accept an idempotency key so a retried POST does not create duplicate records. Designing for idempotency is essential to safe retries and exactly-once semantics.

## API gateway
An API gateway is the single entry point in front of many services. It centralizes cross-cutting concerns: authentication and authorization, TLS termination, rate limiting and throttling, request routing, response aggregation, caching, and request/response transformation. This keeps individual services focused on business logic.

## OpenAPI and contract-first design
OpenAPI (formerly Swagger) is a machine-readable specification of a REST API. Contract-first design means writing the OpenAPI document before the code, then generating server stubs, client SDKs, mock servers, and documentation from it. This makes the contract the single source of truth and enables parallel development of producer and consumer.
