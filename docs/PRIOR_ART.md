# Prior art and what we took from it

Round-2 research notes. Sources are linked; claims that only came from third-party summaries are marked (unverified).

## Claude Code plugins and marketplaces

- Manifest lives at `.claude-plugin/plugin.json`, catalog at `.claude-plugin/marketplace.json`; the version appears in both, and drift between them leaves users on an old release (third-party guides, unverified: [talent-factory reference](https://talent-factory.github.io/claude-plugins/reference/marketplace-json/), [ed3d maintaining-a-marketplace](https://skills.cat/skills/ed3dai/ed3d-plugins/maintaining-a-marketplace)). Official pages: code.claude.com/docs/en/plugin-marketplaces, /plugins, /plugins-reference.
- Checked locally with `claude plugin validate`, which passes for both the mod and the marketplace. Its only advisory is a missing listing icon (square PNG, 512-2048 px); adding one is optional and left undone.
- Applied/kept: kebab-case name, SemVer, local test via `--plugin-dir`, `claude plugin test` in CI docs, one marketplace entry per mod. TODO when releasing: keep the marketplace entry's version (if added) equal to plugin.json in the same commit.

## Pluggable backends in small Python libraries

- The PyPA guide recommends package metadata entry points for plugin discovery, found with `importlib.metadata.entry_points(group=...)` ([Creating and discovering plugins](https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/), [importlib.metadata](https://docs.python.org/3/library/importlib.metadata.html)). The alternatives are naming conventions and namespace packages.
- Applied: `JEV_JUDGE` accepts `jev`, `fake`, `module:factory` (no packaging needed) or the name of an entry point in group `jev_core.judges`. The `Judge` Protocol is `runtime_checkable`, so a factory result is verified structurally. The error taxonomy (`JudgeUnavailable` transient, `JudgeConfigError` permanent) already follows the usual retry/no-retry split; load failures map to `JudgeConfigError`.

## LLM routers

- RouteLLM: two-model strong/weak router, one cost threshold calibrated to a target share of strong-model calls, selected per request ([lm-sys/RouteLLM](https://github.com/lm-sys/RouteLLM)). Takeaway: expose one tunable threshold and calibrate it against logged decisions (our `judge-log.jsonl`).
- OpenRouter Auto Router: classifies the prompt into a task type, supports `allowed_models`/`excluded_models` with wildcards, falls back to a default set if classification is unavailable so routing never fails the request, and can report the classified task type in response metadata ([docs](https://openrouter.ai/docs/guides/routing/routers/auto-router)). Takeaways we already match: fail open, show why a decision was made (`/jev`). Possible later idea: an allow/exclude list for models.
- Martian: OpenAI-compatible endpoint with candidate list and max cost per million tokens (vendor claims, unverified).
- Claude Code specific: a model switch discards the prompt cache, so downgrades are only worth it when context is small or the cache is cold; the mod already does this.
