# 中文本地化文案清单

Source: `apps/web/src/App.tsx`

Use this file as the Chinese copy review sheet. Edit the `中文文案` column only; keep the key, condition, and variable placeholders intact.

## 1. 固定 UI 文案

| Key | 中文文案 |
| --- | --- |
| languageToggle | EN |
| languageToggle shown in English UI | 中文 |
| themeToggleDay | 日间 |
| themeToggleNight | 夜间 |
| switchToEnglish | 切换到英文 |
| switchToChinese | 切换到中文 |
| switchToDay | 切换到日间模式 |
| switchToNight | 切换到夜间模式 |
| brand | Coastal Fishing Forecast |
| eyebrow | 通用海岸鱼情预测引擎 |
| heroTitle | 看看分数再出发。 |
| heroCopy | 搜索地点，查看鱼情。 |
| searchPlaceholder | 搜索海岸地点 |
| forecastButton | 查看鱼情 |
| checkingButton | 分析中... |
| selectedPlace | 已选地点 |
| waitingPlace | 等待预测 |
| todayScore | 今日建议 |
| fishPotential | 潜力 |
| tripReality | 出行质量 |
| waterbodyClass | 水域类型 |
| waterTemp | 水温 |
| airTemp | 气温 |
| temperature | 温度 |
| searchResultWaiting | 搜索后会显示今日分数。 |
| strongestNearby | 更值得一试的水域。 |
| primaryMap | 主要地图 |
| selectedMap | 已选地图 |
| publicAccessTitle | 附近公共钓点 |
| unsupportedMapTitle | 所选位置不在当前预测范围内 |
| officialAccess | 官方钓点 |
| supportedSignals | 信号 |
| mapControls | 地图控制 |
| dragMap | 拖动地图  |
| fishingAccess | 钓点 |
| boatRamp | 公共船坡 |
| mapReference | 地图参考 |
| supplementalSpot | 公开指南钓点 |
| mapLeads | 地图线索 |
| mapIntro | 显示 5 公里内确认或公开钓点。船坡和离岸点只作地图参考，请以实际情况为准。 |
| mapOnlyAccess | 附近有地图参考 |
| mapOnlyAccessNote | 能否钓鱼仍需现场确认规则。 |
| mapOnlyScoreLabel | 地图 |
| noAccess | 附近没有确认的公共钓点 |
| noAccessMeta | 5 公里内暂无确认钓点 |
| noAccessNote | 建议咨询本地钓手。 |
| unsupported | 暂不支持 |
| unsupportedAdvice | 请搜索沿海地区。 |
| fishActivity24h | 鱼情曲线 |
| historyForecast | 每日趋势 |
| dragDates | 横向滑动看每日鱼情分 |
| dateStripPeakLabel | 日分 |
| today | 今天 |
| score | 评分 |
| scoreLayers | 评分拆分 |
| activity | 活跃度 |
| presence | 鱼情信号 |
| trip | 出行质量 |
| biteTiming | 开口时间 |
| fishNearby | 近岸活跃参考 |
| whyWindow | 全天情况 |
| bestTime | 最佳时间 |
| tide | 潮汐 |
| comfort | 舒适度 |
| pressure | 气压 |
| firstMove | 今日建议 |
| scoreFactors | 分数详解 |
| scoreFactorsGenerating | 正在生成说明… |
| scoreFactorsPositive | 加分项 |
| scoreFactorsNegative | 扣分项 |
| backup | 备选方案 |
| weatherVisual | 风浪可视化 |
| windTideWaves | 风、潮汐、浪与涌浪 |
| windMap | 风场地图 |
| windSpeed | 风速 |
| windyNote | Windy 风场，下方曲线使用同一组逐小时数据。 |
| tideHeight | 潮高 |
| tideMovement | 潮汐变化 |
| tideMovementProxyNote | 这条曲线看的是潮水流动强弱，不是潮汐表里的潮位高度。 |
| waveHeight | 浪高 |
| swellHeight | 涌浪高度 |
| publicPlanNote | 仅作地图参考。 |
| exactPlace | 选择准确地点 |
| noPlaceFound | 没有找到匹配地点。 |
| reset | 重置 |
| searchPoint | 搜索点 |
| closeMarker | 关闭点位详情 |
| mapLegend | 地图图例 |
| noMapCenter | 没有可用地图中心。 |
| selectedCoordinate | 已选坐标 |
| dateSelector | 预测日期选择器 |
| fishCurveLabel | 全天鱼情曲线 |
| windyTitle | Windy 风场地图 |

## 2. 今日分数、徽章和日期总结

| Context | Condition | 中文文案 |
| --- | --- | --- |
| 今日徽章 | 65+ | 出发吧！ |
| 今日徽章 | 40-64 | 值得一试 |
| 今日徽章 | <40 | 别抱太大希望 |
| 今日判断 | 无分数 | 请稍等。 |
| 今日判断 | 70+ | 此时不去更待何时？ |
| 今日判断 | 55-69 | 值得一试，但别抱太大希望。 |
| 今日判断 | 40-54 | 顺路的话可以一试 |
| 今日判断 | <40 | 还是改天再去吧 |
| 日期窗口总结 | 无分数 | 选择日期查看当天窗口。 |
| 日期窗口总结 | 70+ | 这一天有较强的附近窗口。 |
| 日期窗口总结 | 55-69 | 这一天可以钓，但需要清晰计划。 |
| 日期窗口总结 | 40-54 | 这一天偏勉强，适合短试。 |
| 日期窗口总结 | <40 | 这一天不适合专门出钓。 |
| 日期整体判断 | 无分数 | 请选择日期。 |
| 日期整体判断 | 70+ | 是时候认真规划一场爆钓了。 |
| 日期整体判断 | 55-69 | 适合轻松愉快的钓鱼之旅。 |
| 日期整体判断 | 40-54 | 顺路的话可以试试。 |
| 日期整体判断 | <40 | 建议这天干些别的。 |

## 3. 水域、结构和地图标签

| Context | Key / Condition | 中文文案 |
| --- | --- | --- |
| 水域类型 | bay_estuary_edge | 湾区 / 河口边缘 |
| 水域类型 | beach | 沙滩 |
| 水域类型 | rocks | 礁石 |
| 水域类型 | jetty | 码头 |
| 水域类型 | morning | 早晨 |
| 水域类型 | dusk | 黄昏 |
| 水域类型 | pre_dawn | 黎明前 |
| 水域类型 | day | 白天 |
| 水域类型 | night | 夜间 |
| 水域类型 | open_water | 开放水域 |
| 潮汐阶段 | rising / flood | 涨潮 |
| 潮汐阶段 | falling / ebb | 落潮 |
| 潮汐阶段 | slack | 平潮 |
| 潮汐阶段 | high | 高潮 |
| 潮汐阶段 | low | 低潮 |
| 水体分类 | open_coast | 外海岸 |
| 水体分类 | surf_coast | 冲浪海岸 |
| 水体分类 | bay_coast | 内湾岸线 |
| 水体分类 | sheltered_estuary | 遮蔽河口 / 内湾 |
| 水体分类 | river_mouth | 河口 |
| 水体分类 | tidal_river | 潮汐河道 |
| 水体分类 | harbour_access | 港湾 / 入口水域 |
| 水体分类 | unsupported | 暂不支持水域 |
| 结构类型 | artificial_reef | 人工鱼礁 |
| 结构类型 | beach_access | 沙滩入口 |
| 结构类型 | boat_ramp | 船坡 / 下水点 |
| 结构类型 | fad | FAD 聚鱼装置 |
| 结构类型 | fishing_platform | 钓鱼平台 |
| 结构类型 | official_fishing_spot | 官方钓点 |
| 结构类型 | pier | 栈桥 |
| 结构类型 | public_jetty | 公共码头 |
| 结构类型 | public_pier | 公共栈桥 |
| 结构类型 | public_wharf | 公共码头 |
| 结构类型 | rocky_shoreline | 礁石岸线 |
| 来源兜底 | 无 source | 预测数据 |
| 结构兜底 | 无 type | 地图结构 |
| 入口状态 | public | 公共入口 |
| 入口状态 | private | 私人入口 |
| 入口状态 | unknown | 入口未知 |
| 水域分类中 | 无值 | 自动判断中 |
| 地图点说明 | list_wildfisheries | 官方钓点入口。 |
| 地图点说明 | public access | 公共入口。 |
| 地图点说明 | access lead | 作为入口线索使用，出发前确认规则和安全。 |

## 4. 今日建议和备选方案

| Context | 中文文案 |
| --- | --- |
| 今日不建议出发 | 今天跳过这个点。条件太弱，不适合专门出钓；等更稳定的窗口，或换附近更合适的位置。 |
| 公共入口起步 | 从公共入口开始，时间约 `${time}` |
| 水域类型起步 | 从最强的`${waterType}`水域开始，时间约 `${time}` |
| 起步后操作 | `${start}`。给它 60-90 分钟；如果水面一直很安静，就换点。 |
| 弱分备选 | 更好的备选：选择更有遮蔽的位置，或把这次出钓留到下一个稳定日。 |
| 礁石岸线备选 | 备选：如果第一个位置人多、关闭或没有动静，换到地图标注的礁石岸线。 |
| 湾区优势 | 优势：有遮蔽的边缘在外侧水域一般时更容易保持稳定。 |
| 码头优势 | 优势：结构物容易集中水流、阴影和饵鱼移动。 |
| 沙滩优势 | 优势：沙滩沟槽和边线在潮汐、浪况配合时更有机会。 |
| 礁石优势 | 优势：硬边和浪花能提供掩护与伏击路线。 |
| 通用优势 | 优势：这是当前窗口附近较强的水域信号之一。 |
| 湾区短标签 | 有遮蔽水域 |
| 码头短标签 | 水流和阴影 |
| 沙滩短标签 | 沟槽和边线 |
| 礁石短标签 | 浪花和掩护 |
| 通用短标签 | 附近较强类型 |

## 5. 分数原因文案

| Context | 中文文案 |
| --- | --- |
| 鱼情无数据 | 数据不足。 |
| 鱼情 70+ | 鱼情信号强。 |
| 鱼情 55-69 | 有机会，可以碰碰运气。 |
| 鱼情 40-54 | 整体一般。 |
| 鱼情 <40 | 改天吧。 |
| 白天强光扣分 | 白天强光会降低鱼的开口欲望，建议考虑清晨或傍晚窗口。 |
| 近期天气变化扣分 | 近期天气变化较大，近岸鱼情不稳定。 |
| 缓水扣分 | 部分时段接近缓水，水流推动不足。 |
| 弱潮扣分 | 潮水推动偏弱，诱鱼和换水信号不足。 |
| 阵风扣分 | 阵风偏强，抛投会受影响。 |
| 强风扣分 | 风力偏强，控线难度和体感压力上升。 |
| 降雨扣分 | 降雨会影响近岸水色、水质和稳定性。 |
| 偏冷扣分 | 气温或水温偏冷，鱼类活跃度可能下降。 |
| 浪况扣分 | 浪况偏大，近岸操作难度和危险性上升。 |
| 通用扣分 | `${rule.label}` 会降低这个时段的表现。 |
| 短窗口提醒 | 当天机会主要集中在少数短窗口，其他时段整体表现较弱。 |
| 强潮加分 | 潮水交换较明显，有利于近岸水流和食物移动。 |
| 中等潮加分 | 潮水具备一定流动性，水体并非完全停滞。 |
| 弱潮说明 | 潮水整体偏弱，水流推动不足，鱼不容易开口。 |
| 潮差说明 | 潮差具备一定幅度，涨落潮节奏较明确。 |
| 水温缺失 | 水温或水温趋势数据不足，鱼情判断会更保守。 |
| 水温冷 | 水温明显偏冷，不能只因为潮水不错就给高鱼情。 |
| 水温凉 | 水温偏凉，鱼情更依赖短时间强水流。 |
| 水温热 | 水温偏热，浅水鱼情稳定性会下降。 |
| 水温合适 | 水温处在目标鱼可接受区间，而且近期变化稳定。 |
| 水温快速下降 | 水温快速下降，鱼情稳定性受到压制。 |
| 水温快速升高 | 水温快速升高，浅水鱼情需要保守判断。 |
| 气温低 | 气温偏低，体感偏冷。 |
| 风力大 | 风力偏大，控线、抛投难度上升。 |
| 阵风强 | 阵风偏强，抛投和站稳需要更加谨慎。 |
| 当天雨明显 | 当天降雨较明显，近岸水况可能受影响。 |
| 近期天气不稳 | 近期天气变化偏大，鱼情稳定性下降。 |
| 天气温和 | 天气整体较温和，未见明显低温、大风、大雨或突变。 |
| 浪况缺失 | 缺少可靠浪况数据，海面情况需现场确认。 |
| 内湾估算浪高 | 浪高来自内湾估算，靠外位置仍需谨慎判断。 |
| 海面数据不足 | 浪况数据不足，海面情况需现场确认。 |
| 浪况偏大 | 浪况偏大，近岸操作难度和安全压力上升。 |
| 浪况中等偏高 | 浪况中等偏高，遮蔽位置更适合执行。 |
| 浪况不大 | 浪况不大，海面整体较平稳。 |
| 涌浪偏大 | 涌浪偏大，即使本地浪高不高，靠外水域的出行品质也会下降。 |
| 涌浪中等 | 涌浪有存在感，外露海岸和礁石位置需要降低执行预期。 |
| 涌浪不大 | 涌浪不大，对今天行程品质的压力有限。 |
| 预报趋势 | 预报趋势：`${notes.join("。")}`。 |
| 无明显加分项 | （无明显加分项） |
| 无明显硬伤 | 没有明显硬伤，但仍要按当天整体分数控制预期。 |
| 当前数据不足 | 当前数据不足。 |

## 6. 趋势归一化和近期变化文案

| Source / Context | 中文文案 |
| --- | --- |
| 潮差还可以 | 潮差具备一定幅度，涨落潮节奏较明确。 |
| 涨落潮节奏 | 涨落潮节奏较明确 |
| 比较看得出来 | 较明确 |
| 水体在中等程度上流动 | 潮水具备一定流动性 |
| 不是完全死水 | 水体并非完全停滞 |
| 水动不起来 | 水流推动不足 |
| 鱼口容易散 | 鱼口稳定性较低 |
| 天气还行 | 天气稳定 |
| 体感还可以 | 体感条件较好 |
| 还可以 | 具备一定条件 |
| 还行 | 基本可控 |
| 好处理 | 较平稳 |
| 不算稳 | 稳定性一般 |
| 打折 | 受到削弱 |
| 拖低 | 降低 |
| 近期暖转冷 | 近期由偏暖转为明显降温 |
| 近期暖段 | 近期偏暖阶段 |
| 存在感 | 影响 |
| Air temperature has dropped sharply from the recent warm period | 近期由偏暖转为明显降温 |
| Air temperature has fallen noticeably over the last day | 过去一天明显降温 |
| Pressure has moved quickly over the last day | 过去一天气压变化较快 |
| Pressure is changing quickly in the current window | 当前时段气压变化较快，稳定性下降 |
| Wind direction has shifted strongly in the last half day | 过去半天风向变化明显 |
| Heavy recent rain may have disrupted inshore water conditions | 近期雨量偏大，近岸水色和盐度可能受影响 |
| Recent multi-day rain may still be affecting the water | 近期连续降雨可能仍在影响近岸水况 |
| Recent strong gusts may have unsettled exposed water | 近期阵风偏强，外露水域稳定性较差 |
| The sea state has changed quickly compared with the previous day | 海况变化较快，单个窗口的参考价值有限 |

## 7. 全天情况和原因卡片

| Context | 中文文案 |
| --- | --- |
| 鱼情等待 | 🎣 鱼情：等待预测 |
| 鱼情强窗口 | 🎣 鱼情：`${plainWindowLabel(window.time_window, lang)}`窗口较强 |
| 鱼情尚可 | 🎣 鱼情：尚可，建议抓强窗口 |
| 鱼情零散 | 🎣 鱼情：偏零散，可以碰碰运气|
| 鱼情水况不稳 | 🎣 鱼情：水况不稳，表现偏弱 |
| 鱼情天气变化 | 🎣 鱼情：天气变化后鱼情偏弱 |
| 鱼情偏弱 | 🎣 鱼情：偏弱，建议改天或换点 |
| 天气问题：风 | 风偏强 |
| 天气问题：阵风 | 阵风偏强 |
| 天气问题：雨 | 有雨 |
| 天气问题：冷 | 气温偏冷 |
| 天气问题：近期变化 | 近期天气变化 |
| 天气一般 | 🍃 天气：体感一般，`${weatherProblems.slice(0, 2).join("、")}` |
| 天气舒适 | 🍃 天气：体感舒适 |
| 浪况无数据 | 🌊 浪况：数据不足，现场确认 |
| 浪很大 | 🌊 浪况：浪很大，注意安全，建议穿戴钉鞋和救生衣或跳过这一天 |
| 浪偏大 | 🌊 浪况：浪偏大，选择安全地点 |
| 浪中等偏大 | 🌊 浪况：中等偏大 |
| 浪不大 | 🌊 浪况：不大 |
| 安全问题：外露水域 | 外露礁石和沙滩需要谨慎 |
| 安全问题：强阵风 | 强阵风会影响抛投和站稳 |
| 安全问题：强风 | 强风会增加暴露风险 |
| 安全问题：大雨 | 大雨会影响视线和脚下安全 |
| 安全有问题 | ⚠️ 安全：`${safetyProblems[0]}` |
| 安全无明显风险 | ⚠️ 安全：未发现明显风险 |

## 8. 日概览卡片和标签

| Context | 中文文案 |
| --- | --- |
| 光照：夜间 | 弱光 |
| 光照：早晚 | 光线变化 |
| 光照：白天 | 白天 |
| 风况：小风 | 风小且舒服 |
| 风况：中等 | 可接受 |
| 风况：偏难 | 迎风区域会更难操作 |
| 浪况：无数据 | 浪况数据不足 |
| 浪况：平静 | 水面平静 |
| 浪况：可钓 | 可钓 |
| 浪况：偏粗 | 水况不稳 |
| 水温：不足 | 水温不足，保守判断。 |
| 水温：冷 | 偏冷，压低活跃度。 |
| 水温：凉 | 偏凉，依赖好窗口。 |
| 水温：热 | 偏热，浅水受压。 |
| 水温：快速降温 | 快速降温，不稳定。 |
| 水温：快速升温 | 升温较快，需保守。 |
| 水温：合适稳定 | 合适且稳定。 |
| 水温：默认 | 水温可参考。 |
| 潮相 | 潮相变化 |
| 水流明显 | 水流明显 |
| 水流中等 | 水流中等 |
| 水流偏弱 | 水流偏弱 |
| 平均风偏强 | 平均风偏强 |
| 阵风偏强 | 阵风偏强 |
| 有雨 | 有雨 |
| 偏冷 | 偏冷 |
| 近期天气变化 | 近期天气变化 |
| 涌浪偏大 | 涌浪偏大 |
| 本地浪高数据不足 | 本地浪高数据不足 |
| 外露水域浪偏大 | 外露水域浪偏大 |
| 强阵风影响 | 强阵风影响站稳和抛投 |
| 本地浪高不足 | 本地浪高不足 |
| 最高浪高 | 最高浪高 |
| 涌浪 | 涌浪 |
| 卡片：鱼情 | 鱼情 |
| 卡片：鱼情值 | `${summary.fishIndex ?? "--"}` 鱼情 |
| 卡片：水流 | 水流 |
| 卡片：数据不足 | 数据不足 |
| 卡片：天气 | 天气 |
| 卡片：天气好 | 体感条件较好 |
| 卡片：浪/安全 | 浪/安全 |
| 卡片：安全好 | 未见明显安全压力 |
| 标签：等待评分 | 等待评分 |
| 标签：全天可钓 | 全天可钓 |
| 标签：整体一般 | 整体一般 |
| 标签：全天偏弱 | 全天偏弱 |
| 标签：水流明显 | 水流明显 |
| 标签：水流中等 | 水流中等 |
| 标签：水流偏弱 | 水流偏弱 |
| 标签：风偏强 | 风偏强 |
| 标签：体感偏冷 | 体感偏冷 |
| 标签：天气稳定 | 天气稳定 |
| 标签：水温拖后腿 | 水温拖后腿 |
| 标签：水温稳定 | 水温稳定 |
| 标签：涌浪偏大 | 涌浪偏大 |
| 标签：浪况待确认 | 浪况待确认 |
| 标签：避开外露水域 | 避开外露水域 |
| 标签：浪不大 | 浪不大 |
| Rule strip aria-label | 全天主要信号 |

## 9. 地图、曲线和辅助说明

| Context | 中文文案 |
| --- | --- |
| 地图 aria-label | 附近公共钓点地图预览 |
| 曲线活跃度 | 活跃度 `${activePointData.score}` |
| 曲线弱日说明 | 全天曲线整体偏弱。不要只因为某个小时略好就专门出发。 |
| 曲线通用说明 | 用曲线判断当天鱼情强弱，但请参考天气、水流和浪况决定是否出发。 |
| 温度图 aria-label | 逐小时气温和水温曲线 |
| 分数拆分 aria-label | 鱼情和出行拆分 |
| 鱼情潜力说明 | 只看鱼情。 |
| 出行风险高 | 安全压力高，出行建议会被压低。 |
| 出行安全余量一般 | 安全余量一般。 |
| 出行现实说明 | 天气、浪和安全。 |
| 不支持水域标题 | 当前预测仅支持海岸和潮汐钓鱼区域。 |

## 10. 内部筛选关键词

These words are used to classify generated reasons as positive or negative. They may not appear directly as complete UI sentences, but changing them can affect how reason lists are grouped.

| Type | 中文词 |
| --- | --- |
| negative keyword | 偏低 |
| negative keyword | 只有 |
| negative keyword | 不算 |
| negative keyword | 不是 |
| negative keyword | 短试 |
| negative keyword | 低到 |
| negative keyword | 不均匀 |
| negative keyword | 偏弱 |
| negative keyword | 缓水 |
| negative keyword | 打折 |
| negative keyword | 缺失 |
| negative keyword | 估算 |
| negative keyword | 突变 |
| negative keyword | 下降 |
| negative keyword | 波动 |
| negative keyword | 偏大 |
| negative phrase | 全天综合分只有 |
| negative phrase | 鱼情指数只有 |
| negative phrase | 行程质量只有 |
| positive keyword | 活跃 |
| positive keyword | 一定流动 |
| positive keyword | 水体并非完全停滞 |
| positive keyword | 潮差 |
| positive keyword | 温和 |
| positive keyword | 没有极端 |
| positive keyword | 浪不大 |
| positive keyword | 较平稳 |
