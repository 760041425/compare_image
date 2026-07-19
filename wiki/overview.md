---
type: overview
title: Image Compare 项目概览
tags: [image-comparison, video-processing, python, xfeat, aliked, lightglue]
related: [algorithm-benchmark-2026, adr-001-xfeat-primary-strategy]
created: 2026-07-18
updated: 2026-07-18
---

# Image Compare — 项目概览

## 一句话描述

从视频中提取帧，与查询图片进行感知相似度比对，找到最匹配的帧。

## 领域模型（DDD 限界上下文）

```
┌─────────────────────────────────────────────────────────┐
│                    Image Compare System                  │
├──────────────┬──────────────────┬───────────────────────┤
│   Image      │   Comparison     │   Video               │
│   Context    │   Context        │   Context             │
├──────────────┼──────────────────┼───────────────────────┤
│ QueryImage   │ ComparisonEngine │ VideoSource           │
│ ImageFeature │ SimilarityResult │ FrameExtractor        │
│ KeypointSet  │ ComparisonStrategy│ FrameSequence        │
└──────────────┴──────────────────┴───────────────────────┘
                        │
              ┌─────────┴─────────┐
              │   Shared Kernel    │
              ├────────────────────┤
              │ ImageData (VO)     │
              │ SimilarityScore(VO)│
              │ MatchPair (VO)     │
              └────────────────────┘
```

**已验证的比对策略** (benchmark 2026-07-18):

| 策略 | 类型 | 综合评分 | 速度 |
|------|------|----------|------|
| **XFeat** (首选) | 深度学习检测+描述 | ⭐⭐⭐⭐⭐ | ~60ms/帧 |
| **ALIKED** | 深度学习检测+描述 | ⭐⭐⭐⭐ | ~175ms/帧 |
| **LightGlue+DISK** | 深度学习端到端匹配 | ⭐⭐⭐⭐ | ~1000ms/帧 |
| **ORB** | 传统特征点 | ⭐⭐⭐⭐ | ~15ms/帧 |

## 开发方法论

| 方法 | 用途 | 产物位置 |
|------|------|----------|
| SDD | 规格先行 | `specs/URD/`, `specs/PRD/`, `specs/ADD/` |
| DDD | 领域建模 | `docs/architecture/domain_model.md`, `wiki/entities/` |
| TDD | 测试驱动 | `tests/` (先于实现) |
| LLM Wiki | 知识编译 | `wiki/` (本目录) |

## 当前状态

- [x] 项目初始化（目录结构、配置）
- [x] URD/PRD 规格文档（草稿）
- [x] 领域模型设计（v0.1）
- [x] **算法 Benchmark** — 4 种算法对比，XFeat 胜出
- [ ] TDD 测试套件
- [ ] 帧提取模块正式实现
- [ ] 比对引擎正式实现（基于 XFeat）
- [ ] 集成测试
- [ ] CLI 工具

## 技术栈

- Python 3.13 (miniconda), torch 2.12, kornia 0.8.3, OpenCV 5.0, MPS (Apple Silicon)
- 关键依赖: kornia (内置 XFeat/ALIKED/LightGlue/DISK), opencv (ORB)
