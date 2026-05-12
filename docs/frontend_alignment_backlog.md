# 前端对齐 Backlog

更新日期：2026-05-07
适用对象：等算法层稳定后做一轮前端集中对齐。**这个文档持续追加，不要单条修改。** 每条改动都标注：

- **来源**：触发这条改动的算法 PR / Issue / 讨论
- **后端契约**：响应里需要前端读的字段
- **前端动作**：UI / 文案 / 视觉的具体变化
- **状态**：`pending` / `prioritized` / `in_progress` / `done`

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
      "best_tag": "rare_alignment_window"  // 或 "strong_alignment_window" / null
    }
    ```
  - 每个被 boost 的窗口，`overall_recommendation.combo_release` 含 `tag / boost / original_score / boosted_score`
  - `reason_tags` 里会出现 `rare_alignment_window` 或 `strong_alignment_window`
- **前端动作**：
  - 在 hero 区分数旁边，当 `combo_release.applied && combo_release.best_tag === "rare_alignment_window"` 时显示 ★ PREMIUM 徽标 + 不同色块
  - `strong_alignment_window` 用一个稍弱的视觉（例如 ✦ STRONG GO）
  - 不要展示 boost 数值或 original_score——保持"分数本身就够"的克制
  - 每日窗口卡片同样按 `combo_release` 字段单独标记
- **状态**：pending

## 2. WAIT / MAYBE / GO / STRONG GO / PREMIUM 五档语义

- **来源**：用户 2026-05-07 讨论；和 combo release 配套
- **后端契约**：当前仅有 `overall_recommendation.label`（"Promising nearby options" / "Usable nearby options" / "Patchy nearby options"），三档语义在 planner 的 `recommendation.label` 也有（"go" / "maybe" / "skip"），但分档和分数挂得很碎。
- **前端动作**：
  - 把"分数 + label"重新映射成五档，用户层只看到这一档：
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
  - 极端情况（potDistance > 100 km / 没有 marine 数据）允许一个不刺眼的小图标，点开才有解释
- **状态**：pending

## 4. day overview 用用户语言，过滤算法术语

- **来源**：用户 2026-05-07 讨论
- **后端契约**：
  - `score_breakdown.drivers[]`：含 `id` / `label` / `type`
  - `reason_tags` / `score_guard_tags` / `score_mode_tags`
- **前端动作**：
  - 建一张 tag → 中文/英文人话映射表，所有渲染走它，禁止裸 tag
  - 例：
    - `dead_water_2h` → "水几乎不动，鱼吃口会很零碎"
    - `timing_capped_by_dead_water` → "日出窗口被弱潮水抵消了"
    - `estuary_system_trend_cap` → "河口系统刚被天气打乱，需要再稳一两天"
    - `passing_swell_high` → "外海有涌路过，但内角应该还稳"（**新增 from 2026-05-07 wave fix**）
    - `rare_alignment_window` / `strong_alignment_window` → 不显示 tag 字面，由 PREMIUM 视觉传达
  - 内部术语黑名单（不能让 LLM 解释里漏出去）：`raw_time_signal` / `local_adjusted` / `score_breakdown` / `adjustment_delta` / `driver` / `reason_tag` / `rule_tags` / `combo_release` 等
- **状态**：pending（映射表是大头）

## 5. Safety / Comfort / Fish 三分独立展示（待算法拆完）

- **来源**：用户 2026-05-07 P0 讨论
- **后端契约**：**待定** — 算法层尚未拆。计划在 `_derwent_style_score_modes` 出口并行输出：
  - `fish_outlook_score`：activity × presence
  - `comfort_score`：基于 wind_chill_proxy / wave / rain / temperature
  - `safety_flag`：`low / moderate / elevated / hazardous`
- **前端动作**：
  - hero 区不再单一数字，而是三个并列 chip：`Fish 75 · Comfort medium · Safety low`
  - 大风大浪日 PREMIUM fishing + ⚠ exposed conditions 可同时存在
- **状态**：pending（依赖后端先拆）

## 6. 地图 pin 各自独立打分（待算法支持）

- **来源**：用户 2026-05-07 P1 讨论
- **后端契约**：**待定** — 当前所有 `structure_facilities` 共享搜索中心点的 environment + score。计划：每个 pin 跑一次 `build_preview`（共享 weather/marine fetch，仅几何 + region 不同）
- **前端动作**：
  - 地图层每个 pin 显示自己的分数和标签
  - 距离很远（> 5 km）的 pin 用不同视觉提示
- **状态**：pending（依赖后端改动）

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
  - `reason_tags` 里现在区分 `big_wave_beach`（风浪一起）vs `passing_swell_high`（外海涌路过）
  - day overview 的 "Waves + safety" 文案应该利用这个区别
- **前端动作**：
  - 当 `passing_swell_high` 在 tags 里且 `big_wave_beach` 不在：浪相关文案改成"外海有涌路过，本地风很小，遮蔽角应该还可钓"
  - 当 `big_wave_beach` 在 tags 里：文案保持现状（"大浪 + 风，不建议专程"）
- **状态**：pending

## 10. dominant water type 文案要尊重 region

- **来源**：PR `cursor/wave-and-dominant-fixes-117c`（dominant tiebreaker）
- **后端契约**：`overall_recommendation.dominant_inferred_type` 现在在 region preference 下更稳定
- **前端动作**：
  - 卡片"主推水型"文案直接用 `dominant_inferred_type`，不需要再做兜底
  - 如果以前有"如果是 sheltered region 但 dominant 是 beach 怎么办"的特殊处理可以删掉
- **状态**：pending（清理代码）

---

## 添加新条目的格式

新算法改动产生的前端对齐需求往这个文档追加。模板：

```md
## N. 简短标题

- **来源**：PR / Issue / 讨论日期
- **后端契约**：响应字段 / 数据形状
- **前端动作**：UI / 文案 / 视觉变化
- **状态**：pending / prioritized / in_progress / done
```

每次后端改完一轮（算法 PR 合并），把对应条目状态推进，并在 PR 描述里链接这个文档。前端集中改的时候按状态过滤。
