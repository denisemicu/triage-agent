
# Claude Partner Network Triage Prototype

This is a small prototype of the application triage workflow I designed for the Claude Partner Network.

The main idea is pretty simple: I don't want Claude making up policy or acting as the final gatekeeper for partner applications.

Instead, Claude does the work it is best suited for — reading the application, pulling out the relevant information, linking that information back to evidence, and identifying anything that is missing or contradictory.

From there, explicit program requirements are evaluated by a deterministic rules engine.

The goal is to automate the repetitive work around the decision while keeping humans focused on the cases that actually require judgment.

## How it works

```text
Application submitted
        ↓
Claude extracts + structures the evidence
        ↓
Deterministic policy checks
        ↓
Qualified / Review Required / Not Qualified
        ↓
Human review where needed
