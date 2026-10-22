# workflow_poc

Scaffold for workflow proof-of-concept.
Workflow: ProtocolReviewWorkflow
1. Receive a protocol ID and synthetic protocol document.
2. Validate required fields using ordinary Python code.
3. Ask the LLM to identify potential completeness issues.
4. Validate the LLM response against a strict Pydantic schema.
5. Apply deterministic rules to decide whether to generate a report or require human review.
6. Wait for an approval or rejection signal when required.
7. Record the final workflow status and audit events.