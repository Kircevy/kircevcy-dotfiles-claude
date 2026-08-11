# Verification and delivery

## Focused verification order

1. Validate migration syntax against the configured database profile.
2. Compile the changed API module.
3. Compile/test the changed service module and mapper XML.
4. Compile the REST and starter modules.
5. Start or test the runnable gateway with the intended profiles.
6. Smoke-test inherited CRUD and every custom action.
7. Run lint/type checks for changed frontend files.
8. Build the frontend bundle when repository health permits.
9. Log in with representative roles and verify menus, buttons, data scope, and direct API access.

Prefer the smallest command that exercises the changed layer before a full reactor build. Use the repository's documented profiles and commands.

## Contract smoke tests

- create valid and invalid records;
- partial update without erasing omitted fields;
- select by ID;
- filtered search with deterministic ordering and pagination;
- single and batch delete under valid permissions;
- duplicate-key and foreign-key failures;
- dictionary rendering;
- row-level data scope;
- audit fields and operation log;
- custom state transitions, retry, and idempotency.

## Diagnose failures accurately

- Capture the exact failing command and first actionable error.
- Determine whether the failure touches a changed file.
- Run a focused check on the changed file/module if the full repository already fails.
- Do not claim the build passes when only lint passes.
- Do not attribute a pre-existing missing module or dependency to the current feature.

## Handoff format

Lead with the delivered outcome, then list:

- schema/menu/dictionary changes;
- backend files and inherited versus custom endpoints;
- frontend physical path and menu component value;
- permissions and roles tested;
- commands run and results;
- known pre-existing failures;
- required deployment steps, configuration, or cache/menu refresh.

Exclude generator staging output, secrets, temporary credentials, debug logs, and unrelated worktree changes from the handoff.
