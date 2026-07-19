# Project Purpose — Image Compare

## 项目目标

构建一个图像/视频比对系统：从视频中提取帧，与查询图片进行相似度匹配，找到最相似的帧。

## 核心问题

> 给定一张查询图片和一段视频，如何高效地找到视频中与查询图片最相似的帧？

## 背景

- 用户有查询图片（query_image/）和视频数据（data/）
- 需要自动化的帧提取和相似度比对流程
- 结果需要可视化展示

## 子问题

1. 如何从视频中高效抽帧？（关键帧 vs 均匀采样）
2. 使用什么相似度算法？（pHash / SSIM / 特征匹配 / 深度学习嵌入）
3. 如何组织领域模型使算法可插拔？
4. 如何输出和可视化比对结果？

## 范围

**In scope:**
- 视频帧提取（均匀采样 + 场景变化检测）
- 多种相似度比对策略（可插拔）
- 比对结果排序和可视化
- CLI 和 Python API

**Out of scope:**
- 实时视频流处理
- Web UI / REST API（v2）
- 分布式处理

## 开发方法论

SDD + TDD + DDD + LLM Wiki:
- **SDD**: 先写规格，再写代码
- **DDD**: 领域模型驱动代码结构
- **TDD**: 先写测试，再写实现
- **LLM Wiki**: 知识编译，持续维护结构化文档

## 技术栈

- Python 3.11+
- OpenCV (视频处理 + 图像处理)
- imagehash (感知哈希)
- scikit-image (SSIM 等)
- pytest (测试)
- Pydantic (数据模型)

## 当前状态

> 项目初始化阶段 — 目录结构已创建，开始编写规格文档。

## Code 仓库

- 代码路径: `/Users/pangjinfu/code/compare_image`
- Wiki 路径: `/Users/pangjinfu/Documents/llm_wiki/image_compare/image_compare`
