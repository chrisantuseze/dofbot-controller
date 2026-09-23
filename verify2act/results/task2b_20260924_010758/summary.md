# Verify2Act session task2b_20260924_010758

- backend: `local`  exec_mode: full_plan  max_replans: 2  theta_c/theta_p: 0.5/0.6  dry_run: False

| metric | value |
|---|---|
| episodes | 4 |
| real_success_rate | 1.0 |
| real_success_overall | 1.0 |
| verified_rate | 1.0 |
| accepted_without_reflect | 0.5 |
| critic_precision | 1.0 |
| false_accepts | 0 |
| avg_timesteps | 2.25 |
| avg_replans | 1 |
| avg_vlm_calls | 2.75 |
| total_requeries | 9 |
| total_temporal_rejections | 9 |
| total_goal_rejections | 3 |
| mean_episode_time_s | 55.17 |

| task | episodes | verified | real success / labeled |
|---|---|---|---|
| task2b | 4 | 4 | 4/4 |

| # | task | steps | replans | vlm calls | verified | executed | real | time (s) |
|---|---|---|---|---|---|---|---|---|
| 1 | task2b | 2 | 2 | 4 | True | True | True | 51.72 |
| 2 | task2b | 2 | 0 | 1 | True | True | True | 40.97 |
| 3 | task2b | 2 | 0 | 1 | True | True | True | 41.36 |
| 4 | task2b | 3 | 2 | 5 | True | True | True | 86.65 |
