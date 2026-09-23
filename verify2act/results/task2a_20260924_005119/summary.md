# Verify2Act session task2a_20260924_005119

- backend: `local`  exec_mode: full_plan  max_replans: 2  theta_c/theta_p: 0.5/0.6  dry_run: False

| metric | value |
|---|---|
| episodes | 4 |
| real_success_rate | 0.0 |
| real_success_overall | 0.0 |
| verified_rate | 0.75 |
| accepted_without_reflect | 0.75 |
| critic_precision | 0.0 |
| false_accepts | 3 |
| avg_timesteps | 1 |
| avg_replans | 0.5 |
| avg_vlm_calls | 1.5 |
| total_requeries | 9 |
| total_temporal_rejections | 9 |
| total_goal_rejections | 0 |
| mean_episode_time_s | 37.26 |

| task | episodes | verified | real success / labeled |
|---|---|---|---|
| task2a | 4 | 3 | 0/4 |

| # | task | steps | replans | vlm calls | verified | executed | real | time (s) |
|---|---|---|---|---|---|---|---|---|
| 1 | task2a | 1 | 2 | 3 | False | False | False | 7.86 |
| 2 | task2a | 1 | 0 | 1 | True | True | False | 47.28 |
| 3 | task2a | 1 | 0 | 1 | True | True | False | 46.88 |
| 4 | task2a | 1 | 0 | 1 | True | True | False | 47.0 |
