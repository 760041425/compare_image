# PRD-001: Image Compare — 产品需求文档

## 版本: 0.2 (Benchmark Updated)
## 日期: 2026-07-18
## 关联: URD-001, Benchmark Report (reports/benchmark_report.html)

---

## 1. 产品概述

Image Compare 是一个 Python 库和 CLI 工具，用于从视频中提取帧并与查询图片进行感知相似度比对。

## 2. 功能需求

### F-001: 视频帧提取 [P0]
- 从视频文件中按指定间隔提取帧
- 支持均匀采样和场景变化检测两种模式
- 输出帧序列（内存或磁盘）

### F-002: 图片相似度比对 [P0]
- 支持多种比对策略（可插拔，Benchmark 验证 2026-07-18）:
  - **XFeat** (默认首选) — 深度学习特征检测+描述，综合最优
  - **ALIKED** — 轻量关键点检测，均衡备选
  - **LightGlue + DISK** — 端到端匹配，精度好但慢
  - **ORB** — 传统特征点，最快但匹配少
- 综合评分: `0.6 × log1p(matches)/log1p(4096) + 0.4 × confidence`
- 返回相似度分数 (0.0 ~ 1.0)

### F-003: 结果排序和过滤 [P0]
- 按相似度分数降序排列
- 支持阈值过滤
- 支持 Top-N 返回

### F-004: CLI 接口 [P0]
```bash
image-compare --query image.jpg --video video.mp4 --top 5 --threshold 0.7
```

### F-005: 结果导出 [P1]
- JSON 格式输出
- 可选保存匹配帧图片

### F-006: 结果可视化 [P1]
- 并排显示查询图和匹配帧
- 标注相似度分数

## 3. 非功能需求

| 需求 | 目标 |
|------|------|
| 性能 | 1 分钟视频 < 30s |
| 内存 | < 4GB |
| 可测试性 | 核心逻辑 > 90% 覆盖 |
| 可扩展性 | 比对策略可插拔 |

## 4. 接口设计

### Python API
```python
from image_compare import ImageComparator

comparator = ImageComparator(strategy="xfeat")  # 默认 XFeat, 可选 aliked/lightglue/orb
results = comparator.compare(
    query="path/to/query.jpg",
    video="path/to/video.mp4",
    top_n=5,
    threshold=0.5,
    extraction_fps=1.0,
)
for result in results:
    print(f"Frame #{result.frame_index} (t={result.timestamp_sec:.1f}s): "
          f"score={result.composite_score:.3f}, matches={result.num_matches}")
```

### CLI
```bash
image-compare compare \
    --query query.jpg \
    --video video.mp4 \
    --strategy xfeat \
    --top 5 \
    --threshold 0.5 \
    --fps 1.0 \
    --output results.json
```

## 5. Benchmark 发现 (2026-07-18)

已完成 4 种算法全量 Benchmark，详见 `reports/benchmark_report.html`。

| 算法 | 综合得分 | 匹配数 | 置信度 | 耗时 | 结论 |
|------|----------|--------|--------|------|------|
| XFeat | **0.767** | 668 | 0.676 | ~60ms | ✅ 首选 |
| ALIKED | 0.658 | 285 | 0.489 | ~175ms | 均衡备选 |
| LightGlue | 0.628 | 46 | 0.236 | ~1000ms | 精度优先 |
| ORB | 0.611 | 15 | 0.839 | ~15ms | 速度优先 |

**关键结论**: 4 种算法全部选出相同最佳帧 (#510)，结果高度一致。

## 6. 里程碑

| 阶段 | 内容 | 状态 |
|------|------|------|
| M0 | 项目初始化 + Benchmark | ✅ 完成 |
| M1 | 帧提取 + XFeat 比对 + CLI | 待开发 |
| M2 | 多策略 + 结果导出 | 待开发 |
| M3 | 可视化 + 性能优化 | 待开发 |
