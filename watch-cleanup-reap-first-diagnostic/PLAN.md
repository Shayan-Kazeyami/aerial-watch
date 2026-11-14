# Exact reap-first platform diagnostic, prepared only

Previous cleanup-only run43646656851 is failed and preserved. This proposal tests a distinct reap-first hypothesis, not a viewer retry or a claimed fix.

Exact independently reviewed helper watch-cleanup-reap-first/cleanup.py copied unchanged. diagnose.py calls it only with literal finite grace=0.5 and post_grace=1.0. Helper's wait timeout5s plus those graces bounds intended cleanup to approximately6.5s excluding scheduler/syscall overhead. No external parameters. The helper itself is not claimed safe for untrusted infinite bounds.

Same two cases as reviewed diagnostic: owned ordinary leader and exited leader with handshaken TERM-resistant descendant. Children self-expire20s. Parent initial handshake/leader wait max5s each; final reap max5s. Success requires exact complete two-case set, started true, initial group present, helper verified with group_absent true/leader_reaped true/no errors, final group absent and final escalation/reap success. All EPERM remains recorded failure even if later group absent.

Workflow macos-latest/Python3.12, contents read only,3minute job. Restricted push branch qa/cleanup-reap-first-20261114; exactly one branch creation/push if separately approved, no follow-up pushes/retries. No browser, packages, payload, security changes or production actions. Diagnostic JSON always uploaded. Exact runner image must be recorded from logs, not assumed identical. Only gate unit tests/syntax checks run locally. No process diagnostic or remote run.

Ten pure gate tests pass. Independent exact workflow/integration review required before approval; previous helper review is insufficient execution authorization. Source and original frozen packages untouched.
