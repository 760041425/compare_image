# Research Log

## 2026-07-18

- [WIKI] 项目创建，初始化 schema/purpose/overview
- [SDD] URD-001 草稿完成 — 用户需求文档
- [SDD] PRD-001 草稿完成 — 产品需求文档
- [DDD] 领域模型 v0.1 — 3 个限界上下文 (Image/Comparison/Video) + 共享内核
- [WIKI] schema 更新为 SDD+TDD+DDD 软件开发模式
- [CODE] Benchmark 脚本实现 — `scripts/benchmark_algorithms.py`
  - 4 种算法 (XFeat, ALIKED, LightGlue+DISK, ORB) 全量对比
  - 视频: 540x960, 30fps, 30.4s → 31 帧 (1fps 采样)
  - 查询图: 1279x1706, resize 到 max 1024px
  - 设备: Apple Silicon MPS
  - 结果: **4 种算法全部共识 Frame #510 (t=17.0s) 为最佳匹配**
  - XFeat 综合最优 (score=0.767, ~60ms/帧)
  - 修复: XFeat 需用 `from_pretrained()` 加载; `np.float64` 不能直接嵌入 JS
- [WIKI] 创建 comparison 页面: algorithm-benchmark-2026
- [WIKI] 创建 ADR: adr-001-xfeat-primary-strategy (accepted)
- [WIKI] 创建 concept 页面: xfeat, aliked, lightglue, orb
- [WIKI] 创建 entity 页面: query-image, video-frame, similarity-result, image-feature
- [SDD] PRD-001 更新 — 加入 benchmark 发现和算法选型结论
