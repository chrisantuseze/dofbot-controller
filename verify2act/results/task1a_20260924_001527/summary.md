# Verify2Act session task1a_20260924_001527

- backend: `local`  exec_mode: full_plan  max_replans: 2  theta_c/theta_p: 0.5/0.6  dry_run: False

| metric | value |
|---|---|
| episodes | 10 |
| real_success_rate | 0.833 |
| real_success_overall | 0.5 |
| verified_rate | 0.6 |
| accepted_without_reflect | 0.6 |
| critic_precision | 0.833 |
| false_accepts | 1 |
| avg_timesteps | 1.6 |
| avg_replans | 0.8 |
| avg_vlm_calls | 1.9 |
| total_requeries | 0 |
| total_temporal_rejections | 0 |
| total_goal_rejections | 12 |
| mean_episode_time_s | 47.31 |

| task | episodes | verified | real success / labeled |
|---|---|---|---|
| task1a | 10 | 6 | 5/10 |

| # | task | steps | replans | vlm calls | verified | executed | real | time (s) |
|---|---|---|---|---|---|---|---|---|
| 1 | task1a | 2 | 0 | 1 | True | True | True | 65.78 |
| 2 | task1a | 1 | 2 | 3 | False | False | False | 5.13 |
| 3 | task1a | 2 | 0 | 1 | True | True | True | 63.82 |
| 4 | task1a | 3 | 0 | 2 | True | True | True | 109.16 |
| 5 | task1a | 2 | 0 | 1 | True | True | True | 66.92 |
| 6 | task1a | 1 | 2 | 3 | False | False | False | 9.11 |
| 7 | task1a | 1 | 2 | 3 | False | False | False | 8.87 |
| 8 | task1a | 1 | 0 | 1 | True | True | False | 67.25 |
| 9 | task1a | 1 | 2 | 3 | False | False | False | 6.19 |
| 10 | task1a | 2 | 0 | 1 | True | True | True | 70.84 |
