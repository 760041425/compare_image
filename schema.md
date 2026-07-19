# Wiki Schema — SDD+TDD+DDD Software Development

## Page Types

| Type | Directory | Purpose |
|------|-----------|---------|
| entity | wiki/entities/ | 领域实体 (QueryImage, VideoFrame, SimilarityResult 等) |
| concept | wiki/concepts/ | 技术概念 (感知哈希, SSIM, 特征匹配, 关键帧提取等) |
| source | wiki/sources/ | 参考资料 (论文, 文档, API 参考) |
| spec | wiki/specs/ | 规格文档摘要 (URD/PRD/ADD 的关键决策) |
| adr | wiki/decisions/ | 架构决策记录 (Architecture Decision Records) |
| comparison | wiki/comparisons/ | 方案对比 (算法 A vs B, 架构选型等) |
| test-strategy | wiki/test-strategies/ | 测试策略和覆盖分析 |
| synthesis | wiki/synthesis/ | 跨切面的总结和洞察 |
| overview | wiki/ | 项目全局概览 |

## Naming Conventions

- Files: `kebab-case.md`
- Entities: 匹配领域模型类名 (e.g., `query-image.md`, `video-frame.md`)
- Concepts: 描述性名词短语 (e.g., `perceptual-hash.md`, `ssim.md`)
- Sources: `author-year-slug.md` (e.g., `opencv-2024-docs.md`)
- Specs: `spec-XXX-slug.md` (e.g., `spec-001-frame-extraction.md`)
- ADRs: `adr-NNN-slug.md` (e.g., `adr-001-use-phash.md`)
- Comparisons: `X-vs-Y.md` (e.g., `phash-vs-ssim.md`)
- Test strategies: `test-strategy-slug.md` (e.g., `test-strategy-comparison.md`)

## Frontmatter

All pages must include YAML frontmatter:

```yaml
---
type: entity | concept | source | spec | adr | comparison | test-strategy | synthesis | overview
title: Human-readable title
tags: []
related: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

Entity pages also include:
```yaml
bounded_context: image | comparison | video | shared
attributes: []
behaviors: []
```

ADR pages also include:
```yaml
status: proposed | accepted | deprecated | superseded
deciders: []
```

Spec pages also include:
```yaml
spec_id: SPEC-XXX
status: draft | reviewed | approved | implemented
priority: P0 | P1 | P2
```

## Index Format

`wiki/index.md` lists all pages grouped by type:
```
## Entities
- [[page-slug]] — one-line description (bounded context)

## Concepts
- [[page-slug]] — one-line description

## ADRs
- [[adr-NNN-slug]] — decision summary [status]

## Specs
- [[spec-XXX-slug]] — spec summary [status]
```

## Log Format

`wiki/log.md` records activity in reverse chronological order:
```
## YYYY-MM-DD

- [SDD] spec-XXX drafted / reviewed / approved
- [TDD] tests written for XXX
- [DDD] domain model updated: added XXX
- [WIKI] updated entity page: XXX
- [CODE] implemented XXX
```

## Cross-referencing Rules

- Use `[[page-slug]]` syntax to link between wiki pages
- Entity pages link to their bounded context and related specs
- ADR pages link to the comparison pages that informed the decision
- Spec pages link to relevant entity pages and ADRs
- Test strategy pages link to the specs they verify
- Every page should appear in `wiki/index.md`

## SDD ↔ Wiki Integration

When a spec is written in the code project (`specs/`):
1. Create a summary page in `wiki/specs/`
2. Update `wiki/index.md`
3. Create or update affected entity pages in `wiki/entities/`
4. Log the activity in `wiki/log.md`

## TDD ↔ Wiki Integration

When tests are written:
1. Update the relevant test strategy page
2. Note test coverage decisions
3. Log in `wiki/log.md`

## DDD ↔ Wiki Integration

When the domain model changes:
1. Update entity pages for new/modified entities
2. Update concept pages for new patterns/strategies
3. Create comparison pages if design alternatives were considered
4. Update overview page if bounded contexts change

## Contradiction Handling

When design decisions conflict:
1. Note the contradiction in relevant pages
2. Create an ADR to track the resolution
3. Link all related pages
4. Resolve in a synthesis page once decided
