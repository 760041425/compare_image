---
type: entity
title: VideoFrame — 视频帧
tags: [entity, video-context]
related: [image-feature, similarity-result]
created: 2026-07-18
updated: 2026-07-18
bounded_context: video
attributes: [index, timestamp_ms, image_data]
behaviors: [extract, resize, save]
---

# VideoFrame

## 所属限界上下文

Video Context

## 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| index | int | 帧在视频中的序号 |
| timestamp_ms | float | 时间戳 (毫秒) |
| image_data | ImageData | 帧图像数据 |

## 行为

- `extract(video_source, mode)` — 从视频中按策略提取
- `resize(max_dim)` — 等比例缩放
- `save(path)` — 保存为图片文件

## 当前实现

- 采样率: 1fps (每 30 帧取 1 帧)
- 原始尺寸: 540×960 (竖版)
- 处理后: ~574×1024 (resize 到 max 1024px)
- 总帧数: 31 (30.4s 视频)

## 关联

- → [[image-feature]] — VideoFrame 也需提取特征用于比对
- → [[similarity-result]] — 与 QueryImage 比对产生结果
