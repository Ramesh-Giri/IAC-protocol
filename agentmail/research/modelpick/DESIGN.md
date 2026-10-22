# Deterministic model-policy guard design

This document describes reusable runtime-selection lessons without private dispatch records or measured fleet history.
Historical datasets, generated results, prototypes and policy provenance live in ignored `local/site-originals/agentmail/research/modelpick/`.

## Selection and authority

The roster records approved runtime/model choices and delegation.
Research and model scores do not authorize implementation, change permission boundaries or grant account entitlement.
The launcher retains the roster model and treats guard results as advisory evidence.

## Independent checks

1. Read dated local runtime catalogues rather than assuming a model ID remains available.
2. Treat unavailable, unreadable or stale capability evidence as unknown.
3. Apply deterministic text and task-kind triggers independently of any classifier output.
4. A probabilistic security score may tighten a configured restriction, never remove one.
5. Keep site model restrictions in ignored `local/model-policy.json`, selected with `IAC_MODEL_POLICY` or `IAC_ROOT` when needed.
6. Filter candidates without adding or reordering them.
7. Keep pinned supervisor/council choices outside automatic routing.
8. Log candidate inputs, filters, survivors and the actual launched choice separately.

## Privacy and verification

Decision logs contain a task-text hash rather than task bodies.
Logs, roster snapshots and measurements can still identify private operations and must remain in local storage.
Use synthetic task fixtures for public tests, including positive, negative and ambiguous text cases.
A sanitized summary cannot reproduce measurements made on original private text.
Do not publish per-seat runtime assignments, dates or scores as generic examples.
The supported catalogue command is `agentmail/bin/catalog-check`; the supported filter is `agentmail/lib/model_guard.py`.
