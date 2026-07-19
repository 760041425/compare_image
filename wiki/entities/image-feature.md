---
type: entity
title: ImageFeature — 图像特征
tags: [entity, image-context, value-object]
related: [query-image, video-frame, xfeat, aliked, lightglue, orb]
created: 2026-07-18
updated: 2026-07-18
bounded_context: image
attributes: [keypoints, descriptors, scores, method]
behaviors: [match_with, distance_to]
---

# ImageFeature (值对象)

## 所属限界上下文

Image Context (值对象)

## 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| keypoints | np.ndarray (N,2) | 关键点像素坐标 (x,y) |
| descriptors | np.ndarray (N,D) | 描述符向量 (L2 归一化) |
| scores | np.ndarray (N,) | 关键点置信度 (可选) |
| method | str | 提取算法名 |

## 各算法的输出格式

| 算法 | D (维度) | 数据类型 | 归一化 |
|------|----------|----------|--------|
| XFeat | 64 | float32 | L2 |
| ALIKED | 128 | float32 | L2 |
| DISK (LightGlue) | 128 | float32 | L2 |
| ORB | 32 bytes | uint8 | 无 (Hamming) |

## 匹配方式

- **XFeat/ALIKED/DISK**: `KF.match_mnn(desc1, desc2)` — 互最近邻匹配，L2 距离
- **ORB**: `BFMatcher(NORM_HAMMING).knnMatch(k=2)` + Lowe's ratio test
- **LightGlue**: 端到端匹配，输入嵌套 dict，输出 matches + scores

## 关联

- ← [[query-image]] / [[video-frame]] — 从图像提取特征
- → [[similarity-result]] — 特征匹配产生比对结果
