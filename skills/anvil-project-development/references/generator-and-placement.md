# Anvil generator and placement

## Before generation

- Read the generator POM and plugin descriptor; do not guess the goal or options.
- Use a development/schema-read account. Replace literal credentials with local properties or environment-backed Maven settings where the project supports them.
- Verify the selected table list. Never generate every table by accident.
- Set the package parent to the destination business module's real Java package, using a nearby feature as evidence.
- Set `requestMapping` deliberately. It influences controller URLs, permission prefixes, and often Vue/API directories.
- Enable MDA or Vue output only when the target project uses those artifacts.
- Point `outputDir` to staging, not checked-in source modules.

For `com.zbiti:zbiti-generator-maven-plugin` releases whose descriptor exposes prefix `zbiti-generator` and goal `code`, invoke:

```bash
mvn -f <generator-pom> zbiti-generator:code
```

If the version differs, confirm with Maven plugin help or inspect `META-INF/maven/plugin.xml` in the installed plugin JAR.

## Typical output-to-module map

| Generated relative path | Typical destination |
|---|---|
| `api/generator/domain/*GeneratorDomain.java` | `module-<business>-api/src/main/java/<package>/api/generator/domain/` |
| `api/domain/*Domain.java` | `module-<business>-api/src/main/java/<package>/api/domain/` |
| `api/mda/domain/*MdaDomain.java` | API module MDA package, only if enabled |
| `api/service/I*Service.java` | API module service package |
| `service/generator/mapper/*GeneratorMapper.java` | service module generator mapper package |
| `service/mapper/*Mapper.java` | service module custom mapper package |
| `service/service/impl/*ServiceImpl.java` | service module implementation package |
| `resources/mapper/generator/*GeneratorMapper.xml` | service module `src/main/resources/mapper/generator/` |
| `resources/mapper/*Mapper.xml` | service module `src/main/resources/mapper/` |
| `rest/controller/*Controller.java` | rest module controller package |
| `autoconfigure/*Configuration.java` | rest Spring Boot starter auto-configuration package |
| `vue-src/api/<mapping>/index.*` | frontend `src/api/<mapping>/index.*` |
| `vue-src/views/<mapping>/index.vue` | frontend `src/views/<mapping>/index.vue` |

Treat the table as a pattern, not proof. Discover actual module names and package roots first.

## Safe placement procedure

1. Record the staging tree and expected final tree.
2. Check Java package declarations against destinations.
3. Compare each generated artifact with the nearest working resource.
4. Copy new files one category at a time and compile the affected module.
5. For existing features, separate regenerable base files from extension files.
6. Diff old and new generator bases. Merge schema changes without replacing custom code.
7. Leave the staging directory untracked or remove only artifacts created by the current run after verification.

## Regeneration policy

- Regenerate `*Generator*` artifacts when the table changes.
- Review non-generator Domain, Mapper XML, Service, Controller, Configuration, Vue, and API files as merge targets, not disposable output.
- If the generator overwrites all files, generate to a clean staging directory and use a three-way/manual merge.
- Do not edit generated files to hide a wrong generator configuration. Fix the configuration and regenerate.
