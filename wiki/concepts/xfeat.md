---
type: concept
title: XFeat — 加速特征提取与匹配
tags: [deep-learning, feature-extraction, matching, cvpr-2024]
related: [xfeat, algorithm-benchmark-2026, adr-001-xfeat-primary-strategy]
created: 2026-07-18
updated: 2026-07-18
---

# XFeat (Accelerated Features)

## 概述

XFeat 是 CVPR 2024 提出的轻量级特征提取和匹配网络，专为实时场景设计。
同时完成关键点检测和描述符生成，输出 64 维描述符。

## 在本项目中的角色

**首选比对策略** — benchmark 中综合得分最高 (0.767)。

## 使用方式 (kornia)

```python
import kornia.feature as KF

detector = KF.XFeat.from_pretrained().to(device).eval()
features = detector.detectAndCompute(image_tensor)[0]
# features['keypoints']  — (N, 2) 像素坐标
# features['descriptors'] — (N, 64) L2 归一化
# features['scores']     — (N,) 置信度

distances, indices = KF.match_mnn(desc1, desc2)
```

## 性能特征

- **速度**: ~60ms/帧 (Apple Silicon MPS)
- **匹配数**: ~668 (本项目测试数据)
- **置信度**: ~0.676
- **GPU 依赖**: 可用 MPS/CUDA，CPU 也可运行

## 注意事项

- 必须用 `from_pretrained()` 加载，直接构造 `KF.XFeat()` 不会加载权重
- 输入张量格式: `(1, 3, H, W)` float32 [0,1]

## 参考

- 论文: "XFeat: Accelerated Features for Lightweight Image Matching" (CVPR 2024)
- GitHub: [verlab/accelerated_features](https://github.com/verlab/accelerated_features)
- kornia 集成: `kornia.feature.XFeat`
