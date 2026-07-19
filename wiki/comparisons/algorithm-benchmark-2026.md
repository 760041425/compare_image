---
type: comparison
title: 图像比对算法 Benchmark (2026-07-18)
tags: [xfeat, aliked, lightglue, orb, benchmark]
related: [adr-001-xfeat-primary-strategy, xfeat, aliked, lightglue, orb]
created: 2026-07-18
updated: 2026-07-18
---

# 图像比对算法 Benchmark

## 测试条件

- **视频**: `data/242d929f1b68303b2f7edbff10c14427.mp4` (540×960, 30fps, 30.4s)
- **查询图**: `query_image/f04eb4d677dfc38ac2304575aaf80dfa.jpg` (1279×1706)
- **采样**: 1fps → 31 帧
- **设备**: Apple Silicon MPS
- **预处理**: resize 到最长边 1024px

## 结果汇总

| 算法 | 综合得分 | 平均匹配数 | 平均置信度 | 平均耗时 | 最佳帧 |
|------|----------|-----------|-----------|---------|--------|
| **XFeat** | **0.767** | ~668 | 0.676 | ~60ms | #510 |
| **ALIKED** | 0.658 | ~285 | 0.489 | ~175ms | #510 |
| **LightGlue** | 0.628 | ~46 | 0.236 | ~1000ms | #510 |
| **ORB** | 0.611 | ~15 | 0.839 | ~15ms | #510 |

## 关键发现

1. **4 算法共识**: 全部算法独立选出相同的最佳帧 (#510, t=17.0s)，说明匹配结果可靠
2. **XFeat 综合最优**: 匹配数最多(668)，置信度高(0.676)，速度快(~60ms)
3. **ORB 最快但匹配少**: 纯传统方法，15ms/帧，但只找到 15 个匹配点
4. **LightGlue 精度好但慢**: 端到端匹配器质量高，但 1s/帧 难以实时使用
5. **ALIKED 均衡**: 介于 XFeat 和 LightGlue 之间

## 评分方法

综合分 = `0.6 × log1p(matches)/log1p(4096) + 0.4 × confidence`

- 匹配数用 log 归一化，避免某算法靠数量碾压
- 置信度各算法内部归一化到 [0,1]

## 结论

→ [[adr-001-xfeat-primary-strategy]]: XFeat 作为首选比对策略
