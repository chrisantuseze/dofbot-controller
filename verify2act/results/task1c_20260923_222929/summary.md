# Verify2Act session task1c_20260923_222929

- backend: `local`  exec_mode: full_plan  max_replans: 2  theta_c/theta_p: 0.5/0.6  dry_run: False

| metric | value |
|---|---|
| episodes | 10 |
| real_success_rate | 0.75 |
| real_success_overall | 0.3 |
| verified_rate | 0.4 |
| accepted_without_reflect | 0.2 |
| critic_precision | 0.75 |
| false_accepts | 1 |
| avg_timesteps | 1.4 |
| avg_replans | 1.6 |
| avg_vlm_calls | 2.8 |
| total_requeries | 27 |
| total_temporal_rejections | 27 |
| total_goal_rejections | 15 |
| mean_episode_time_s | 32.38 |

| task | episodes | verified | real success / labeled |
|---|---|---|---|
| task1c | 10 | 4 | 3/10 |

| # | task | steps | replans | vlm calls | verified | executed | real | time (s) |
|---|---|---|---|---|---|---|---|---|
| 1 | task1c | 2 | 0 | 1 | True | True | False | 74.69 |
| 2 | task1c | 1 | 2 | 3 | False | False | False | 4.34 |
| 3 | task1c | 2 | 0 | 1 | True | True | True | 69.85 |
| 4 | task1c | 2 | 2 | 4 | True | True | True | 75.12 |
| 5 | task1c | 2 | 2 | 4 | True | True | True | 71.24 |
| 6 | task1c | 1 | 2 | 3 | False | False | False | 5.58 |
| 7 | task1c | 1 | 2 | 3 | False | False | False | 5.74 |
| 8 | task1c | 1 | 2 | 3 | False | False | False | 5.56 |
| 9 | task1c | 1 | 2 | 3 | False | False | False | 5.67 |
| 10 | task1c | 1 | 2 | 3 | False | False | False | 5.97 |
