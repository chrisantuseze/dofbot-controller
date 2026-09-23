# Verify2Act session task1d_20260924_004231

- backend: `local`  exec_mode: full_plan  max_replans: 2  theta_c/theta_p: 0.5/0.6  dry_run: False

| metric | value |
|---|---|
| episodes | 3 |
| real_success_rate | 1.0 |
| real_success_overall | 1.0 |
| verified_rate | 1.0 |
| accepted_without_reflect | 0.0 |
| critic_precision | 1.0 |
| false_accepts | 0 |
| avg_timesteps | 2 |
| avg_replans | 2 |
| avg_vlm_calls | 4 |
| total_requeries | 27 |
| total_temporal_rejections | 27 |
| total_goal_rejections | 0 |
| mean_episode_time_s | 103.34 |

| task | episodes | verified | real success / labeled |
|---|---|---|---|
| task1d | 3 | 3 | 3/3 |

| # | task | steps | replans | vlm calls | verified | executed | real | time (s) |
|---|---|---|---|---|---|---|---|---|
| 1 | task1d | 2 | 2 | 4 | True | True | True | 101.78 |
| 2 | task1d | 2 | 2 | 4 | True | True | True | 104.9 |
| 3 | task1d | 2 | 2 | 4 | True | True | True | 103.35 |
