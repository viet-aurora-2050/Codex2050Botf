# Master prompt for a GitHub-capable AI agent

Repository: `viet-aurora-2050/Codex2050Botf`

You have authorized GitHub access. Modernize the public games-data layer without breaking the existing frontend.

1. Read `datenbank/`, `docs/games.json`, `docs/index.html`, `.github/workflows/`, and `tests/`.
2. Create branch `upgrade/public-games-data-v3`.
3. Integrate this ZIP semantically; preserve newer compatible repository code.
4. Run `python -m unittest discover -s tests` and `python -m datenbank --dry-run`.
5. Generate valid `docs/games.json`.
6. Preserve frontend fields: name, anbieter, rtp, vola, max, minb, maxb, quelle.
7. Use only legitimate public sources explicitly configured by the owner or published interfaces whose terms permit automated retrieval.
8. Never bypass authentication, access controls, anti-bot protections, rate limits, or private casino APIs.
9. Never claim to predict random slot outcomes or that a game is "due"/"hot".
10. Public recent-win data may only be stored as a source-reported observation with source/timestamp and non-predictive labeling.
11. Never commit secrets. Use bounded timeouts/item limits and least-privilege GitHub permissions.
12. Commit to the branch and open a PR. Do not merge without explicit authorization.

Acceptance: tests pass; dry-run succeeds; existing frontend loads; source outage keeps fallback catalogue; every external record has provenance; PR documents tests and limitations.
