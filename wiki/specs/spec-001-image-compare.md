---
type: spec
title: SPEC-001 图像比对核心需求
tags: [spec, requirements]
related: [adr-001-xfeat-primary-strategy, algorithm-benchmark-2026]
created: 2026-07-18
updated: 2026-07-18
spec_id: SPEC-001
status: approved
priority: P0
---

# SPEC-001: 图像比对核心需求

## 来源

- `specs/URD/urd-001-image-compare.md` — 用户需求
- `specs/PRD/prd-001-image-compare.md` — 产品需求

## 核心需求摘要

1. **视频帧提取**: 按 1fps 从视频中均匀采样帧
2. **图片相似度比对**: 用可插拔策略比较查询图与视频帧
3. **结果排序和过滤**: 按综合分降序，支持阈值过滤
4. **CLI 接口**: 命令行一键运行
5. **结果可视化**: 匹配帧并排显示

## 已验证的技术方案

→ [[adr-001-xfeat-primary-strategy]]: XFeat 作为首选比对策略

| 策略 | 场景 |
|------|------|
| XFeat (默认) | 通用场景，平衡精度和速度 |
| ALIKED | 需要旋转鲁棒性时 |
| LightGlue | 精度优先，不计时间 |
| ORB | 纯 CPU / 资源受限 |

## 技术约束

- Python 3.11+ (实际运行在 3.13)
- MPS 加速 (Apple Silicon)
- 图片 resize 到 max 1024px 后比对
- 综合分 = 0.6×log1p(matches)/log1p(4096) + 0.4×confidence
