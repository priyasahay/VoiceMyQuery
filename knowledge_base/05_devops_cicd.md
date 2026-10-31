# DevOps and CI/CD for Cloud-Native

## DevOps culture
DevOps unifies development and operations around shared ownership of the software lifecycle, aiming for fast, frequent, reliable releases. Its pillars are automation, measurement, and a blameless culture of continuous improvement. The DORA metrics — deployment frequency, lead time for changes, change failure rate, and mean time to recovery — are the standard way to measure delivery performance.

## Continuous integration
Continuous integration (CI) means developers merge small changes to the mainline frequently, and every merge triggers an automated pipeline that builds the code, runs unit and integration tests, performs static analysis and security scanning, and produces an artifact. The goal is to detect integration problems within minutes, keeping the mainline always releasable.

## Continuous delivery vs deployment
Continuous delivery keeps every change in a deployable state and makes releasing a one-click business decision. Continuous deployment goes further: every change that passes the pipeline is automatically pushed to production with no human gate. The difference is whether a human approves the final promotion to production.

## Pipeline stages
A typical cloud-native pipeline: source (commit triggers) → build (compile, containerize) → test (unit, integration, contract, end-to-end) → scan (SAST, dependency/CVE, image scanning) → publish (push image to registry) → deploy (to staging, then production) → verify (smoke tests, monitoring). Artifacts are built once and promoted unchanged through environments to preserve dev/prod parity.

## Infrastructure as Code
Infrastructure as Code (IaC) manages infrastructure through declarative, version-controlled files rather than manual clicks. Tools like Terraform (provisioning cloud resources) and Helm (packaging Kubernetes manifests) make infrastructure reproducible, reviewable, and auditable. Immutability and idempotency are key: applying the same configuration always yields the same result.

## GitOps
GitOps makes a Git repository the single source of truth for the desired state of the system. An agent running in the cluster (such as Argo CD or Flux) continuously pulls the repo and reconciles the cluster to match it. Deployments happen by merging a pull request; rollbacks happen by reverting a commit. This gives a full audit trail and prevents configuration drift.

## Deployment strategies
- Rolling update: gradually replace old instances with new ones; the default in Kubernetes.
- Blue-green: run two identical environments and switch all traffic from blue (old) to green (new) at once, enabling instant rollback.
- Canary: route a small percentage of traffic to the new version, watch metrics, and progressively increase if healthy.
- Feature flags: decouple deployment from release by toggling features at runtime without redeploying.
These strategies reduce the blast radius of a bad release and enable zero-downtime deployments.
