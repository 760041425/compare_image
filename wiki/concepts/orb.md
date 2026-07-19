---
type: concept
title: ORB — 传统特征点检测与描述
tags: [traditional, feature-detection, opencv, cpu]
related: [algorithm-benchmark-2026, xfeat]
created: 2026-07-18
updated: 2026-07-18
---

# ORB (Oriented FAST and Rotated BRIEF)

## 概述

ORB 是 OpenCV 内置的传统特征点检测算法，结合 FAST 关键点和 BRIEF 描述符，
加入方向不变性。纯 CPU 运算，无需深度学习框架。

## 在本项目中的角色

备选比对策略 — 速度最快 (15ms/帧)，但匹配点少。
适合作为 fallback 或资源受限场景。

## 使用方式 (OpenCV)

```python
import cv2

orb = cv2.ORB_create(nfeatures=2000)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

kp1, desc1 = orb.detectAndCompute(gray1, None)
kp2, desc2 = orb.detectAndCompute(gray2, None)

raw_matches = bf.knnMatch(desc1, desc2, k=2)

# Lowe's ratio test
good = []
for m, n in raw_matches:
    if m.distance < 0.75 * n.distance:
        good.append(m)
```

## 性能特征

- **速度**: ~15ms/帧 (CPU) — 最快
- **匹配数**: ~15 — 最少
- **置信度**: ~0.839 — Hamming 距离低
- **GPU**: 不需要

## 优劣

- ✅ 速度极限，纯位运算
- ✅ 无深度学习依赖
- ❌ 面对旋转、尺度、大光照变化容易误匹配
- ❌ 匹配点少，可能遗漏相似度

## OpenCV 5.0 注意事项

OpenCV 5.0 中 `BRISK_create()`, `AKAZE_create()`, `KAZE_create()` 已被移除，
但 ORB 和 SIFT 仍可用。
