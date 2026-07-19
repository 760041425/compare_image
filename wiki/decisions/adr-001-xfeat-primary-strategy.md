---
type: adr
title: ADR-001 选择 XFeat 作为首选比对策略
tags: [architecture, xfeat, comparison-strategy]
related: [algorithm-benchmark-2026, xfeat, comparison-engine]
created: 2026-07-18
updated: 2026-07-18
status: accepted
deciders: [pangjinfu, claude]
---

# ADR-001: 选择 XFeat 作为首选比对策略

## 状态

**Accepted** (2026-07-18)

## 上下文

需要从视频中找出与查询图片最相似的帧。评估了 4 种算法方案：
- [[xfeat]] — 轻量深度学习特征检测+描述
- [[aliked]] — 轻量关键点检测网络
- [[lightglue]] — 自适应端到端匹配器 (搭配 DISK)
- [[orb]] — 传统 ORB 特征点

Benchmark 详见 [[algorithm-benchmark-2026]]。

## 决策

**选择 XFeat 作为首选 (default) 比对策略**，同时保留策略模式接口，允许切换其他算法。

## 理由

1. **综合得分最高** (0.767)，显著领先第二名 ALIKED (0.658)
2. **匹配数最多** (~668)，能捕获更多图像间的结构相似性
3. **速度可接受** (~60ms/帧)，在 Apple Silicon MPS 上实时可用
4. **kornia 内置**，无需额外安装依赖
5. **Benchmark 共识**: 4 种算法选出相同最佳帧，结果可信

## 备选方案

- **ALIKED**: 均衡但各方面不及 XFeat
- **LightGlue**: 精度好但太慢 (~1s/帧)，适合对精度有极端要求的场景
- **ORB**: 速度极快但匹配点太少，适合作为 fallback 或资源受限场景

## 后果

- 代码实现以 XFeat 为主要策略
- `ComparisonStrategy` 接口保持抽象，支持运行时切换
- 默认策略为 `XFeatStrategy`，用户可通过配置切换
