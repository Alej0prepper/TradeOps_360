# TradeOps 360 Agent Guide

## Project purpose

TradeOps 360 is a single Odoo 17 project developed incrementally throughout its learning course. It must become both a functional application for commercial and import operations and an understandable record of how the application evolved.

Read `README.md`, `docs/roadmap.md`, `docs/vision.md`, `docs/architecture.md`, and `CHANGELOG.md` before making architecture or domain decisions. Treat `docs/roadmap.md` as the progression contract.

## Current baseline

- Infer the current implementation baseline from the roadmap, vision, architecture, changelog, existing code, and learning and decision records. Do not assume or state a fixed lesson day as the baseline.
- Use the most recently documented and observable functionality to determine what is already available, then use the roadmap to identify the next permitted scope.
- Do not introduce functionality belonging to a later roadmap milestone. In particular, do not add infrastructure, models, views, security, demo data, tests, or a separate backend unless the current permitted scope requires it.

## Architecture rules

- TradeOps runs inside Odoo; it is not an independent service or backend.
- Reuse standard Odoo models whenever Odoo already owns the business concept. Extend them with `_inherit` when necessary; do not create duplicates such as `trade.customer`, `trade.product`, or `trade.sale`.
- Create TradeOps models only for genuine custom domains: imports, presales, distribution, and supplier reconciliation.
- Use the Odoo ORM for ordinary business logic. Direct SQL requires an explicit technical justification because it may bypass framework behavior and security.
- Preserve multi-company and multi-warehouse compatibility. Never assume one company exists or equate a company with a warehouse.

## Incremental delivery

- Implement only the scope of the current roadmap milestone. Do not introduce future-class functionality early.
- Every lesson must leave a functional, coherent, and observable improvement over the preceding state.
- Record significant architecture or domain choices in `docs/decisions/` using a numbered decision record.
- Record material learning transformations in `docs/learning/`; explain what changed, why, the Odoo concept involved, and the resulting behavior.
- Update `CHANGELOG.md` for notable user-facing, architectural, or release changes. Describe the concrete before-and-after behavior in a short narrative: enough to tell the change's story, without repeating implementation details.

## Code and documentation

- Prefer clear Odoo conventions and small, focused changes over speculative abstractions.
- Keep code comments for non-obvious domain or technical decisions, not basic Python syntax.
- Keep long-form explanations in `docs/`.
- When adding a model or workflow in later milestones, document the business problem, standard Odoo models reused, company and warehouse ownership, security needs, traceability, and test approach.

## Git workflow

- Inspect the working tree before staging; do not stage unrelated files.
- Make one coherent commit per meaningful change or lesson checkpoint, using Conventional Commit-style messages.
- Run relevant format, test, and validation commands before committing. At this baseline, verify documentation links, Markdown structure, and repository scope.
- Do not force-push, rewrite shared history, or publish changes unless the user explicitly authorizes it.

## Completion checks

Before handing off a change, confirm that it satisfies the relevant roadmap milestone, no future features were introduced, documentation reflects the decision, and the working tree contains only expected changes.
