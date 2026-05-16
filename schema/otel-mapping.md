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
| `tetrad.figure_ground`           | string  | figure / ground / both / unclear | derived  | Read-only (`readOnly: true`). Computed by consumer; producers MUST NOT set. |
| `tetrad.tier`                    | string  | heuristic / llm / annotation     | yes      | Now in JSON Schema `required[]`. |
| `tetrad.confidence`              | double  | [0, 1]                           | conditional | required when `tetrad.tier=llm` (enforced via JSON Schema `allOf`+`if`/`then`). |
| `engelbart.level`                | string  | a / b / c                        | no       | Bootstrap Institute ABC framing (1990s) — NOT in the 1962 SRI report. |
| `engelbart.role_split.human`     | double  | [0, 1]                           | no       | |
| `engelbart.role_split.ai`        | double  | [0, 1]                           | no       | |

## `tetrad.figure_ground` derivation (consumer-side)

Producers MUST NOT emit this attribute. Consumers (dashboards / SDK
helpers) derive it from the four scores using the rule below (defaults in
parentheses; tunable per consumer):

```
high = 0.6
figure_score = (tetrad.enhance + tetrad.retrieve) / 2
ground_score = (tetrad.obsolesce + tetrad.reverse) / 2

if figure_score >= high and ground_score >= high: figure_ground = "both"
elif figure_score >= high:                        figure_ground = "figure"
elif ground_score >= high:                        figure_ground = "ground"
else:                                             figure_ground = "unclear"
```

Cross-language consumers should converge on this rule for dashboard parity. The Python helper is `tetrad_lens.figure_ground_of(...)`.

## Dual-emit with OpenInference / OTel GenAI (planned, v0.1.x)

The environment variable `OTEL_SEMCONV_STABILITY_OPT_IN=tetrad/dup`
(following the openinference / OTel GenAI convention for opt-in dual-emit)
is **reserved** for emitting both the `tetrad.*` attributes and the
equivalent openinference / OTel GenAI attributes when a mapping exists.

**Status (v0.1.0)**: the SDK reads this env var but the dual-emit code path
is not yet wired. Setting the variable has no effect today. Implementation
is queued in v0.1.x — track in the repo issue list.

## Why not propose to the SIG immediately

Adding a vendor namespace to the official OTel GenAI semantic conventions requires (per OTEP process) at least two language implementations, technical-committee review, and consensus among observability vendors. `tetrad-lens` v0.1 ships with Python only; OTEP submission is queued for v0.3+. Until then, `tetrad.*` is a **custom convention** and consumers should treat it as such.
