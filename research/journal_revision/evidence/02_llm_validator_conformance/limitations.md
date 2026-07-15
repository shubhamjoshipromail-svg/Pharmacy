# Limitations

1. **No live model was evaluated.** The suite tests response enforcement, not the frequency or distribution of defects from Anthropic or another model.
2. **No clinical correctness assessment.** The cases contain obvious sentinels and do not establish whether a clinically worded explanation is correct.
3. **Project-defined contract.** Expected outcomes derive from the committed prompt, rubric, and review recommendations rather than a validated external conformance standard.
4. **Finite cases.** Thirty cases cover important failure classes but are not exhaustive. Many encodings, Unicode cases, nested structures, long outputs, and adversarial strings remain untested.
5. **Stubbed query result.** The database session is stubbed only for the list of stored drug names. This isolates the name algorithm but does not test database failures, scale, collation, or real vocabulary coverage.
6. **Semantic probes are sentinel-based.** Unsupported dose, mechanism, food, source, severity, and injection cases are deliberately obvious. Their false acceptance demonstrates absence of corresponding checks but does not measure sophisticated semantic validators.
7. **Pydantic exceptions are function-level evidence.** The actual Pydantic builder is exercised. The statement that persistence occurs before response-building is inferred from code order and was not confirmed through a full mocked provider/database integration test.
8. **No frontend behavior.** The audit does not test how validation errors or provider exceptions are displayed to a user.
9. **No remediation evaluated.** Original application code was preserved. A strict validator design and regression rerun remain future engineering work.
10. **Finding-authority boundary is out of scope.** Evidence 01 separately verifies that the tested core checker does not depend on the LLM. This audit should not be misread as showing that the LLM creates findings.
