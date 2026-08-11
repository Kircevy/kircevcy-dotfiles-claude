# Backend extension rules

## Layer ownership

| Concern | Preferred location |
|---|---|
| table fields and base accessors | `*GeneratorDomain` |
| calculated/join/transient fields | non-generator `*Domain` |
| public service contract | API module `I*Service` |
| generated CRUD mapper contract | `*GeneratorMapper` |
| custom queries | non-generator `*Mapper` and mapper XML |
| validation, state changes, orchestration | service implementation |
| HTTP mapping and custom action boundary | REST controller |
| bean registration | REST Spring Boot starter auto-configuration |

## Extension sequence

1. Compile the generated baseline before adding business logic.
2. Keep inherited CRUD behavior unless requirements require a semantic custom action.
3. Use service hooks such as `beforeInsert` and `beforeUpdate` only when the local base service supports them.
4. Validate both create and partial-update semantics; do not reject omitted fields on a patch-style update.
5. Put multi-write state transitions in a transaction and make retry/idempotency behavior explicit.
6. Enforce authorization and row ownership on the server even when the frontend hides buttons.
7. Use platform logging annotations and business types on mutating custom actions.
8. Register service beans following the repository's `@Configuration`, `@Bean`, and `@ConditionalOnMissingBean` pattern.

## Generated SQL cautions

- Inspect query suffix behavior (`Like`, ranges, ordering) rather than inventing parameter names.
- Keep namespace inheritance between generator and custom mapper XML intact.
- Never expose `${dataScope}`, `${orderBy}`, or other raw SQL fragments directly to untrusted input unless the platform validates them.
- Reject empty-condition update/delete operations.
- Add deterministic ordering before pagination.
- Check database-specific statements for every supported profile; generated MySQL, Oracle, PostgreSQL, or Dameng variants can diverge.

## Codes and dictionaries

- Put stable business status values in a dictionary/constants/enums class.
- Keep database dictionary values, Java comparisons, frontend option values, and menu permissions aligned.
- Avoid expressions such as `"01".equals(status)` when a named platform/business constant exists.
- Model allowed state transitions explicitly and reject invalid transitions with a business exception.

## Integration checks

- Confirm the starter module is a dependency of the runnable gateway/application.
- Confirm mapper scanning and XML resource loading include the destination paths.
- Confirm bean names do not collide with another module.
- Confirm controller request mapping does not duplicate an inherited or existing route.
- Test data scope with at least an administrator and a restricted user.
