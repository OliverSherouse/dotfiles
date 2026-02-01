---
name: spec
description: Interview me and draft/update a single living domain spec under ./specs/ (spec-driven development, vertical-slice domains; not one spec per change).
---

## What I do

I help maintain "living specs" for a project:

- One spec per logical domain / vertical slice (not one spec per change)
- Specs live in `./specs/` at the project root
- Git history is the changelog; specs evolve over time

## Operating rules

- Ask as many questions as needed; do not assume missing details.
- Prefer updating an existing spec over creating a new one.
- Do not write implementation code until the spec is accepted.
- Keep decisions explicit: tradeoffs, alternatives considered, and why.

## Interview flow (repeat until complete)

1. Identify the domain spec to update:
   - Ask for the domain name and intended spec filename under `specs/` (or propose one).
   - If a matching spec exists, read it and ask what's changing.
2. Establish intent:
   - What problem are we solving? Why now?
   - Who is the user/customer (even if internal)?
   - What does success look like (measurable if possible)?
3. Define scope:
   - In-scope / out-of-scope
   - Non-goals
   - Constraints (time, compatibility, security, cost, ops)
4. Behavior and interfaces:
   - UX / CLI behavior (if any)
   - APIs/contracts (if any)
   - Data model / state changes
   - Infrastructure/Terraform impact (if any)
5. Safety and quality:
   - Failure modes and recovery
   - Security/privacy considerations
   - Observability (logs/metrics), rollout/rollback
   - Testing strategy
6. Acceptance criteria:
   - Crisp, testable bullets
7. Confirm:
   - Summarize open questions and assumptions
   - Ask for approval to write/update the spec file(s)

## Spec template (write/update `specs/<domain>.md`)

# <Domain>: <Title>

## Context

## Problem

## Goals

## Non-goals

## Scope

## Proposed Approach

## Alternatives Considered

## Interfaces / UX

## Data / State

## Infrastructure (Terraform)

## Risks & Mitigations

## Rollout / Migration

## Testing Strategy

## Acceptance Criteria

## Open Questions

## Decision Log
