# Run-coordinator test fixtures

This package contains test-owned workflow and task doubles used to exercise orchestration admission, failure, and recovery boundaries. They are explicit simulations, not production commands, scientific-runtime substitutes, or evidence that the real workflow executed.

The workflow fixture and `with_owner_doubles` declare `execution_mode: test-double`
in newly constructed Attempts, including successors. They retain all Run, source,
required-tool and dummy storage identities; their injected runtime/storage callbacks
supply simulation behavior. No retained Attempt is rewritten. Production plan
assertions and real managed E2E continue to use `local-science-tools` and actual
runtime/storage admission. The existing public v4 schema still admits both modes;
retiring that compatibility is a separate decision, not a fixture rename.
