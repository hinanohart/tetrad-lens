# OpenTelemetry attribute mapping

`tetrad-lens` writes span attributes under two namespaces:

| Namespace      | Owner         | Reserved by OTel SIG? |
|----------------|---------------|------------------------|
| `tetrad.*`     | tetrad-lens   | No (custom; v0.3+ may submit OTEP for Federated Conventions) |
| `engelbart.*`  | tetrad-lens   | No (custom)            |

`otel.*` is reserved by the OpenTelemetry SIG and **MUST NOT** be used by `tetrad-lens`.

## Attribute table

| Attribute                        | Type    | Range / Enum                     | Required | Notes |
|----------------------------------|---------|----------------------------------|----------|-------|
| `tetrad.schema_version`          | string  | semver `^\d+\.\d+\.\d+$`         | yes      | Producers MUST set. |
| `tetrad.enhance`                 | double  | [0, 1]                           | yes      | |
| `tetrad.enhance.rationale`       | string  | <= 2000 chars                    | conditional | required when score >= 0.5 |
| `tetrad.obsolesce`               | double  | [0, 1]                           | yes      | |
| `tetrad.obsolesce.rationale`     | string  | <= 2000 chars                    | conditional | required when score >= 0.5 |
| `tetrad.retrieve`                | double  | [0, 1]                           | yes      | |
| `tetrad.retrieve.rationale`      | string  | <= 2000 chars                    | conditional | required when score >= 0.5 |
| `tetrad.reverse`                 | double  | [0, 1]                           | yes      | |
| `tetrad.reverse.rationale`       | string  | <= 2000 chars                    | conditional | required when score >= 0.5 |
| `tetrad.figure_ground`           | string  | figure / ground / both / unclear | derived  | Read-only. Computed by consumer; producers MUST NOT set. |
| `tetrad.tier`                    | string  | heuristic / llm / annotation     | yes      | |
| `tetrad.confidence`              | double  | [0, 1]                           | conditional | required for tier=llm |
| `engelbart.level`                | string  | a / b / c                        | no       | Bootstrap Institute ABC framing (1990s) — NOT in the 1962 SRI report. |
| `engelbart.role_split.human`     | double  | [0, 1]                           | no       | |
| `engelbart.role_split.ai`        | double  | [0, 1]                           | no       | |

## Dual-emit with OpenInference / OTel GenAI

Set `OTEL_SEMCONV_STABILITY_OPT_IN=tetrad/dup` (matches the openinference / OTel GenAI convention for opt-in dual-emit) to have the SDK emit both the `tetrad.*` attributes and the equivalent openinference / OTel GenAI attributes when a mapping exists.

The default is **dual-emit ON** — turn it off with `OTEL_SEMCONV_STABILITY_OPT_IN=tetrad` (no `/dup` suffix) if you want only the `tetrad.*` namespace.

## Why not propose to the SIG immediately

Adding a vendor namespace to the official OTel GenAI semantic conventions requires (per OTEP process) at least two language implementations, technical-committee review, and consensus among observability vendors. `tetrad-lens` v0.1 ships with Python only; OTEP submission is queued for v0.3+. Until then, `tetrad.*` is a **custom convention** and consumers should treat it as such.
