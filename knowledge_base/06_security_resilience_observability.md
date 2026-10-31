# Security, Resilience, and Observability

## API security: authentication and authorization
Authentication proves who you are; authorization decides what you may do. In cloud-native APIs the dominant patterns are:
- OAuth 2.0: an authorization framework where a client obtains a scoped access token from an authorization server to call a resource server on a user's behalf. It defines grant types such as authorization code (for web apps) and client credentials (for service-to-service).
- OpenID Connect (OIDC): an identity layer on top of OAuth 2.0 that adds authentication and an ID token.
- JWT (JSON Web Token): a signed, self-contained token carrying claims; it lets resource servers validate a request statelessly without a database lookup. Always validate the signature, issuer, audience, and expiry.
- API keys: simple shared secrets suitable for identifying applications, but not users, and must be transmitted only over TLS.

## Defense in depth
Cloud-native security applies controls at every layer: TLS everywhere (including mutual TLS between services), the principle of least privilege for identities and network policies, secret management with a vault rather than plaintext, image scanning for vulnerabilities, and a zero-trust posture where no network location is implicitly trusted. Rate limiting and quotas protect against abuse and denial of service.

## Rate limiting and throttling
Rate limiting caps how many requests a client may make in a time window, protecting backends from overload and ensuring fair use. Common algorithms are the token bucket and the leaky bucket. When a client exceeds its limit the API returns HTTP 429 Too Many Requests, ideally with a Retry-After header. This is usually enforced at the API gateway.

## Resilience patterns
Distributed systems must expect partial failure. Key patterns:
- Timeout: never wait indefinitely for a downstream call.
- Retry with exponential backoff and jitter: retry transient failures without creating a thundering herd.
- Circuit breaker: after repeated failures, "open" the circuit and fail fast for a cooldown period, giving the struggling dependency time to recover, then probe with half-open state.
- Bulkhead: isolate resources (thread pools, connection pools) so one failing dependency cannot exhaust everything.
- Graceful degradation and fallback: return a cached or default response when a dependency is unavailable.

## The three pillars of observability
Observability is the ability to understand a system's internal state from its outputs. Its three pillars are:
- Logs: discrete, timestamped, structured event records; in cloud-native systems they are written to stdout as JSON and aggregated centrally.
- Metrics: numeric time-series aggregates (request rate, error rate, latency, saturation) exposed for systems like Prometheus and visualized in Grafana.
- Traces: distributed traces follow a single request across service boundaries via a propagated trace context, revealing where latency accrues. OpenTelemetry is the vendor-neutral standard for instrumenting all three.

## SLIs, SLOs, and error budgets
A Service Level Indicator (SLI) is a measured quantity such as the fraction of successful requests. A Service Level Objective (SLO) is the target for an SLI, for example 99.9% availability. The error budget is the allowed shortfall (0.1%); as long as the budget is not exhausted, teams can ship features quickly, and when it is, they prioritize reliability. This aligns velocity with stability.

## The RED and USE methods
The RED method monitors request-driven services by Rate, Errors, and Duration. The USE method monitors resources by Utilization, Saturation, and Errors. Together they give a practical starting point for what to measure in a cloud-native system.
