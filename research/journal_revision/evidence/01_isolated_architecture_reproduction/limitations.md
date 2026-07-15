# Limitations

1. **Architecture verification only.** The evaluator checks conformance to implementation requirements. It does not measure clinical accuracy, sensitivity, specificity, completeness, patient outcomes, or pharmacist decision quality.
2. **Self-authored expected outcomes.** The evaluated scenarios and their expected behavior were produced within the same project. The clean rerun reduces environment uncertainty but does not add independent adjudication.
3. **Synthetic data only.** Fixtures contain no real patients or reference clinical cases and do not evaluate the quality of DDInter-derived records.
4. **Schema creation bypasses Alembic.** The committed Alembic `upgrade()` remains empty. `Base.metadata.create_all()` demonstrates that the current model metadata can create the necessary tables, not that the repository has a reproducible migration history.
5. **Unpinned repository dependencies.** The exact resolved environment is archived, but `requirements.txt` remains unpinned and could resolve differently later.
6. **Prerequisites are not one-command installed.** The retained harness automates cluster initialization, databases, repetitions, and teardown after PostgreSQL and Python dependencies are available. This task built PostgreSQL and the virtual environment outside the repository, but those build/install steps are not yet encoded in the runner.
7. **No real import reproduction.** The exact DDInter release, source files, checksums, and import accounting remain unavailable. The test starts from synthetic fixtures rather than rebuilding the profiled database.
8. **External-service flags are path assertions.** The evaluator uses failing sentinels on selected boundaries and reports no external calls. It does not prove that every untested route is network-independent.
9. **Three repetitions are limited.** They show consistent deterministic outcomes in one machine/environment, not cross-platform or independent-laboratory reproducibility.
10. **No concurrency or load testing.** The sub-second times are not a performance benchmark and should not support latency, capacity, or reliability claims.
11. **Security remediation is unresolved.** The reproduction avoids the committed remote URL but does not rotate credentials, inspect provider logs, remove secrets from active files/history, or assess database contents.
12. **Application defects remain visible.** Passing the authored scenarios does not correct known issues such as duplicate-medication self-pair counting, incomplete attempted-run auditing, hard-coded run-level source reporting, shallow LLM validation, absent authentication, or broad CORS.
