# 前端对齐 Backlog

更新日期：2026-05-07
适用对象：等算法层稳定后做一轮前端集中对齐。**这个文档持续追加，不要单条修改。** 每条改动都标注：

- **来源**：触发这条改动的算法 PR / Issue / 讨论
- **后端契约**：响应里需要前端读的字段
- **前端动作**：UI / 文案 / 视觉的具体变化
- **状态**：`pending` / `prioritized` / `ready` / `in_progress` / `done`

---

## 1. PREMIUM 标签（combo release）

- **来源**：PR `cursor/combo-release-117c`（confidence-gated combo release）
- **后端契约**：
  - 顶层 `response.combo_release`：
    ```json
    {
      "applied": true,
      "windows_boosted": 1,
      "hours_boosted": 5,
      "best_tag": "rare_alignment_window"
    }
    ```
    `best_tag` 还可能为 `"strong_alignment_window"` 或 `null`（视窗口对齐结果而定）。
  - 每个被 boost 的窗口，`overall_recommendation.combo_release` 含 `tag / boost / original_score / boosted_score`
  - `reason_tags` 里会出现 `rare_alignment_window` 或 `strong_alignment_window`
- **前端动作**：
  - 在 hero 区分数旁边，当 `combo_release.applied && combo_release.best_tag === "rare_alignment_window"` 时显示 ★ PREMIUM 徽标 + 不同色块
  - `strong_alignment_window` 用一个稍弱的视觉（例如 ✦ STRONG GO）
  - 不要展示 boost 数值或 `original_score`——保持「分数本身就够」的克制
  - 每日窗口卡片同样按 `combo_release` 字段单独标记
- **状态**：ready

## 2. WAIT / MAYBE / GO / STRONG GO / PREMIUM 五档语义

- **来源**：用户 2026-05-07 讨论；和 combo release 配套
- **后端契约**：当前有 `overall_recommendation.label`（"Promising nearby options" / "Usable nearby options" / "Patchy nearby options"），三档语义在 planner 的 `recommendation.label` 也有（"go" / "maybe" / "skip"），但分档和分数挂得很碎；另有 `score`。
- **前端动作**：
  - 把「分数 + label」重新映射成五档，用户层只看到这一档：
    - `< 50`：WAIT — "今天不建议专程"
    - `50-65`：MAYBE — "路过试 30 分钟，别带太多装备"
    - `65-80`：GO — "值得安排短窗口"
    - `80-90`：STRONG GO — "强窗口"
    - `≥ 90`：★ PREMIUM — "罕见对齐"（与 combo release 联动）
  - 把档位作为**主视觉**，分数次之
- **状态**：pending（设计已敲定，等 UI 改）

## 3. confidence 永远不展示为 UI 元素

- **来源**：用户 2026-05-07 反复确认 — confidence 只做隐藏分
- **后端契约**：`response.confidence`（含 score / label / factors / limitations / caps_applied）继续存在，但**不要直接渲染** `label === "low"` / `label === "medium"`
- **前端动作**：
  - 删除任何 `Confidence: low` / `Confidence: medium` chip
  - 不要在分数下面长期挂 `(model tide)` 这种后缀
  - 数据警告（如 "tide is model-estimated"）只在用户主动展开 "Why this score?" 时露出
  - 极端情况（`station_distance_km > 100` / 没有 marine 数据）允许一个不刺眼的小图标，点开才有解释
- **状态**：pending

## 4. day overview 用用户语言，过滤算法术语

- **来源**：用户 2026-05-07 讨论
- **后端契约**：`score_breakdown.drivers[]` 含 `id / label / type`；`reason_tags` / `score_guard_tags` / `score_mode_tags`；`safety_factors` / `comfort_factors`
- **前端动作**：
  - 建一张 tag → 中文/英文人话映射表，所有渲染走它，禁止裸 tag
  - 例：
    - `dead_water_2h` → "水几乎不动，鱼吃口会很零碎"
    - `timing_capped_by_dead_water` → "日出窗口被弱潮水抵消了"
    - `estuary_system_trend_cap` → "河口系统刚被天气打乱，需要再稳一两天"
    - `passing_swell_high` → "外海有涌路过，但内角应该还稳"（**新增 from 2026-05-07 wave fix**）
    - `rare_alignment_window` / `strong_alignment_window` → 不显示 tag 字面，由 PREMIUM 视觉传达
    - 详见条目 5 的 safety / comfort tag 映射
  - 内部术语黑名单（不能让 LLM 解释里漏出去）：`raw_time_signal` / `local_adjusted` / `score_breakdown` / `adjustment_delta` / `driver` / `reason_tag` / `rule_tags` / `combo_release` / `safety_factors` / `comfort_factors` 等
- **状态**：pending（映射表是大头）

## 5. Safety / Comfort / Fish 三分独立展示

- **来源**：用户 2026-05-07 P0 讨论；PR `cursor/safety-comfort-split-117c`（已实现）
- **后端契约**：`overall_recommendation` 现在并行输出：
  - `fish_outlook_score` (int 0-100)：纯鱼情，等于 `0.55 × activity + 0.45 × presence`，不含 trip/safety
  - `comfort_score` (int 0-100)：体感舒适，从 78 base 减去（冷/湿/风/浪/阵风/温度）
  - `comfort_factors` (string[])：拉低 comfort 的 tag，例如 `cold_air / steady_rain / strong_gusts / rough_seas / biting_wind_chill`
  - `safety_flag`：枚举 `low / moderate / elevated / hazardous`
  - `safety_factors` (string[])：触发 flag 的 tag，例如 `moderate_wave_activity / exposed_with_wave / strong_gusts / cold_wet_windy / rapid_wave_change`
  - 同字段也透传到 `hero` 顶层和 `daily_forecast[*].windows[*]` 卡片
  - `hourly_activity[*]` 也带 `fish_outlook_score / comfort_score / safety_flag`
  - 既有 `score / activity_score / presence_score / trip_quality_score` 全部保留不变（向后兼容）
- **前端动作**：
  - hero 区可以三 chip 并列：`Fish 75 · Comfort 65 · Safety low`
  - 主分仍展示 `score`（最终「今日总判断」），上面三个并列做 sub-chip
  - 大风大浪日：`Fish 75 · Comfort 28 · Safety hazardous` —— 用户立刻看到危险信号，鱼情不被掩盖
  - safety_flag 视觉建议：`low` 隐藏 chip / `moderate` 灰 / `elevated` 黄 / `hazardous` 红 + 警告图标
  - `safety_factors / comfort_factors` 用户语言映射（同条目 4 映射表）：
    - `rough_seas_above_2m5` → "海况 2.5m+ 大涌"
    - `notable_wave_activity` → "浪有点大"
    - `exposed_with_wave` → "暴露海岸 + 浪"
    - `severe_gusts` → "强阵风"
    - `cold_wet_windy` → "冷+湿+风同时"
    - `rapid_wave_change` → "海况快速变化"
    - `biting_wind_chill` → "刺骨风寒"
    - `cold_air` → "冷空气"
    - `steady_rain` → "持续降雨"
    - `notable_seas` → "浪较大"
- **状态**：ready（算法已实现，等前端对齐）

## 6. 地图 pin 各自独立打分

- **来源**：用户 2026-05-07 P1 讨论；PR `cursor/per-pin-scoring-117c`（已实现）
- **后端契约**：每个 `structure_facilities[*]` 现在带一个 `pin_forecast` 子对象：
  ```json
  {
    "pin_forecast": {
      "available": true,
      "distance_km_from_search": 3.31,
      "score": 60,
      "label": "Usable nearby options",
      "fish_outlook_score": 62,
      "comfort_score": 70,
      "comfort_factors": [],
      "safety_flag": "low",
      "safety_factors": [],
      "dominant_water_type": "bay_estuary_edge",
      "support_mode": "near_water",
      "search_confidence_score": 0.48,
      "recent_social_pulse": { "见条目 12" },
      "reason_summary": "Pin-specific geometry, shared weather/tide with search center."
    }
  }
  ```
  - `available: false` 时含 `reason` 字段（`inland_or_non_tidal / too_far_from_supported_water / no_environment / preview_error`）
  - 共享搜索中心的 weather/marine/tide environment（不重复打 Open-Meteo），但**几何信号每个 pin 独立**——这是核心价值：朝外 pin 会被识别为 beach 即使搜索中心是 sheltered_estuary
- **前端动作**：
  - 地图每个 pin 显示自己的分数和 `dominant_water_type`
  - `safety_flag` 高（elevated/hazardous）的 pin 用警告色或不渲染（避免引导用户去危险点）
  - `available: false` 的 pin 仍可显示在地图上（位置已知），但分数槽显示 "—" 或 "geometry"
  - `distance_km_from_search > 5km` 用不同视觉（淡色 / 虚线）
  - 选中 pin 时可显示完整的 fish/comfort/safety 三维度（同条目 5）
- **状态**：ready

## 7. 相对天框架（"今天比近 30 天平均强 / 弱"）

- **来源**：用户 2026-05-07 P2 讨论
- **后端契约**：`hourly_activity` 已经有 30 天历史，前端可在客户端算 z-score
- **前端动作**：
  - 日历条上方加一行 "今天比近 30 天平均强 12%" 之类
  - 配合极值标注（"近 30 天最好"）
- **状态**：pending（纯前端）

## 8. 数据警告只在异常时小图标

- **来源**：用户 2026-05-07 关于 confidence 的讨论
- **后端契约**：`tide_verification.status` / `confidence.caps_applied` / `confidence.limitations`
- **前端动作**：
  - 默认 UI 不显示数据来源警告
  - 出现以下任一时，分数右侧加一个不刺眼的小图标（点开有解释）：
    - `tide_verification.status === "live_verified_remote_station"` 且 `station_distance_km > 100`
    - `data_sources.conditions !== "open_meteo"`（fixture / 缓存重放）
    - `caps_applied` 里含 `"Low searched-coordinate geometry confidence"`
- **状态**：pending

## 9. 浪源解释（passing swell vs wind chop）

- **来源**：PR `cursor/wave-and-dominant-fixes-117c`（Southport 修复）
- **后端契约**：
  - `reason_tags` 里区分 `big_wave_beach`（风浪一起）vs `passing_swell_high`（外海涌路过）
  - day overview 的 "Waves + safety" 文案应该利用这个区别
- **前端动作**：
  - 当 `passing_swell_high` 在 tags 里且 `big_wave_beach` 不在：浪文案改成"外海有涌路过，本地风很小，遮蔽角应该还可钓"
  - 当 `big_wave_beach` 在 tags 里：文案保持现状（"大浪 + 风，不建议专程"）
- **状态**：ready

## 10. dominant water type 文案要尊重 region

- **来源**：PR `cursor/wave-and-dominant-fixes-117c`（dominant tiebreaker）
- **后端契约**：`overall_recommendation.dominant_inferred_type` 现在在 region preference 下更稳定
- **前端动作**：
  - 卡片「主推水型」文案直接用 `dominant_inferred_type`，不需要再做兜底
  - 如果以前有「如果是 sheltered region 但 dominant 是 beach 怎么办」的特殊处理可以删掉
- **状态**：ready（清理代码）

## 12. 地图 pin 上的"近期社交活跃度"徽标

- **来源**：用户 2026-05-07 路径 1 讨论；PR `cursor/pin-social-pulse-117c`（已实现）
- **后端契约**：每个 `pin_forecast` 现在含 `recent_social_pulse` 子对象：
  ```json
  {
    "recent_social_pulse": {
      "available": true,
      "level": "medium",
      "report_count": 8,
      "top_species": ["bream", "australian_salmon", "flathead"],
      "nearest_anchor": "sandy_bay",
      "nearest_anchor_family": "derwent",
      "recent_window_days": 30,
      "score_adjustment_allowed": false,
      "source": "context_only"
    }
  }
  ```
  - 30 天滚动窗口（短于 hero 的 45 天，pin 是决策点要更新鲜）
  - 同一搜索内不同 pin 可命中不同 anchor（Sandy Bay 区 pin → `sandy_bay`；Bellerive Pier → `kangaroo_bluff`），这是 per-pin 几何价值的延伸
  - **`score_adjustment_allowed: false` 是硬约束**：社交内容偏报喜不报忧 + 物种 mismatch（淡水 / 船钓深海）严重，不能进算法
  - 大部分 pin 在大部分时间显示 `available: false / level: "none"`——这是**正确的**。crawler 覆盖稀疏，宁可不发声
- **前端动作**：
  - pin marker 加**小型徽标**（不要喧宾夺主，`pin_forecast.score` 才是主信号）：
    - `level: "none"` → 不显示
    - `level: "low"` → 浅灰小点
    - `level: "medium"` → 普通色 chip "近期 N 报"
    - `level: "high"` → 突出色 chip + 微弱光晕
  - 选中 pin 时 tooltip 展开 `top_species`，附 "基于近 30 天社交媒体活跃度，仅供参考，不影响评分"
  - **不要**把 `top_species` 当作"今天能钓到什么"——它是"过去一个月有人发过什么"
  - 物种过滤器（如果做）：让用户按 species 过滤地图 pin
- **设计原则提醒**：
  - 永远不要把 `recent_social_pulse.level` 加到任何分数计算
  - 如果 LLM 文案接入这个数据，必须强制 prepend "according to recent social posts" 这种限定语
- **状态**：ready

---

## 添加新条目的格式

新算法改动产生的前端对齐需求往这个文档追加。模板：

```md
## N. 简短标题

- **来源**：PR / Issue / 讨论日期
- **后端契约**：响应字段 / 数据形状
- **前端动作**：UI / 文案 / 视觉变化
- **状态**：pending / prioritized / ready / in_progress / done
```

每次后端改完一轮（算法 PR 合并），把对应条目状态推进，并在 PR 描述里链接这个文档。前端集中改的时候按 `状态: ready` 过滤优先做。
