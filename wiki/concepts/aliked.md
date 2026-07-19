---
type: concept
title: ALIKED — 轻量关键点检测网络
tags: [deep-learning, keypoint-detection, lightweight]
related: [algorithm-benchmark-2026, xfeat]
created: 2026-07-18
updated: 2026-07-18
---

# ALIKED

## 概述

ALIKED (A Lighter Keypoint and Descriptor Extraction Network via Deformable Transformation)
是一个轻量级关键点检测和描述符提取网络，通过可变形变换实现鲁棒的特征提取。
IEEE TIM 2023 发表。

## 在本项目中的角色

备选比对策略 — benchmark 中综合得分第二 (0.658)。

## 使用方式 (kornia)

```python
import kornia.feature as KF

detector = KF.ALIKED.from_pretrained('aliked-n16', device=device).eval()
features = detector(image_tensor)[0]
# features.keypoints    — (N, 2)
# features.descriptors  — (N, D) L2 归一化
# features.keypoint_scores — (N,)

distances, indices = KF.match_mnn(features.descriptors, frame_features.descriptors)
```

## 模型变体

- `aliked-t16` — 最快，适合实时
- `aliked-n16` — 标准（本项目使用）
- `aliked-n16rot` — 旋转不变
- `aliked-n32` — 更高精度

## 性能特征

- **速度**: ~175ms/帧 (MPS)
- **匹配数**: ~285
- **置信度**: ~0.489

## 参考

- 论文: IEEE TIM 2023
- GitHub: [Shiaoming/ALIKED](https://github.com/Shiaoming/ALIKED)
