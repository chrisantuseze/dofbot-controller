# Verify2Act session task2a_20260924_010106

- backend: `local`  exec_mode: full_plan  max_replans: 2  theta_c/theta_p: 0.5/0.6  dry_run: False

| metric | value |
|---|---|
| episodes | 4 |
| real_success_rate | 1.0 |
| real_success_overall | 1.0 |
| verified_rate | 1.0 |
| accepted_without_reflect | 1.0 |
| critic_precision | 1.0 |
| false_accepts | 0 |
| avg_timesteps | 2.25 |
| avg_replans | 0 |
| avg_vlm_calls | 1.25 |
| total_requeries | 0 |
| total_temporal_rejections | 0 |
| total_goal_rejections | 0 |
| mean_episode_time_s | 53.98 |

| task | episodes | verified | real success / labeled |
|---|---|---|---|
| task2a | 4 | 4 | 4/4 |

| # | task | steps | replans | vlm calls | verified | executed | real | time (s) |
|---|---|---|---|---|---|---|---|---|
| 1 | task2a | 2 | 0 | 1 | True | True | True | 42.64 |
| 2 | task2a | 2 | 0 | 1 | True | True | True | 41.09 |
| 3 | task2a | 3 | 0 | 2 | True | True | True | 86.47 |
| 4 | task2a | 2 | 0 | 1 | True | True | True | 45.74 |
