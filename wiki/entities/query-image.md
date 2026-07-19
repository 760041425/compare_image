---
type: entity
title: QueryImage — 查询图片
tags: [entity, image-context]
related: [image-feature, similarity-result, spec-001-image-compare]
created: 2026-07-18
updated: 2026-07-18
bounded_context: image
attributes: [path, image_data, features]
behaviors: [load, compute_features, resize]
---

# QueryImage

## 所属限界上下文

Image Context

## 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| path | str | 图片文件路径 |
| image_data | ImageData | 原始图像数据 (numpy array) |
| features | ImageFeature | 提取的特征 (关键点+描述符) |

## 行为

- `load()` — 从磁盘加载图片
- `resize(max_dim)` — 等比例缩放（最长边 = max_dim）
- `compute_features(strategy)` — 用指定策略提取特征

## 当前实现

- 实际数据: `query_image/f04eb4d677dfc38ac2304575aaf80dfa.jpg`
- 原始尺寸: 1279×1706 (竖版)
- 处理后: 767×1023 (resize 到 max 1024px)

## 关联

- → [[image-feature]] — QueryImage 产出特征
- → [[similarity-result]] — 与 VideoFrame 比对产生结果
