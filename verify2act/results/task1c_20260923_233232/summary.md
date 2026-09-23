# Verify2Act session task1c_20260923_233232

- backend: `local`  exec_mode: full_plan  max_replans: 2  theta_c/theta_p: 0.5/0.6  dry_run: False

| metric | value |
|---|---|
| episodes | 10 |
| real_success_rate | 0.857 |
| real_success_overall | 0.6 |
| verified_rate | 0.7 |
| accepted_without_reflect | 0.3 |
| critic_precision | 0.857 |
| false_accepts | 1 |
| avg_timesteps | 2 |
| avg_replans | 1.4 |
| avg_vlm_calls | 3.1 |
| total_requeries | 36 |
| total_temporal_rejections | 36 |
| total_goal_rejections | 9 |
| mean_episode_time_s | 66.45 |

| task | episodes | verified | real success / labeled |
|---|---|---|---|
| task1c | 10 | 7 | 6/10 |

| # | task | steps | replans | vlm calls | verified | executed | real | time (s) |
|---|---|---|---|---|---|---|---|---|
| 1 | task1c | 1 | 2 | 3 | False | False | False | 8.93 |
| 2 | task1c | 2 | 2 | 4 | True | True | True | 70.93 |
| 3 | task1c | 2 | 0 | 1 | True | True | True | 75.21 |
| 4 | task1c | 2 | 2 | 4 | True | True | False | 70.99 |
| 5 | task1c | 2 | 0 | 1 | True | True | True | 76.14 |
| 6 | task1c | 3 | 2 | 5 | True | True | True | 107.22 |
| 7 | task1c | 2 | 0 | 1 | True | True | True | 69.86 |
| 8 | task1c | 1 | 2 | 3 | False | False | False | 3.48 |
| 9 | task1c | 4 | 2 | 6 | True | True | True | 176.7 |
| 10 | task1c | 1 | 2 | 3 | False | False | False | 5.02 |
