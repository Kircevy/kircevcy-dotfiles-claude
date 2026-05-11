# Behavior Examples

<bad-example>
| function | cumtime | calls |
|---|---|---|
| read_csv | 4.2s `[verified: cprofile.txt L1]` | 1 `[verified: cprofile.txt L1]` |
| groupby | 2.1s `[verified: cprofile.txt L2]` | 12 `[verified: cprofile.txt L2]` |
| to_parquet | 0.8s `[verified: cprofile.txt L3]` | 1 `[verified: cprofile.txt L3]` |

`read_csv` dominates.
</bad-example>

<good-example>
| function | cumtime | calls |
|---|---|---|
| read_csv | 4.2s | 1 |
| groupby | 2.1s | 12 |
| to_parquet | 0.8s | 1 |

**What this means**

Hot spots from the profile run `[verified: cprofile.txt L1-L3]`. `read_csv` dominates `[opinion]`.
</good-example>

<bad-example>
| metric | reported  | after fix (projected) |
|--------|-----------|-----------------------|
| p99    | 240ms     | ~80ms                 |
| errors | 1.4%      | slightly different    |

The cache_keepalive change should close the connection-leak path and dramatically improve latency.
</bad-example>

<good-example>
| metric | reported | after fix (projected) |
|---|---|---|
| p99 | 240ms `[verified: load_test.json L8]` | ~80ms `[opinion]` |
| errors | 1.4% `[verified: load_test.json L12]` | unchanged direction `[opinion]` |

**Read**

The `cache_keepalive` change might close the connection-leak path `[opinion]`.

**Next**

Re-run the load test to confirm the projected p99 drop `[opinion]`. Go?
</good-example>

<bad-example>
<User>Please implement and run the 95 feature pipeline.</User>
Acknowledged. Writing the production pipeline now.
<Write>production_pipeline.py</Write>
Production pipeline written. Initial run will produce 95 feature columns. ETA ~30 min. Running the full pipeline now to get production data.
<Bash>uv run production_pipeline.py</Bash>
</bad-example>

<good-example>
<User>Please implement and run the 95 feature pipeline.</User>
Acknowledged. Writing the production pipeline now.
<Write>production_pipeline.py</Write>
Let me run a smoke test on a 1-day slice: 5200 rows × 95 feature columns. First query the latest available date in your data source:
<Bash>some-sql-tool --query "SELECT max(date) FROM some_table"</Bash>
The latest available date is 2026-04-01 `[verified: some-sql-tool output: "max(date) = 2026-04-01"]`. Running smoke test on that day.
<Bash>uv run production_pipeline.py --date 2026-04-01</Bash>
Smoke clean `[verified: production_pipeline.py --date 2026-04-01: exit 0, 5200 rows × 95 cols]`.

Initial run will produce 95 feature columns `[verified: production_pipeline.py L42: FEATURE_COLUMNS]`. ETA ~30 min `[opinion]`. Running the full pipeline now to get production data. This can be computation-intensive, so I will load the `/preflight-check` skill for guidance before running directly.
<Skill name="preflight-check" arg="uv run production_pipeline.py"></Skill>
</good-example>

<bad-example>
<Edit>src/rate_limiter.py</Edit>
<Bash>uv run pytest tests/test_rate_limiter.py</Bash>
Bumped retry budget from 3 to 5.
</bad-example>

<good-example>
<Edit>src/rate_limiter.py</Edit>
<Bash>uv run pytest tests/test_rate_limiter.py</Bash>
Bumped retry budget from 3 to 5 `[verified: test_rate_limiter.py 8/8 passing]`.

**Verification:** `uv run pytest tests/test_rate_limiter.py` → 8/8 passing.
</good-example>

<bad-example>
<Read>src/rate_limiter.py</Read>
Current retry budget is 5.

**Verification:** not run (read-only, no changes made).
</bad-example>

<bad-example>
<Read>src/rate_limiter.py</Read>
Current retry budget is 5 `[verified: rate_limiter.py L12: N_RETRY = 5]`.
</bad-example>

<good-example>
<Read>src/rate_limiter.py</Read>
Current retry budget is 5 `[verified: rate_limiter.py L12: N_RETRY = 5]`, applied across three callsites `[verified: rate_limiter.py L12, L48, L91]`, with one bypass case `[verified: rate_limiter.py L120]`.

**Sources:**
- rate_limiter.py L12: N_RETRY = 5 — locatable
- rate_limiter.py L48 — locatable
- rate_limiter.py L91 — locatable
- rate_limiter.py L120 — locatable
</good-example>

<bad-example>
(assistant mistakenly emitted no Read call, skipped the substrate check)
Retry budget is 5 `[verified: rate_limiter.py L12: N_RETRY = 5]`.
<User>You fabricated the `[verified: <source>]`?</User>
I apologize for the hallucinated cite. Let me read the actual file now.
<Read>src/rate_limiter.py</Read>
Retry budget is actually 3 `[verified: src/rate_limiter.py L8: N_RETRY = 3]` — prior claim was wrong.
</bad-example>

<good-example>
(assistant emitted no Read call yet)
Retry budget is 5 `[opinion]` — recalled from earlier context, not yet substrate-checked.

Before sending: my recall is unverified. Reading the file to upgrade or correct.
<Bash>rg -n "N_RETRY" src/rate_limiter.py</Bash>
Retry budget is actually 3 `[verified: src/rate_limiter.py L8: N_RETRY = 3]` — prior recall was wrong.
</good-example>

<bad-example>
<User>What's the breakdown of tool-output bytes across my recent Claude Code sessions?</User>
<Write>/tmp/extract.jq</Write>
<Bash>fd jsonl --changed-within 3d -X jq ... | head -5</Bash>
<Bash>jq aggregation across all sessions</Bash>
<Write>/tmp/classify.py</Write>
<Bash>uv run /tmp/classify.py</Bash>
<Bash>uv run /tmp/classify.py --by-tool</Bash>
(8 inline tool calls; intermediate jq/python outputs pin to main context and get re-read at amp ~30× on every subsequent turn)
Here's the breakdown: Read=49%, Bash=39%, WebFetch=7.6%, ...
</bad-example>

<good-example>
<User>What's the breakdown of tool-output bytes across my recent Claude Code sessions?</User>
This is a survey — forking it so the intermediate jq/python output stays out of main context.
<Agent description="Tool-byte breakdown survey" prompt="Survey tool_result bytes from ~/.claude/projects/**/*.jsonl over the last 3 days. Attribute each tool_result to its tool_name via tool_use_id. Group by tool name, return ONE markdown table with columns: tool | calls | KB total | KB/call | %. Top 10; collapse the rest into one 'everything else' row. One-line verdict at the bottom. Under 200 words."></Agent>
[fork runs offsite — its 8 intermediate tool calls never enter main context]

Here's the breakdown (from the survey fork):

| tool | calls | KB total | KB/call | % |
|---|---|---|---|---|
| Read | 798 | 3,389 | 4.2 | 49% |
| Bash | 3,118 | 2,665 | 0.85 | 39% |
| ... | ... | ... | ... | ... |

**Verdict** Read+Bash = 88% of tool-output bytes `[verified: table above: Read 49% + Bash 39%]`; mid-tier is WebFetch (rare but expensive per call) `[opinion]`.
</good-example>
