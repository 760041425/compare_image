---
type: entity
title: SimilarityResult — 比对结果
tags: [entity, comparison-context]
related: [query-image, video-frame, adr-001-xfeat-primary-strategy]
created: 2026-07-18
updated: 2026-07-18
bounded_context: comparison
attributes: [num_matches, avg_confidence, composite_score, elapsed_ms]
behaviors: [rank, filter_by_threshold, to_dict]
---

# SimilarityResult

## 所属限界上下文

Comparison Context

## 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| query_image | QueryImage | 查询图片引用 |
| matched_frame | VideoFrame | 匹配的视频帧 |
| num_matches | int | 匹配特征点数量 |
| avg_confidence | float | 平均置信度 [0,1] |
| composite_score | float | 综合得分 = 0.6×log1p(matches)/log1p(4096) + 0.4×confidence |
| elapsed_ms | float | 处理耗时 |
| algorithm | str | 使用的算法名 |

## 行为

- `rank(results)` — 按 composite_score 排序
- `filter_by_threshold(threshold)` — 过滤低于阈值的结果
- `top_n(n)` — 返回前 N 个最佳匹配

## Benchmark 数据 (2026-07-18)

所有算法的最佳结果均指向 Frame #510 (t=17.0s):

| 算法 | Score | Matches | Confidence |
|------|-------|---------|------------|
| XFeat | 0.767 | 668 | 0.676 |
| ALIKED | 0.658 | 285 | 0.489 |
| LightGlue | 0.628 | 46 | 0.236 |
| ORB | 0.611 | 15 | 0.839 |
