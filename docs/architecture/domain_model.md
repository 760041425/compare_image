# 领域模型 — Image Compare

## 版本: 0.2 (Benchmark Validated)
## 日期: 2026-07-18

---

## 限界上下文

### 1. Image Context (图像上下文)

负责图像的加载、预处理和特征提取。

```
QueryImage (实体)
├── path: str
├── image_data: ImageData (值对象)
├── hash: ImageHash (值对象, 可选)
├── features: List[ImageFeature] (值对象, 可选)
├── load() -> None
├── compute_hash(strategy: HashStrategy) -> ImageHash
└── extract_features(method: FeatureMethod) -> List[ImageFeature]

ImageData (值对象)
├── array: np.ndarray
├── width: int
├── height: int
├── channels: int
└── format: str

ImageHash (值对象)
├── value: int | str
├── algorithm: str  # "phash" | "dhash" | "ahash"
└── hamming_distance(other: ImageHash) -> int

ImageFeature (值对象)
├── keypoints: np.ndarray
├── descriptors: np.ndarray
└── method: str  # "orb" | "sift"
```

### 2. Comparison Context (比对上下文)

负责执行相似度计算和结果管理。

```
ComparisonEngine (领域服务)
├── strategy: ComparisonStrategy (策略接口)
├── compare(query: QueryImage, frames: FrameSequence) -> List[SimilarityResult]
└── rank(results: List[SimilarityResult]) -> List[SimilarityResult]

ComparisonStrategy (策略接口)
├── extract_features(image: ImageData) -> ImageFeature
├── match(query_feat: ImageFeature, frame_feat: ImageFeature) -> MatchResult
├── name: str
└── description: str

# 具体策略 (Benchmark 验证 2026-07-18)
XFeatStrategy : ComparisonStrategy     # 首选 ✅ score=0.767, ~60ms
ALIKEDStrategy : ComparisonStrategy    # 备选   score=0.658, ~175ms
LightGlueStrategy : ComparisonStrategy # 精度优先 score=0.628, ~1000ms
ORBStrategy : ComparisonStrategy       # 速度优先 score=0.611, ~15ms

SimilarityResult (实体)
├── query_image: QueryImage
├── matched_frame: VideoFrame
├── score: SimilarityScore (值对象)
├── frame_index: int
└── timestamp_ms: float

SimilarityScore (值对象)
├── value: float  # 0.0 ~ 1.0
├── algorithm: str
└── is_above_threshold(threshold: float) -> bool
```

### 3. Video Context (视频上下文)

负责视频加载和帧提取。

```
VideoSource (实体)
├── path: str
├── metadata: VideoMetadata (值对象)
├── load() -> None
└── get_frame_count() -> int

VideoMetadata (值对象)
├── fps: float
├── width: int
├── height: int
├── duration_seconds: float
├── frame_count: int
└── codec: str

FrameExtractor (领域服务)
├── mode: ExtractionMode  # UNIFORM | SCENE_CHANGE
├── interval_seconds: float
├── extract(source: VideoSource) -> FrameSequence
└── extract_key_frames(source: VideoSource) -> FrameSequence

FrameSequence (集合)
├── frames: List[VideoFrame]
├── __len__() -> int
├── __iter__() -> Iterator[VideoFrame]
└── filter_by_time_range(start: float, end: float) -> FrameSequence

VideoFrame (实体)
├── index: int
├── timestamp_ms: float
├── image_data: ImageData (值对象, 共享内核)
└── save(path: str) -> None
```

### 4. Shared Kernel (共享内核)

跨上下文共享的基础类型。

```
ImageData (值对象) — 被 Image/Video 上下文共用
SimilarityScore (值对象) — 被 Comparison 上下文定义，其他上下文使用
Config (配置) — 全局配置参数
```

## 上下文映射

```
Video Context ──[FrameSequence]──▶ Comparison Context
                                        │
Image Context ──[QueryImage]──────▶     │
                                        ▼
                                  SimilarityResult
```

## 设计模式

| 模式 | 应用位置 |
|------|----------|
| Strategy | ComparisonStrategy — 算法可插拔 |
| Repository | 帧序列的持久化（未来） |
| Value Object | ImageData, ImageHash, SimilarityScore |
| Domain Service | ComparisonEngine, FrameExtractor |
