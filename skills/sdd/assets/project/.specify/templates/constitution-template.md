# [PROJECT_NAME] 宪章
<!-- 示例：Spec 宪章、TaskFlow 宪章等。 -->

## 核心原则

### [PRINCIPLE_1_NAME]
<!-- 示例：I. 库优先 -->
[PRINCIPLE_1_DESCRIPTION]
<!-- 示例：复用优先：先扩展同类/同模块现有实现；只有 `NM-###` 证明无合适复用点并获批准时才新增抽象；禁止仅为组织代码而创建库。 -->

### [PRINCIPLE_2_NAME]
<!-- 示例：II. CLI 接口 -->
[PRINCIPLE_2_DESCRIPTION]
<!-- 示例：每个库都通过 CLI 暴露能力；文本输入/输出协议：stdin/args → stdout，错误 → stderr；同时支持 JSON 与人类可读格式。 -->

### [PRINCIPLE_3_NAME]
<!-- 示例：III. 测试优先（不可妥协） -->
[PRINCIPLE_3_DESCRIPTION]
<!-- 示例：强制 TDD：先编写测试 → 用户批准 → 确认测试失败 → 再实现；严格执行红灯—绿灯—重构循环。 -->

### [PRINCIPLE_4_NAME]
<!-- 示例：IV. 集成测试 -->
[PRINCIPLE_4_DESCRIPTION]
<!-- 示例：必须重点进行集成测试的领域：新库契约测试、契约变更、服务间通信、共享 schema。 -->

### [PRINCIPLE_5_NAME]
<!-- 示例：V. 可观测性、VI. 版本与破坏性变更、VII. 简洁性 -->
[PRINCIPLE_5_DESCRIPTION]
<!-- SDD_BROWNFIELD_SAFETY_V1:constitution-template -->
<!-- 示例：兼容与回归安全（不可妥协）：优先复用同类/同项目现有实现；新需求不得破坏 PB-### 既有行为；Bug 修复必须先复现、最小修复并通过相邻与完整回归验证。 -->

## [SECTION_2_NAME]
<!-- 示例：附加约束、安全要求、性能标准等。 -->

[SECTION_2_CONTENT]
<!-- 示例：技术栈要求、合规标准、部署政策等。 -->

## [SECTION_3_NAME]
<!-- 示例：开发工作流、审查流程、质量关卡等。 -->

[SECTION_3_CONTENT]
<!-- 示例：代码审查要求、测试关卡、部署审批流程等。 -->

## 治理
<!-- 示例：本宪章优先于所有其他实践；修订必须有文档、批准和迁移计划。 -->

[GOVERNANCE_RULES]
<!-- 示例：所有 PR/审查都必须验证合规性；复杂度必须得到论证；运行时开发指南见 [GUIDANCE_FILE]。 -->

**版本**：[CONSTITUTION_VERSION] | **批准日期**：[RATIFICATION_DATE] | **最后修订**：[LAST_AMENDED_DATE]
<!-- 示例：版本：2.1.1 | 批准日期：2025-06-13 | 最后修订：2025-07-16 -->
