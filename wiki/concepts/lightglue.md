---
type: concept
title: LightGlue — 自适应特征匹配器
tags: [deep-learning, feature-matching, adaptive, iccv-2023]
related: [algorithm-benchmark-2026, aliked, xfeat]
created: 2026-07-18
updated: 2026-07-18
---

# LightGlue

## 概述

LightGlue 是 ICCV 2023 提出的端到端特征匹配器，具有动态提前退出机制，
能在匹配精度高和省算力之间取得平衡。它是一个**匹配器**而非检测器，
需要搭配 Detector 使用（如 SuperPoint, DISK, ALIKED, XFeat 等）。

## 在本项目中的角色

备选比对策略 — benchmark 中得分第三 (0.628)，但精度好、速度慢。

## 使用方式 (kornia)

**注意**: LightGlue 的输入是嵌套 dict 格式，不是简单的张量。

```python
import kornia.feature as KF

disk = KF.DISK.from_pretrained('depth', device=device).eval()
matcher = KF.LightGlue(features='disk').to(device).eval()

# 提取特征
q_feats = disk(query_tensor, n=4096, pad_if_not_divisible=True)
f_feats = disk(frame_tensor, n=4096, pad_if_not_divisible=True)

# LightGlue 输入格式 (嵌套 dict)
data = {
    'image0': {
        'keypoints': q_feats[0].keypoints.unsqueeze(0),   # (1, N, 2)
        'descriptors': q_feats[0].descriptors.unsqueeze(0), # (1, N, 128)
        'image': query_tensor,
    },
    'image1': {
        'keypoints': f_feats[0].keypoints.unsqueeze(0),
        'descriptors': f_feats[0].descriptors.unsqueeze(0),
        'image': frame_tensor,
    },
}

output = matcher(data)
# output['matches'] — list[(Si, 2)] 匹配索引对
# output['scores']  — list[(Si,)] 匹配置信度
```

## 支持的 Detector

`superpoint`, `disk`, `aliked`, `xfeat`, `dedodeb`, `dedodeg`, `sift`, `doghardnet`

## 性能特征

- **速度**: ~1000ms/帧 (MPS) — 最慢
- **匹配数**: ~46
- **置信度**: ~0.236

## 参考

- 论文: ICCV 2023
- GitHub: [cvg/LightGlue](https://github.com/cvg/LightGlue)
