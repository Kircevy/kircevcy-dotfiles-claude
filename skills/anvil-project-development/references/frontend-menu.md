# Frontend, route, menu, and permission alignment

## Keep four paths distinct

1. **Physical view path:** e.g. `src/views/acme/order/index.vue`.
2. **Frontend API path:** e.g. `src/api/acme/order/index.js`.
3. **Menu component value:** interpreted by the dynamic router loader.
4. **Browser route path:** configured by the menu route tree; it need not equal the component path.

Do not store `src/views/...` in the menu merely because that is the physical path. Inspect the loader.

## Common Anvil Vue 3 rule

When the router contains logic equivalent to:

```ts
const viewsModulesImport = import.meta.glob('../views/**/*.vue')
component = viewsModulesImport[`../views/${route.component}.vue`]
```

the mapping is:

```text
physical file:  src/views/acme/order/index.vue
menu component: acme/order/index
```

Do not include `src/views/` or `.vue` in that menu value.

When the router maps aliases such as `@base/` into `src/platform/base/views/base/`, keep the platform alias form for platform-owned pages. Business pages normally belong under the application's `src/views`, not a bundled platform module.

Use the verifier:

```bash
python <skill-dir>/scripts/verify_menu_component.py <frontend-root> acme/order/index
python <skill-dir>/scripts/verify_menu_component.py <frontend-root> src/views/acme/order/index.vue
```

## Endpoint and permission ledger

For a request mapping `/acme/order`, align:

```text
search endpoint      /acme/order/search
insert endpoint      /acme/order/insert
update endpoint      /acme/order/updateRowNotNullById
delete endpoint      /acme/order/deleteByIds
search permission    acme:order:search
insert permission    acme:order:insert
update permission    acme:order:update
delete permission    acme:order:delete
```

These names are common generator defaults; inspect the generated controller/API and local menu model before using them.

## Frontend adaptation checklist

- Move generated API and view files together so imports resolve.
- Keep the project's request wrapper, response envelope, loading convention, and error handling.
- Remove generated fields that users should not edit, especially IDs, audit fields, internal JSON, ownership, and server-managed status.
- Replace free-text coded fields with platform dictionary selectors/tags.
- Add field validation and operation confirmations.
- Pass backend ordering before pagination; do not sort only the current page in the browser.
- Verify component name/casing, route cache behavior, and Linux-sensitive path casing.
- Verify button permissions and direct API authorization separately.
- Exercise empty, loading, validation, permission-denied, server-error, and success states.
