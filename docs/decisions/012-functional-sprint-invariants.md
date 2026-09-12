# Decision 012 - Functional sprint and invariant ownership

The approved phase-one plan supersedes the lesson-number gate for this branch, not the architectural rules. Standard Odoo owns partners, products, purchases, physical inventory, quotations and sales. TradeOps owns import approval, commercial commitments, operational incidents and commercial reconciliation.

Three additive roles are introduced: Consultation, Operator and Responsible. Operators also receive the standard operational groups needed for purchases, sales and inventory; Responsible receives their management groups. These grants are intentionally explicit and are not accounting-administrator grants. Companies remain limited by each user's allowed companies and record rules. Shared port catalogs are global and maintained by Responsible.

Document and child mixins centralize only common invariants: automatic reference, initial state, company, immutable generated links, parent editability and row locking. They do not implement a generic workflow engine. Business actions own their specific transitions. Private server methods perform validated state changes without accepting a client context flag that disables validation.

A row lock is acquired only after ACL and record-rule checks. The SQL statement locks existing rows and does not mutate business data; writes, constraints and Chatter still pass through the ORM. PostgreSQL uniqueness remains the final guarantee for generated one-to-one business links. Repeated conversion returns the existing quotation. Serialization failures must be retried in a fresh transaction by the request boundary.

A broad role can have broad standard application access; Consultation is not a universal deny rule because Odoo permissions are additive. Tests use users without unrelated extra groups to verify each role independently.
