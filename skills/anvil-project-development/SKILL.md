---
name: anvil-project-development
description: Develop and extend Java/Spring Boot + Vue projects built on the ZBITI Anvil platform. Use when Codex needs to inspect an unfamiliar Anvil repository, design a table-backed feature, configure and run the Anvil Maven code generator, place generated API/service/rest/autoconfiguration/mapper files into the correct modules, place generated Vue and API files under the correct frontend paths, align backend request mappings with menu component paths and permission strings, add business logic without corrupting generated layers, or verify an Anvil feature end to end.
---

# Anvil Project Development

Follow the host repository's instructions and detected Anvil version. Treat this skill as a workflow and safety rail, not as a fixed project template.

## Start with discovery

1. Read every applicable `AGENTS.md`, project README, root `pom.xml`, module POMs, frontend `package.json`, Vite config, router loader, and environment/profile documentation.
2. Run the read-only audit before proposing paths:

   ```bash
   python <skill-dir>/scripts/inspect_anvil_project.py <project-root>
   ```

3. Identify:
   - backend root and Anvil/platform version;
   - generator module, plugin version, goal, output directory, table selection, package parent, and request mapping;
   - business `api`, `service`, `rest`, and `rest-spring-boot-starter` modules;
   - frontend root, `src/views`, `src/api`, platform aliases, and dynamic menu loader;
   - database dialect/profile, dictionary conventions, permissions, data-scope mechanism, and nearby reference feature.
4. Do not infer paths only from module names. Use an adjacent working feature in the same repository as the local standard.
5. Never print or copy literal database passwords, API keys, or tokens discovered in generator/config files. Report only that a literal secret exists.

Read [generator-and-placement.md](references/generator-and-placement.md) before generating or moving code. Read [backend-extension.md](references/backend-extension.md) before changing Java/MyBatis code. Read [frontend-menu.md](references/frontend-menu.md) before editing Vue APIs, routes, menus, or permission values. Read [verification-and-delivery.md](references/verification-and-delivery.md) before testing or handing off.

## Convert the request into an implementation contract

Before editing, write a compact contract containing:

- business entity/table and ownership;
- roles and row-level visibility;
- state transitions and validation rules;
- standard CRUD endpoints to inherit versus custom actions to add;
- page path, API path, route path, menu component value, and button permissions;
- dictionaries and audit fields;
- acceptance tests, migration needs, and rollback expectations.

Resolve contradictions before generating code. A generator accelerates a known design; it does not replace one.

## Design the schema first

1. Follow the repository's table, primary-key, audit-column, logical-delete, sequence, character-set, and migration conventions.
2. Put meaningful comments on tables and columns because generator labels, Swagger descriptions, Excel annotations, and Vue fields may derive from them.
3. Create dictionary types and values for stable coded states. Use constants/enums/dictionary classes in business code instead of raw string literals.
4. Add unique constraints and indexes for actual business invariants and query patterns.
5. Keep schema migration and seed/menu/dictionary data versioned. Never make an undocumented manual-only database change.

## Generate into staging

1. Configure the existing Anvil generator; do not hand-write baseline CRUD when the repository already uses it.
2. Select only the intended table. Verify `requestMapping`, package parent, ID strategy, logical-delete fields, database dialect, MDA setting, and Vue version.
3. Keep the generator output outside production source trees. Treat it as staging even when `fileOverride=true`.
4. For the common `zbiti-generator-maven-plugin`, confirm the installed goal from the POM/plugin descriptor. A typical invocation is:

   ```bash
   mvn -f <backend-root>/generator-code/pom.xml zbiti-generator:code
   ```

5. Inspect all generated files before copying. Reject wrong packages, wrong URL prefixes, missing fields, unexpected tables, or incompatible Vue syntax.
6. Produce a source-to-destination manifest and copy by layer. Do not bulk-copy an unreviewed generated tree.
7. Preserve existing user changes. For regeneration, diff generated bases and merge intentionally; never overwrite business extension files blindly.

## Extend rather than replace platform conventions

- Keep schema-derived boilerplate in `*GeneratorDomain`, `*GeneratorMapper`, and generator mapper XML.
- Put custom fields in the non-generator `*Domain`; custom mapper methods/XML in the non-generator mapper; business rules in the service implementation/interface; custom HTTP actions in the controller.
- Reuse `IBaseService`, `BaseServiceImpl`, and `IBaseController` where the local project does so. Do not duplicate inherited CRUD endpoints.
- Register services in the project's auto-configuration/starter pattern when component scanning does not create them automatically.
- Put authorization, data-scope, audit logging, transactions, idempotency, and state-transition checks at the same layers used by nearby Anvil features.
- Treat dynamic SQL fragments such as `${dataScope}` as framework-controlled only. Never bind them from client input.
- Guard all generated map/entity update or delete operations against empty conditions.

## Align the endpoint, frontend, menu, and permissions

Maintain one mapping ledger per resource:

```text
table                <table_name>
backend mapping      /<module>/<resource>
frontend API folder  src/api/<module>/<resource>/
frontend view file   src/views/<module>/<resource>/index.vue
menu component       derive from router loader; often <module>/<resource>/index
permissions          <module>:<resource>:search|insert|update|delete|...
```

The physical Vue path and menu component value are not necessarily identical. Verify them with:

```bash
python <skill-dir>/scripts/verify_menu_component.py <frontend-root> <component-or-physical-path>
```

In common Anvil Vue 3 projects, a physical file such as `src/views/acme/order/index.vue` maps to menu component `acme/order/index`, because the router loader adds `src/views/` and `.vue`. Platform-owned pages may instead use aliases such as `@base/...`. Always inspect the repository's loader; do not hardcode this example.

## Customize the generated Vue page

1. First make the generated page and API compile in their final paths.
2. Remove irrelevant generated fields; then add business-specific forms, tables, dictionaries, validation, and actions.
3. Reuse the project's request wrapper and response envelope. Match the platform's actual HTTP conventions even if they differ from generic REST conventions.
4. Keep query field suffixes (`Like`, ranges, ordering fields) consistent with generated mapper behavior.
5. Match each button permission to backend/menu permission data. Test hidden buttons and direct API access separately.
6. Preserve route component naming and case exactly; Windows may hide casing mistakes that fail on Linux.

## Work in short verified slices

Implement in this order:

1. migration and dictionary/menu seed data;
2. generated backend baseline in final modules;
3. backend compile and CRUD smoke test;
4. generated frontend baseline in final paths;
5. menu component resolution and permissions;
6. business rules and custom actions;
7. frontend business interactions;
8. focused tests, module builds, integration tests, and full build where feasible.

After each slice, inspect the diff. Distinguish new failures from pre-existing repository failures and report both accurately.

## Definition of done

Do not call the feature complete until:

- generated and custom layers are placed correctly and imports/packages resolve;
- migration, dictionaries, menus, roles, and button permissions are reproducible;
- menu component resolves to an existing case-correct file;
- standard CRUD and custom actions enforce validation, authorization, data scope, logging, and transactions;
- frontend search, pagination, sorting, create, edit, delete, empty/error/loading states, and refresh behavior are checked as applicable;
- affected backend modules and frontend files pass focused validation;
- no secret, generated staging artifact, debug endpoint, or unrelated change is included;
- the handoff lists changed files, commands run, known pre-existing failures, and any manual deployment step.
