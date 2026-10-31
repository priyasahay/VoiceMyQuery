"""Held-out evaluation questions for comparing RAG vs fine-tuning.

Mix of:
  * in-domain questions whose answer IS in the knowledge base (both should do well)
  * paraphrased questions (tests generalization)
  * out-of-scope questions (tests honesty: RAG should say "I don't know";
    a fine-tuned small model is more likely to hallucinate)
"""

IN_DOMAIN = [
    "What is the difference between PUT and PATCH?",
    "Explain the circuit breaker pattern.",
    "Why should cloud-native processes be stateless?",
    "What are the three pillars of observability?",
    "What is the saga pattern used for?",
    "How does a readiness probe differ from a liveness probe?",
    "What does HTTP 429 mean and what causes it?",
    "What is GitOps?",
]

PARAPHRASED = [
    "If a service keeps failing, what pattern stops the failures from cascading?",
    "How do I stop one client from overwhelming my API with requests?",
    "What keeps Kubernetes from sending traffic to a pod that isn't ready yet?",
    "How can I roll out a new version to only 5% of users first?",
]

OUT_OF_SCOPE = [
    "What is the capital of France?",
    "How do I bake sourdough bread?",
    "What were the main causes of World War I?",
]

ALL = (
    [("in_domain", q) for q in IN_DOMAIN]
    + [("paraphrased", q) for q in PARAPHRASED]
    + [("out_of_scope", q) for q in OUT_OF_SCOPE]
)
