# Unimage: Next-Generation Capability-Based Generative Media Runtime Layer (CMRL)
## Technical Architecture & Research Specification Whitepaper

> **Version**: 0.1.0-alpha  
> **Status**: Conceptual Blueprint & Core Engine Specification  
> **Target Audience**: AI Infrastructure Architects, Multimodal Agent Developers, Systems Engineers

---

## 1. 核心论点与范式革命 (The Paradigm Shift)

### 1.1 破除迷信：为什么做“图片版 One-API / NewAPI”是死路？

当前 LLM 领域的成功使得许多工程团队产生路径依赖，试图复制 `POST /v1/images/generations` 的模式，把 OpenAI、Gemini、Midjourney、Flux、fal.ai 做一层薄薄的参数映射。这种做法存在根本性的系统级缺陷：

1. **一维离散 Token 流 vs 高维流形变换（Manifold Transformation）**  
   - LLM 处理的是一维离散序列（$Token_{t+1} \sim P(Token | Context)$），语义和参数高度对称（`prompt`, `temperature`, `max_tokens`）。
   - 视觉生成本质是多维潜空间上的扩散/流匹配随机微分方程（SDE/ODE 求解）。不同模型的潜空间（Latent Space）几何结构完全不同（如 SD1.5 的 4 通道 8x 下采样 vs SD3 的 16 通道 8x 下采样 vs Flux 的 Rectified Flow）。
2. **复合工作流（Composite Pipeline）vs 单次前向推理（Single Forward Pass）**  
   - 工业级生图生视频从不依赖单次调用。一次高质量的人像生成通常是：`Prompt 增强 -> 基础扩散采样 -> 局部面部检测与 Mask -> LoRA/IP-Adapter 面部特征注入 -> 引导度退火局部重绘 -> 超分重建`。
   - 简单的 API 聚合器只能把这个复杂度推卸给客户端；一旦客户端自己实现这套胶水代码，就立即与特定模型强耦合。
3. **状态黑盒（The State Dilemma）与像素级往返损耗**  
   - 当前 API 每次交互都把中间结果编码为 PNG/JPEG 传输，丢失了潜向量、注意力图（Cross-Attention Maps）、随机种子分布。多轮编辑时反复解码/重编码，造成不可逆的高频信息衰减与风格漂移。
4. **失败语义与非确定性补偿（Stochastic Failure & Non-deterministic Recovery）**  
   - LLM 的失败通常是超时或格式错误（可幂等重试）。
   - 生成式媒体的失败多是“局部质量崩溃”（手指畸形、人脸漂移、文字乱码）。如果只能通过 `Retry()` 重新跑整个流程，不仅算力浪费极大，而且破坏了画面中原本令人满意的背景和光影。

### 1.2 核心主张：声明式意图编译与运行时（Declarative Intent & Media Runtime）

Unimage 的设计哲学借鉴了现代数据库（如 Relational Algebra / Catalyst Optimizer）与分布式容错系统（如 Temporal / Nervipulsa Saga）：

* **调用端（Agent/App）声明“目标与 SLA 约束”**，而不是挑选具体模型。
* **控制面（Compiler & Planner）** 将声明式意图编译为带类型检查的逻辑执行图（Logical Plan），再根据算力成本、延迟、质量 SLA 特化为物理执行图（Physical DAG）。
* **执行面（Runtime Engine）** 统一调度异构算力（Cloud APIs + Self-hosted ComfyUI Workers），维护跨步骤的中间状态与 Latent 缓存。
* **反馈面（Evaluator & Saga Compensator）** 执行自动化的视觉问答/特征检验；一旦局部未达标，触发局部重绘或降级补偿，而非整图推倒重来。

---

## 2. 业界代表方案解构与生态断层

```
+---------------------------------------------------------------------------------+
|                                 APPLICATION LAYER                               |
|        (Autonomous Agents, Creative Co-pilots, Game Gen, Dynamic Ads)          |
+---------------------------------------------------------------------------------+
                                      |
                      [ The Missing Runtime Layer: UNIMAGE ]
                      - Declarative CDMP Protocol
                      - Dynamic Workflow Synthesis (Intent -> DAG)
                      - Latent & Context State Mesh
                      - Saga Transactional Quality Compensation
                                      |
+--------------------------+----------------------------+-------------------------+
|    Serverless Model APIs |  Interactive Graph Engines |  Raw Compute Primitives |
|  (fal.ai, Replicate,     |  (ComfyUI, WebUI, Diffusers|  (RunPod, Modal,        |
|   OpenAI, Gemini)        |   Workflows)               |   Local GPU Clusters)   |
+--------------------------+----------------------------+-------------------------+
```

### 2.1 详细对比矩阵

| 架构维度 | OpenRouter / NewAPI | fal.ai / Replicate | ComfyUI 生态 | **Unimage (本方案)** |
| :--- | :--- | :--- | :--- | :--- |
| **抽象层级** | 简单参数映射（Model-Centric） | Serverless 容器与模型端点 | 手工节点连线（Imperative DAG） | **声明式能力意图（Intent-Centric）** |
| **工作流生成** | 无（仅单模型调用） | 静态固定管道（Fixed Chaining） | 极客手动配置，换模型即崩塌 | **动态多智能体图编译器（Logical -> Physical DAG）** |
| **状态维护** | 无状态（Stateless） | 仅提供中间临时 URL | 本地内存暂存，无法跨集群扩展 | **分布式 Latent/Mask/Embedding 状态网格** |
| **一致性保障** | 无 | 依赖调用方上传参考图 | 节点中挂载 IP-Adapter/PuLID | **原生 SLA 约束与自动化补偿修补循环** |
| **失败处理** | HTTP 重试（整图重跑） | 任务排队失败重试 | 中断报错，需人工排查节点 | **Saga 局部补偿（Targeted Inpainting Patch）** |

---

## 3. 协议规范：CDMP (Capability-based Declarative Media Protocol)

### 3.1 核心数据结构

CDMP 协议包含 4 个核心构件：
1. **`Intent` (意图)**: 用户希望完成的语义动作（生成、角色修改、风格迁移、局部重置、外扩扩展等）。
2. **`Anchors` (锚点)**: 跨步骤必须保留的先验约束（人脸特征、几何深度、线稿、调色板、语义文字）。
3. **`Requirements` (SLA 要求)**: 预算（Max Cost）、延迟上限（Max Latency）、保真度阈值、分辨率。
4. **`LifecyclePolicy` (生命周期与故障策略)**: 是否保留潜向量缓存、失败时是否允许自动修补。

### 3.2 规范定义 (JSON Schema 示例)

```json
{
  "$schema": "https://unimage.dev/schema/cdmp-v1.json",
  "task": "character_consistent_edit",
  "intent": {
    "action": "scene_transfer",
    "prompt": "把女孩置于暴雨倾盆的赛博朋克夜市中，手持一把半透明光剑",
    "negative_prompt": "mutated fingers, extra limbs, low resolution, blurry"
  },
  "anchors": [
    {
      "id": "char_primary_face",
      "type": "identity",
      "source_url": "s3://assets/character_master_01.png",
      "target_region": "face",
      "fidelity_level": "strict"
    }
  ],
  "requirements": {
    "dimensions": { "width": 1280, "height": 720 },
    "max_cost_cents": 5.0,
    "max_latency_ms": 6000,
    "quality_thresholds": {
      "face_similarity": 0.85,
      "aesthetic_score": 0.75
    }
  },
  "lifecycle_policy": {
    "cache_intermediate_latents": true,
    "allow_saga_repair": true,
    "max_repair_passes": 2
  }
}
```

---

## 4. Unimage 核心子系统架构

### 4.1 能力拓扑注册表 (Capability Registry)
注册表并不记录简单的“模型名称”，而是维护高维能力的特征向量：
- `IdentityPreservation`: [0.0 - 1.0] (结合 PuLID / IP-Adapter 时的面部一致性能力)
- `TextRenderingFidelity`: [0.0 - 1.0] (图像中渲染印刷级排版文字的能力，如 Flux/Ideogram 显著高于 SDXL)
- `SpatialControl`: 支持 Canny / Depth / Pose 的精度
- `ExecutionCost`: 每次调用的美分成本与典型推理时间 (ms)
- `NativeResolutionRange`: 适配的分辨率桶

### 4.2 动态工作流编译器 (Dynamic Workflow Compiler)
编译器采用两阶段规划：
1. **Logical Planning (逻辑计划)**:  
   将用户意图分解为标准的语义操作符序列：  
   `ParseIntent -> AnchorIdentity -> SynthesizeBaseCanvas -> VerifyFaceSimilarity -> ConditionalPatch -> SuperRes`
2. **Physical Planning & Optimization (物理计划与 Pareto 优化)**:  
   根据当前节点的可用算力健康度、成本上限和延迟要求选择具体的执行路径：
   - *高速路径 (Fast Cloud Path)*: Flux-Schnell (via fal.ai) + 快速云端面部微调
   - *高保真路径 (High Fidelity Local Path)*: 本地 ComfyUI Worker (SDXL/Flux + PuLID + ControlNet + 4x-UltraSharp)
   - *应急回退路径 (Fallback Path)*: OpenAI DALL-E 3 / Google Imagen 3

### 4.3 Saga 事务性自愈补偿器 (Saga Generative Compensator)
结合 Nervipulsa 的状态机与事务思想：
- **Check-point**: 基础扩散生成完成后，中间生成的图像与潜空间向量保存至内存/快速存储。
- **Evaluation Gate**: 轻量级评估器（基于 FaceNet/ArcFace 向量余弦距离或 CLIP 相似度）打分。
- **Conditional Branching**:
  - 若 `Similarity >= 0.85`: 直接进入超分与交付流程；
  - 若 `Similarity < 0.85`: 触发**补偿事务（Compensating Action）**。裁剪面部边界框，生成软羽化 Mask，调度局部重绘适配器（Inpaint Repair Worker）注入原图 Face Embedding 执行局部降噪微调（Denoise = 0.35）。
- 避免因局部缺陷而重新支付 100% 的推理成本。

---

## 5. 项目结构与交付规划

```
Unimage/
├── docs/
│   └── ARCHITECTURE_SPEC.md       # 本架构白皮书
├── unimage/
│   ├── protocol/                  # 声明式协议定义 (CDMP)
│   │   ├── schema.py              # Pydantic v2 模型
│   │   └── types.py               # 枚举与核心常量
│   ├── registry/                  # 能力注册表与模型特征矩阵
│   │   ├── capability_matrix.py   # 模型能力维度评分
│   │   └── providers.py           # 算力提供商注册定义
│   ├── compiler/                  # 图编译器与优化器
│   │   ├── planner.py             # 逻辑图生成器
│   │   └── optimizer.py           # Pareto 成本/延迟/SLA 优化器
│   ├── runtime/                   # 执行运行时与补偿调度
│   │   ├── engine.py              # 异步 DAG 执行引擎
│   │   ├── state_store.py         # 跨步骤中间资产与 Latent 缓存
│   │   └── saga_compensator.py    # 质量门禁与局部自动修补
│   ├── evaluator/                 # 视觉质量与特征评估器
│   │   └── quality_checker.py     # 人脸一致性/CLIP/美学评分抽象
│   ├── adapters/                  # 异构模型适配器
│   │   ├── base.py                # 统一适配器接口
│   │   ├── mock_adapter.py        # 本地确定性仿真适配器（测试与体验）
│   │   ├── fal_adapter.py         # fal.ai 驱动
│   │   └── comfy_adapter.py       # ComfyUI 驱动
│   └── api/                       # HTTP/WebSocket 网关服务
│       └── server.py              # FastAPI 声明式接口服务
├── examples/
│   └── run_declarative_pipeline.py# 端到端运行演示
├── pyproject.toml
└── README.md
```
