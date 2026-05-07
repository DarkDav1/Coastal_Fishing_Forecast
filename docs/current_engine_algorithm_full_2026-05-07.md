# 当前公共海岸预测引擎完整算法文档

更新日期：2026-05-07  
项目范围：`workspace-cocky/coastal-fishing-forecast`  
适用对象：后续 AI、前端开发、算法调优、产品讨论  
不适用对象：个人德文特引擎、淡水内陆钓点、人工现场观测评分

## 1. 边界和核心原则

这个文档描述的是公共版 generic coastal engine。它只服务海岸、港湾、河口、近岸咸水或受潮汐影响的地点。它不应该混入个人德文特引擎的高置信规则，也不应该把用户现场看到的鸟、饵鱼、水色、炸水等信息当作自动事实。

当前算法的核心原则：

- 自动评分只使用可以自动获取或预先结构化的数据。
- 搜索坐标通常是低置信输入，不能像人工标注热点一样给高确定性结论。
- 分数表达的是“今天这个地点是否值得安排岸钓”，不是保证上鱼。
- 鱼情分、出行体验、舒适度、安全风险要尽量分开理解，不能把“安全”包装成“鱼多”。
- 月相和日照只作为弱到中等信号，不能压过潮汐、水流、风向、天气趋势。
- 社交内容、现场观察、用户经验只能作为解释或 tips，默认不进入自动分数。

## 2. 当前整体流程

用户搜索地点后，当前系统大致按下面顺序运行：

1. 前端把地点名称传给本地 API。
2. API 调用搜索服务，把地点名称转换成经纬度。
3. 系统判断这个坐标是否在支持范围内：是否靠近海水、是否是潮汐走廊、是否是可解释的近岸点。
4. 系统获取或估算天气、海况、潮汐、日照、月相、岸线、水域类型、附近结构。
5. 引擎对不同钓点类型分别打分：beach、rocks、jetty、bay/estuary edge。
6. 引擎生成 activity、presence、trip quality、resident、roaming 等内部指标。
7. 引擎应用公共预览校准、天气冲击惩罚、弱水流保护、局部系统优先级保护。
8. `build_range_forecast` 生成逐小时曲线、早晨/白天/傍晚窗口、每日平均分。
9. `build_frontend_forecast_response` 把后端输出整理成前端可读结构。
10. 前端展示今日判断、全天曲线、日历条、天气可视化、地图钓点和解释文案。

## 3. 主要入口

### 3.1 单点预览

核心函数：

```text
coastal_fishing_forecast.preview.build_preview(lat, lon, environment=None, region=None)
```

作用：

- 根据一个经纬度生成当前地点的基础评分。
- 判断地点是否被支持。
- 推断岸线、水域类型、开阔程度、遮蔽程度。
- 对 beach、rocks、jetty、bay/estuary edge 四类机会分别评分。
- 生成 `overall_recommendation`。

这是整个算法最核心的入口。

### 3.2 全天和多日预测

核心函数：

```text
coastal_fishing_forecast.forecast.build_range_forecast(...)
```

作用：

- 读取每天逐小时的天气、海况、潮汐。
- 每个小时调用一次 `build_preview`。
- 形成 24 小时鱼情曲线。
- 形成早晨、白天、傍晚窗口。
- 形成 30 天历史和未来预报日期条。

当前前端日历条显示的是日均分，不是最高峰。这个改动是为了避免“某个小时高峰把整天看起来抬高”的误导。

### 3.3 前端响应

核心函数：

```text
coastal_fishing_forecast.api.build_frontend_forecast_response(...)
```

作用：

- 把后端算法结果转换成前端结构。
- 生成 summary、scores、timeline、weather visual、map leads、plan card 等字段。
- 计算前端信心等级。
- 整理解释标签和用户可读文案。

### 3.4 搜索入口

核心函数：

```text
coastal_fishing_forecast.search_forecast.build_search_forecast_response(...)
```

作用：

- 先搜索地点，再跑预测。
- 支持 Mapbox 或 Nominatim。
- 当前本地 web server 默认走 `coastal-search-forecast` CLI。

本地 web server 默认参数：

- 地点搜索 provider：`nominatim`
- 默认 region：`sheltered_estuary`
- 窗口：`morning,day,dusk`
- 天气来源：`forecast`
- 潮汐来源：`openmeteo_model`
- 结构来源：`auto`
- 结构搜索半径：`2000m`
- API 缓存：5 分钟，最多 40 条

## 4. 数据来源

### 4.1 地点搜索

支持：

- Nominatim
- Mapbox

搜索候选点会根据 coastal relevance 排序。算法会优先选择更像海岸、港湾、海湾、码头、海滩、河口的候选。

大致逻辑：

- coastal 类型提示加分。
- 行政边界、纯区域边界减分。
- 有合理 bbox 的候选加分。
- provider 给出的 confidence 会参与排序。

### 4.2 天气

主要使用 Open-Meteo forecast/archive。

天气 hourly 字段：

- air temperature
- surface pressure
- wind speed at 10m
- wind direction at 10m
- wind gusts at 10m
- precipitation
- rain
- cloud cover

时间区：

- `Australia/Hobart`

风速单位：

- knots

### 4.3 海况

主要使用 Open-Meteo marine。

marine hourly 字段：

- wave height
- wave period
- swell wave height
- swell wave direction
- sea surface temperature
- sea level height msl

marine 请求使用 `cell_selection=sea`，尽量取海上格点。

### 4.4 潮汐

潮汐来源按优先级可来自：

- 用户或外部传入的 tide events
- TidesAtlas
- Open-Meteo marine sea level height model
- 粗略天文估算

当前默认 web flow 用的是 `openmeteo_model`，即从 sea level height 曲线推断高低潮。

### 4.5 岸线和水域

使用：

- `global_land_mask`
- 周边多方向采样
- 周边多距离采样

算法用这些采样推断：

- 是否接近海水
- 距离最近水体多远
- 岸线复杂度
- 是否像开放海岸
- 是否像 sheltered bay 或 estuary edge
- 开阔水面方向
- 岸线朝向和风向关系

### 4.6 结构和地图钓点

结构来源：

- OpenStreetMap Overpass
- Tasmania LIST MAST boat ramps
- WildFisheries sea spots
- 内置或后续人工数据

结构类型包括：

- public jetty
- fishing platform
- official fishing spot
- rocky shoreline
- beach access
- boat ramp

注意：boat ramp 可以显示在地图上，但不一定作为“推荐岸钓点”。

### 4.7 社交信号

当前 `social_pulse` 只作为 context。默认：

```text
score_adjustment_allowed = False
```

也就是说，社交内容不会自动改分。它最多用于解释或人工审核。这样做是为了避免把不可验证的历史内容当作实时鱼情。

## 5. 地点支持判断

当前引擎不是任何坐标都给分。它先判断地点是否属于可解释的 coastal/tidal 场景。

关键距离：

- 直接近水范围：5 km
- 扩展潮汐预览范围：8 km
- 搜索采样距离：0.5、1.5、3、5、8、12、20 km
- 分析环：3、8、15 km
- 方位采样：每 30 度一次

支持模式：

- `on_water`：坐标在水体上或非常靠近水体。
- `near_water`：坐标在近岸范围内。
- `tidal_corridor`：离水稍远，但像潮汐河口或海湾走廊。
- `unsupported`：不属于当前公共海岸引擎支持范围。
- `invalid`：坐标或输入无效。

扩展支持只用于可信的潮汐候选点。普通内陆点不会因为离海 8 km 内就被强行评分。

## 6. 岸线和水域类型推断

引擎会计算一组几何信号：

- `inner_water_fraction`
- `mid_water_fraction`
- `outer_water_fraction`
- `coastline_complexity`
- `open_water_bearing_deg`
- `coastal_edge_signal`
- `exposure`
- `shelter`
- `accessibility`
- `search_confidence_score`

其中：

- `exposure` 越高，越像开放海岸。
- `shelter` 越高，越像内湾、港湾、河口边。
- `coastline_complexity` 越高，说明岸线越复杂，可能有边界、转角、结构、水流集中点。
- `open_water_bearing_deg` 用于判断开阔水面方向，也用于风向和岸线关系。
- `search_confidence_score` 反映这个搜索点是否适合被自动解释。

四类水域机会的初始推断：

```text
beach = 0.50 * exposure
      + 0.30 * coastal_edge_signal
      + 0.20 * accessibility

rocks = 0.40 * exposure
      + 0.35 * coastline_complexity
      + 0.25 * accessibility

jetty = 0.35 * coastal_edge_signal
      + 0.30 * coastline_complexity
      + 0.20 * shelter
      + 0.15 * accessibility

bay_estuary_edge = 0.45 * shelter
                 + 0.35 * coastline_complexity
                 + 0.20 * accessibility
```

这些只是自动推断，不等于确认现场真的有某个结构。前端文案不能把未确认的结构说成真实结构。

## 7. Region presets

当前有这些 region preset：

- `generic_coastal`
- `open_coast`
- `sheltered_estuary`
- `surf_coast`
- `harbour_access`
- `bay_coast`

region 会调整以下偏置：

- beach
- rocks
- jetty
- bay/estuary
- tide
- shelter
- exposure

默认 web flow 目前更偏 `sheltered_estuary`。这适合很多塔州港湾/河口搜索，但也意味着开放海岸需要依赖几何判断和海况数据来拉开差异。

## 8. EnvironmentInputs

`EnvironmentInputs` 是环境输入的统一结构。它可以包含：

天气：

- air temperature
- wind speed
- wind direction
- wind gust
- recent max gust
- pressure
- pressure delta 3h/6h/24h/48h/72h
- temperature delta 24h/48h/72h
- peak temperature drop over 72h
- wind direction shift
- precipitation/rain
- rainfall 12h/24h/48h/72h
- cloud cover

海况：

- swell height
- swell direction
- wave height
- wave direction
- wave height delta
- sea surface temperature

潮汐：

- tide phase
- tide stage
- tide range
- current tide height
- tide height change next 2h/3h
- tide height change previous 2h
- tide movement rate
- high tide time
- low tide time

光照和月相：

- sunrise
- sunset
- twilight-like time windows
- moon phase
- moon phase name
- moon illumination
- solunar-like major/minor flags if available

其他：

- time window
- hour of day
- rule family

不是每个字段每次都有。缺字段时，引擎会降级估算，并降低 confidence。

## 9. 潮汐模块

当前潮汐模块输出：

- tide phase
- tide stage
- hours to high
- hours from high
- hours to low
- hours from low
- tide range
- current height
- next 2h height change
- next 3h height change
- previous 2h height change
- movement rate

当前 tide stage 大致覆盖：

- rising
- falling
- high
- low
- slack-like state
- approaching high
- approaching low

细分逻辑还没有完全产品化成用户给出的八段：

- early rising
- mid rising
- late rising
- high slack
- early falling
- mid falling
- late falling
- low slack

但当前内部已经有足够的 phase、hours、height change，可以继续往这个方向增强。

当前潮汐打分倾向：

- rising 或 flood 对大部分岸钓机会加分。
- falling 对 bay/estuary edge、draining flat、河口边会更有意义。
- high/low slack 会被扣分，因为水不动。
- 小潮差、弱 2h/3h 高度变化、弱 movement rate 会明显拉低鱼情。
- 大潮差或强局部流动会加分。

典型规则：

- flood approaching high：加分较强。
- early flood：加分。
- ebb approaching low：轻到中等加分。
- slack：扣分。
- dead water next 2h：明显扣分。
- weak movement 3h：明显扣分。
- strong local tide movement：加分。

## 10. 天气趋势和天气冲击

天气模块不只看当天某一小时，也看过去几天趋势。当前 lookback：

```text
WEATHER_TREND_LOOKBACK_DAYS = 3
```

天气趋势关注：

- 24h/48h/72h 气压变化
- 24h/48h/72h 温度变化
- 72h 最大降温
- 24h/72h 阵风
- 12h/24h/48h/72h 降雨
- 风向突变
- 浪高变化

天气冲击会形成 `weather_shock`。典型触发：

- 24h 气压变化达到约 8 hPa。
- 多天气压变化达到约 10-12 hPa。
- 6h 气压快速变化达到约 4 hPa。
- 24h 明显降温。
- 72h 峰值降温达到约 4.5、6、8 度。
- 风向大幅转变，约 90 度或以上。
- 24h 阵风达到约 45 或 65 kph。
- 24h 降雨达到约 30 mm。
- 72h 降雨达到约 45 mm。
- 浪高短期变化达到约 0.6 m。

天气冲击惩罚大致分层：

- shock >= 1.5：约 -8
- shock >= 2.5：约 -14
- shock >= 4：约 -22
- shock >= 5.5：约 -30

恢复逻辑：

如果天气正在稳定，惩罚会逐步恢复，而不是一直压死：

- 温度开始回稳。
- 气压变化变小。
- 阵风下降。
- 降雨停止或明显变少。
- 浪高回落。

恢复越明显，weather shock 乘数越低。

## 11. 天气舒适和鱼情天气规则

通用天气规则会对基础鱼情产生加减分：

有利：

- 轻到中等风。
- 稳定气压。
- 轻微上升或下降的气压。
- 30-80% 云量。
- 小雨边缘。
- 0.3-1.0 m 左右的可钓浪况。
- 15-22 度左右 SST。

不利：

- 强风。
- 大阵风。
- 大雨。
- 24h/48h 明显降雨。
- 过冷水温。
- 大浪。
- 高日照中午弱水流。
- 天气趋势被打破。

这里的“舒适”不是安全分，也不是鱼情分。它更多反映出行体验、风雨冷暖和水面可操作性。

## 12. 风向和岸线关系

风不只看大小，还看它和岸线的关系。

算法使用 `open_water_bearing_deg` 推断开阔水面方向，再把风向分为：

- onshore：风把水和表层食物往岸边推。
- offshore：风把表层水和食物推离岸边。
- alongshore：风沿岸线吹。
- uncertain：几何不够确定。

当前规则倾向：

- 温和 onshore：加分，但风不能太大。
- 温和 alongshore：小幅加分。
- offshore 且风不小：扣分。
- 强风不管方向都会降低 trip quality。
- 岸线几何不确定时，不做强判断。

这部分只应该表达成“更支持/不支持这个岸线”，不能说成绝对结论。

## 13. 结构和水流互动

结构互动模块关注：

- 岸线复杂度
- 遮蔽程度
- coastal edge signal
- 潮汐 movement

大致计算：

```text
structure_edge_signal =
    0.65 * coastline_complexity
  + 0.20 * shelter
  + 0.15 * coastal_edge_signal

interaction = structure_edge_signal * tide_movement
```

当前加分逻辑：

- 复杂岸线配合移动水：加分。
- 河口边、内湾边、礁石边、人工结构附近，如果同时有水流：加分。
- 没有确认结构时，只能说“结构感/边界感更强”，不能说“这里有真实 jetty/reef”。

## 14. 光照和月相

当前 light/time 模块包括：

- sunrise 附近
- sunset 附近
- dawn/dusk
- night
- high sun / noon penalty
- major/minor moon
- moon phase

典型规则：

- 日出/日落附近加分。
- dawn/dusk 加分。
- major moon 小幅加分。
- 满月或暗月夜晚小幅加分。
- 正午高日照，尤其弱水流时扣分。

月相权重保持低位。当前它只提供小幅修正，不能决定整天强弱。

## 15. Raw time signal

系统保留一个 `raw_time_signal`，用于解释“纯时间信号”。

它大致表示：

- 如果只看光照、时间、月相，这个小时是否好。
- 不包含本地潮汐、水流、天气冲击、风向、浪况。

这用于解释：

- “时间看起来不错，但被弱潮水、天气不稳、风向不支持拉低。”
- “不是所有日出/日落都应该自动高分。”

当前 raw time signal 不应该直接展示为内部术语，而应该转成用户语言。

## 16. 水域类型评分

当前四类主要钓法/场景：

- beach
- rocks
- jetty
- bay/estuary edge

每类都会生成：

- resident opportunity
- roaming opportunity
- trip quality
- overall
- confidence
- evidence/reasons

### 16.1 Beach

更依赖：

- open coast exposure
- coastal edge
- access
- rising tide
- moderate wave
- not too much wind

开放海滩在强风、大浪、天气冲击时会被更重地压低。

### 16.2 Rocks

更依赖：

- exposure
- coastline complexity
- deep/open water access proxy
- tide movement
- wave not excessive

rocks 对结构和边界更敏感，但安全风险也更应该谨慎表达。

### 16.3 Jetty

更依赖：

- confirmed or inferred structure
- shelter
- tide movement
- night/light proxy if available
- access

没有确认 public jetty 时，前端不能说成真实 jetty。

### 16.4 Bay / Estuary Edge

更依赖：

- shelter
- coastline complexity
- moving tide
- falling or rising tide depending on local edge
- stable weather
- wind not breaking presentation

河口和内湾对水流、风向、天气趋势更敏感。相比月相和光照，水流、风向、天气趋势更重要。

## 17. 潮汐对不同类型的调整

当前 `_apply_tide_adjustment` 大致使用：

```text
resident += 12 * (tide_value - 0.60)
roaming  += 20 * (tide_value - 0.60)
trip     +=  8 * (tide_value - 0.60)
```

含义：

- tide 对 roaming predators 影响更大。
- resident fish 也受影响，但幅度小一些。
- trip quality 受 tide 影响，但不应该只由 tide 决定。

不同水域类型有不同 tide preference：

- beach：rising 更好。
- rocks：rising/high/moving water 更好。
- jetty：running current 更好。
- bay/estuary edge：falling 和 rising 都可能有用，取决于是否有 draining edge。

## 18. 环境修正

环境修正会综合：

- movement bonus
- pressure bonus
- exposure penalty
- shelter bonus
- wind alignment
- swell alignment
- weather stress
- structure flow
- generic rule delta

简化理解：

- 水动、风向支持、天气稳定、结构边界明确：加分。
- 水不动、风向不支持、天气刚剧烈变化、浪风过大：扣分。
- sheltered estuary 不应该被开放海岸浪况完全误伤，但如果海况确实灌入内湾，也会扣。

## 19. 内部评分层

当前不是单一分数。内部主要有：

- `activity_score`：鱼开口或活动时机。
- `presence_score`：附近是否可能有鱼或鱼是否集中。
- `trip_quality_score`：这个时间/地点是否值得实际出行。
- `resident_opportunity`：底栖或常驻类机会。
- `roaming_opportunity`：巡游捕食类机会。
- `big_fish_near_shore`：大鱼靠岸机会，当前很保守。
- `confidence`：系统对这个判断有多确定。

当前前端主要展示：

- 今日总体判断。
- 24 小时鱼情曲线。
- 日均分日期条。
- day overview。
- 天气/风/潮/浪可视化。
- 地图钓点。

## 20. 前端日均分

当前日期条显示的是每日平均分，不是最高峰。

每日 summary 大致按全天窗口平均：

```text
fish_index = average(activity, presence)

visible_day_score =
    0.40 * activity
  + 0.35 * presence
  + 0.25 * trip_quality
```

这样做的原因：

- 防止某一个小时的短暂高峰把整天误导成好日子。
- 更符合“今天是否值得安排一趟”的用户决策。
- 如果全天大部分时间很差，只能说有短窗口，而不是整天好。

## 21. 公共预览校准

搜索坐标不是人工热点，所以当前有 public preview calibration。

校准函数大致为：

```text
if score <= 35:
    score = score * 0.92
elif score <= 50:
    score = 32.2 + (score - 35) * 0.95
elif score <= 65:
    score = 46.45 + (score - 50) * 1.02
elif score <= 78:
    score = 61.75 + (score - 65) * 1.05
else:
    score = min(86.5, 75.4 + (score - 78) * 0.55)
```

目的：

- 普通日子不要过高。
- 搜索坐标不要假装有人工热点置信度。
- 仍然保留强信号叠加时达到 80+ 的路径。
- 避免用户觉得每天都“还不错”。

## 22. 极端分保护

当前有多个 guard，防止虚高。

### 22.1 False high guards

典型情况：

- 时间很好，但水不动。
- 月相或日出不错，但天气冲击很强。
- activity 高，但 trip quality 很差。
- presence 高，但 movement 太弱。

系统会 cap 或扣分，避免“看起来有个窗口但实际不值得安排”。

### 22.2 Local system priority guards

这部分主要解决不同水域的真实优先级。

河口/内湾：

- 水流、风向、天气趋势优先。
- 如果 timing 很好但 flow 不支持，会压低。
- 天气趋势被打破时，河口系统尤其容易被压低。

开放海岸：

- 浪、风、暴露度更重要。
- 同样的风浪，在 sheltered bay 和 open coast 的影响不同。

### 22.3 Ocean-influenced estuary pressure

有些点看起来像内湾或河口，但仍受外海浪涌影响。当前逻辑会检测：

- water body exposure
- inner bay shelter
- effective wave

如果内湾实际受外海影响，会对 bay/jetty 类型加压，避免过度乐观。

### 22.4 Sheltered estuary support lift

如果一个 sheltered estuary 具备：

- 没有明显天气冲击。
- 没有大浪灌入。
- flow 支持。
- wind fit 不差。
- moving water 或 structure flow 成立。

系统会给小幅支撑。这样避免 sheltered estuary 被开放海岸规则压得过低。

## 23. 当前推荐标签

当前前端会把分数转成大致状态：

- WAIT：不建议专门安排。
- MAYBE：可以短时间尝试，或顺路看。
- GO：有相对明确的好窗口或整体支持。

这些标签的目标是降低用户理解成本。用户不应该只看到一个数字，还应该看到“今天大概该怎么理解”。

## 24. Day overview

当前 day overview 不是分析最佳窗口，而是分析当天整体情况。

它包含：

- Fish outlook：解释鱼情指数的意义。
- Water movement：解释当天潮水/水流是否支持。
- Weather comfort：解释风、冷暖、体感。
- Waves + safety：解释浪况和宽泛安全风险。
- Tags：用短标签总结核心影响因素。

注意：这里应该解释分数原因，不应该写行动建议，也不应该保留 backup 建议。

## 25. 天气可视化

当前前端天气模块：

- 使用 Windy 嵌入作为风图视觉层。
- 使用本地 hourly forecast 数据画风、潮、浪等曲线。
- 曲线跟随左侧用户选择的日期和时间。

Windy 图本身是视觉参考，不是当前评分的主要数据源。当前评分仍以 Open-Meteo 等后端数据为准。

## 26. Confidence

confidence 不是分数。它表示系统对判断的确定性。

加分因素：

- 坐标就在水边或水上。
- 搜索结果 confidence 高。
- 有 Open-Meteo 条件数据。
- 有更可靠潮汐数据。
- 岸线方向和水域类型明确。

降分或 cap 因素：

- tide 只是模型估计。
- 天气历史不完整。
- 岸线几何不确定。
- wind-to-shore 不确定。
- search confidence 低。
- weather shock 高。
- 结构只是 inferred，不是 confirmed。

当前 confidence label 大致为：

- medium
- low

搜索坐标默认很难达到高置信，这是合理的。

## 27. Planner 和解释文案

Planner 当前主要生成用户可读解释，不应该改核心分数。

当前已有约束：

- 不把未确认结构说成真实结构。
- 不把现场观察当成事实。
- 不承诺有鱼。
- 只解释已知数据如何影响判断。

如果接入 LLM，建议只用于说人话：

- 哪些因素拉低。
- 哪些因素支撑。
- 今天为什么是 WAIT/MAYBE/GO。
- 用户应该如何理解这个分数。

LLM 不应该绕过算法改分。

## 28. 地图钓点

地图钓点来源包括 official/mapped access。

当前逻辑：

- 只展示一定范围内的公开或可映射钓点。
- 对 near duplicate 做合并。
- 地图点分数来自当前地点环境和对应类型机会，不等于那个点的实测鱼情。
- 前端目前限制展示近距离候选，避免 20 km 外点干扰当前搜索。

需要注意：

- 官方 fishing map entry 可以说是官方地图条目。
- OSM 推断结构不能说成官方确认。
- boat ramp 不一定适合岸钓，只能谨慎展示。

## 29. 当前没有完整实现的模块

下面这些不是当前完整自动评分能力，后续可以增强。

### 29.1 独立 Safety Score

当前没有完全独立的 safety score。

现在安全相关主要散落在：

- trip quality
- wave/swell/gust/rain penalty
- waves + safety 文案
- marine condition 风险表达

后续可以拆成独立 safety score，但不要和 fish activity 混在一起。

### 29.2 真实水温适配

当前可用 sea surface temperature，但没有完整 species temperature profile。

已做：

- SST 太冷扣分。
- 15-22 度大致加分。

未做：

- 按目标鱼种分别适配水温。
- 河口实际水温。
- 浅滩日内升温。

### 29.3 河流流量和淡水输入

当前主要用 rainfall proxy。

已做：

- 24h/48h/72h 降雨影响。
- 大雨后 dirty water/freshwater inflow proxy。

未做：

- river height
- river flow
- flood warning
- 盐度变化
- 养料/浑水带实际边界

### 29.4 Bathymetry 和深水可达性

当前 deep water within casting range 主要是 proxy，没有真实等深线。

未做：

- nautical chart
- bathymetry
- channel/drop-off/gully 自动识别
- casting range 内深水距离

### 29.5 Legal/advisory

当前没有完整法律和食用建议模块。

未做：

- size limits
- bag limits
- closed seasons
- marine protected areas
- pollution advisories
- consumption advisories

这些后续应该单独展示，不应该并入鱼情分。

### 29.6 Species profile

当前已有 resident、roaming、大鱼靠岸等粗分层。

未做完整 species profile：

- resident bottom species
- structure ambush predators
- mobile schooling predators
- 不同 species 对 tide、temperature、light、structure、weather stability 的不同权重

### 29.7 用户现场 tips

当前不自动使用：

- baitfish
- birds diving
- surface boils
- water colour
- weed floating
- snag level
- boat traffic
- crowding
- short strikes
- shark/ray bycatch

这些应该作为用户手动报告后的 modifier 或 tips，不应该默认进入自动分。

## 30. 当前调优建议

短期最稳妥的调优方向：

1. 保持日均分，不回退到最高峰。
2. 加强 day overview 的用户语言，让用户知道 35、50、70 分各自意味着什么。
3. 河口系统继续提高水流、风向、天气趋势权重。
4. 开放海岸继续提高浪、风、暴露度权重。
5. 拆出独立 safety score，但不要马上大改主分。
6. 完善 tide stage 八段分类，让潮汐解释更清楚。
7. 加入 bathymetry 或 channel/drop-off 数据前，不要把“深水可达”说得太确定。
8. 增加 confidence 解释，让用户知道“分数不低但置信低”的原因。

## 31. 当前测试和验证入口

常用后端测试：

```bash
./.venv/bin/python -m unittest discover -s tests -v
```

常用 CLI 检查：

```bash
./.venv/bin/coastal-preview --lat <lat> --lon <lon>
./.venv/bin/coastal-search-forecast "<place name>"
```

常用前端检查：

```bash
cd apps/web
npm run dev
```

然后在浏览器打开：

```text
http://127.0.0.1:5173/
```

调分后必须检查：

- 前端可见分数，不只看后端内部值。
- 日期条是否显示日均分。
- 全天曲线是否和选中时间联动。
- day overview 是否解释当天整体，而不是只解释最佳窗口。
- Windy 只是视觉层，不要误认为评分数据源。

## 32. 给后续 AI 的执行提醒

如果你要继续改这个引擎：

- 先确认工作目录是 `workspace-cocky/coastal-fishing-forecast`。
- 不要编辑个人德文特项目。
- 不要把现场观察当自动事实。
- 不要把安全、舒适、鱼情混成一个不可解释的总分。
- 调分时看前端显示的日均分和用户观感，不只看某个小时的峰值。
- 改算法后至少跑一次测试。
- 改前端后必须看浏览器实际显示。
- 不确定结构时，文案必须保守。
- 不确定潮汐或岸线时，confidence 要降。

