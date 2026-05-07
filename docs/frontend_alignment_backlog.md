# 前端对齐 Backlog

更新日期：2026-05-07
适用对象：等算法层稳定后做一轮前端集中对齐。**这个文档持续追加，不要单条修改。** 每条改动都标注：

- **来源**：触发这条改动的算法 PR / Issue / 讨论
- **后端契约**：响应里需要前端读的字段
- **前端动作**：UI / 文案 / 视觉的具体变化
- **状态**：`pending` / `prioritized` / `ready` / `in_progress` / `done`

---

> Note：当前 main 还没合并 #3-#6 几个算法 PR，所以 #1, #5, #6, #9, #10 在这个分支看起来是 "待合并依赖"。完整的条目状态以最近合并的算法 PR 为准。

## 1. PREMIUM 标签（combo release）— 见 PR #3

## 2. WAIT / MAYBE / GO / STRONG GO / PREMIUM 五档语义

## 3. confidence 永远不展示为 UI 元素

## 4. day overview 用用户语言，过滤算法术语

## 5. Safety / Comfort / Fish 三分独立展示 — 见 PR #5

## 6. 地图 pin 各自独立打分 — 见 PR #6

## 7. 相对天框架（"今天比近 30 天平均强 / 弱"）

## 8. 数据警告只在异常时小图标

## 9. 浪源解释（passing swell vs wind chop）— 见 PR #4

## 10. dominant water type 文案要尊重 region — 见 PR #4

## 11. 用户反馈采集：4 档 outcome + 可选文本

- **来源**：用户 2026-05-07 P1 #6 讨论；PR `cursor/feedback-collection-117c`（已实现 Phase A 后端）
- **后端契约**：`POST /api/feedback`
  - 请求体见 `docs/feedback_schema_v1_2026-05-07.md`
  - 必须字段：`trip_date / trip_window / lat / lon / predicted.score / outcome`
  - 强烈建议传完整 `predicted` 块（fish/comfort/safety/combo/dominant/key_reason_tags 全部原样回传给后端落盘，未来算法升级不影响历史数据）
  - 响应：201 + 存储后的 record；或 400 + `{error, message}`
- **前端动作**：
  - 在 day-overview 的窗口卡片末尾加小型 4 档 picker：
    ```
    How did it go?
    [😐 skunked] [🐟 ok] [🐟🐟 decent] [🎯 great]
    ```
  - 点击后 POST 到 `/api/feedback`，请求体由前端从 forecast response 拼装：
    ```json
    {
      "trip_date": "2026-05-08",
      "trip_window": "morning",
      "lat": -42.8915,
      "lon": 147.332,
      "region": "sheltered_estuary",
      "predicted": {
        "score": 65,
        "fish_outlook_score": 67,
        "comfort_score": 70,
        "safety_flag": "low",
        "safety_factors": [...],
        "comfort_factors": [...],
        "dominant_water_type": "bay_estuary_edge",
        "key_reason_tags": ["sunrise_window", "rising_tide_window"],
        "combo_release": "rare_alignment_window"
      },
      "outcome": "decent",
      "outcome_notes": "可选自由文本，<=120 字"
    }
    ```
  - 可选 `outcome_notes` 文本框（单行，limit 120 字）放在 outcome 选完之后展开
  - **Fire-and-forget**：UI 不需要等待结果。201 = ✓ 角标 / 400 = 用 toast 友好提示
  - 不展示 outcome 历史给用户（这是隐私敏感数据，且 Phase A 不做查询接口）
  - 同一个 trip_date + trip_window + lat/lon 用户可以多次提交（后端不去重，分析时按需处理）
- **后续 Phase B / C**：
  - Phase B：`scripts/analyze_feedback.py` 离线跑分析
  - Phase C：数据 ≥ 50 条 + 3 地区 + 2 周后，校准 `_calibrate_public_preview_score`
  - 这两个 phase 不是 Phase A 的范围
- **状态**：ready（后端已实现，等前端加 picker）

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
