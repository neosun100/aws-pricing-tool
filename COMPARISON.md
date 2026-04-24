# AWS Pricing Tool vs AWS Official MCP Server — 详细对比分析

## 1. 两个工具是什么

| | AWS 官方 `aws-pricing-mcp-server` | 本项目 `aws-pricing-tool` |
|---|---|---|
| 维护者 | AWS Labs（官方） | 社区（neosun100） |
| 定位 | 通用查价引擎 | 定价顾问（查价 + 分析 + 建议） |
| 安装 | `uvx awslabs.aws-pricing-mcp-server@latest` | `pip3 install boto3 fastmcp` + 本地运行 |
| 接口 | MCP only | CLI + MCP Server + AI Skill（3 种） |

## 2. 功能逐项对比

### 2.1 官方有、我们也有 ✅

| 功能 | 官方 | 本项目 | 说明 |
|------|------|--------|------|
| 实时查价 | ✅ | ✅ | 都调用 AWS Price List API |
| 多 Region 比价 | ✅ | ✅ | 都支持跨区对比 |
| 服务发现 | ✅ | ✅ | 都能列出可用服务和机型 |
| MCP 协议 | ✅ | ✅ | 都是标准 MCP Server |
| 自然语言查询 | ✅ | ✅ | 都支持 AI 自然语言交互 |

### 2.2 官方有、我们没有 ❌

| 功能 | 说明 | 是否值得做 |
|------|------|-----------|
| CDK/Terraform 扫描 | 扫描 IaC 代码自动识别服务和配置 | ❌ 不做。这是 IaC 工具的领域，用户可以同时配置两个 MCP Server |
| CSV/JSON 批量下载 | 下载完整定价数据集做离线分析 | ❌ 不做。我们有本地缓存，定位不同 |
| Well-Architected 建议 | 基于 AWS WAF 的优化建议 | ❌ 不做。太重，且官方做得更权威 |
| Docker 部署 | 容器化运行 | ⚠️ 可选。当前 `python3 mcp_server.py` 已经足够简单 |
| PyPI/uvx 发布 | `uvx` 一键安装 | ⚠️ 可选。未来可做 |

### 2.3 我们有、官方没有 🌟（核心差异化）

| 功能 | 说明 | 价值 |
|------|------|------|
| 🇨🇳 中文 Region 别名 | "东京" / "tokyo" / "ap-northeast-1" 三种输入 | 中文用户体验极大提升 |
| 🎯 19 服务精确 Filter 预设 | 用户只需说 `ec2 c6g.xlarge tokyo`，不需要知道 API filter 怎么写 | 官方需要用户自己构造 filter |
| ⚡ 7 天本地缓存 | 重复查询毫秒级响应 | 官方每次都调 API |
| 💻 独立 CLI 工具 | 不依赖 MCP 客户端，终端直接用 | 官方只有 MCP 模式 |
| 🤖 AI Skill（3 平台） | SKILL.md / CLAUDE_COMMAND.md / openclaw-skill/ | 官方没有 Skill 模式 |
| 📊 BOM 模板指导 | AI Skill 中内置完整 BOM 输出格式 | 官方没有 |
| 💡 Graviton 推荐 | AI Skill 自动建议 ARM 替代机型 | 官方没有 |
| 📈 RI 回本分析 | AI Skill 计算 break-even | 官方没有 |
| ⚠️ 隐藏成本提醒 | AI Skill 提醒 NAT/EIP/跨 AZ 等 | 官方没有 |
| 🧮 15+ 按用量服务公式 | S3/Lambda/DynamoDB 等内置计算 | 官方没有 |

## 3. 两者的关系

```
┌─────────────────────────────────────────────────────────┐
│                    用户的 AI 助手                         │
│              (Kiro / Claude Code / OpenClaw)              │
├─────────────────────┬───────────────────────────────────┤
│  aws-pricing-tool   │  AWS 官方 aws-pricing-mcp-server  │
│  (定价顾问)          │  (通用查价引擎)                    │
│                     │                                   │
│  ✅ 精确查价         │  ✅ 通用查价                       │
│  ✅ 中文别名         │  ✅ CDK/Terraform 扫描             │
│  ✅ 本地缓存         │  ✅ 批量数据下载                    │
│  ✅ BOM/Graviton/RI │  ✅ WAF 优化建议                   │
│  ✅ CLI 独立使用     │                                   │
├─────────────────────┴───────────────────────────────────┤
│                   AWS Price List API                      │
└─────────────────────────────────────────────────────────┘
```

**结论：互补关系，不是替代关系。**

- 想快速查某个机型的价格 → 用我们的工具（更简单、有缓存、支持中文）
- 想扫描 CDK/Terraform 项目估算成本 → 用官方工具
- 两个可以同时配置在同一个 MCP 客户端中，互不冲突

## 4. 推荐配置（同时使用两个）

```json
{
  "mcpServers": {
    "aws-pricing-tool": {
      "command": "python3",
      "args": ["/path/to/mcp_server.py"],
      "env": { "AWS_PROFILE": "your-profile" }
    },
    "awslabs.aws-pricing-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.aws-pricing-mcp-server@latest"],
      "env": { "AWS_PROFILE": "your-profile", "AWS_REGION": "us-east-1" }
    }
  }
}
```

AI 助手会根据用户的问题自动选择合适的工具：
- "c6g.xlarge 东京多少钱" → 调用 `aws-pricing-tool.query_pricing`
- "帮我扫描这个 CDK 项目的成本" → 调用 `awslabs.aws-pricing-mcp-server`

## 5. 当前项目完成度评估

| 维度 | 状态 | 说明 |
|------|------|------|
| 核心功能 | ✅ 完成 | 19 服务 × 34 Region × 7 价格点 |
| CLI 工具 | ✅ 完成 | query/batch/compare/list/regions/cache |
| MCP Server | ✅ 完成 | 6 个工具，所有 MCP 客户端通用 |
| AI Skill | ✅ 完成 | Kiro + Claude Code + OpenClaw 三平台 |
| 测试 | ✅ 完成 | 250 个测试（134 MCP + 81 unit + 35 E2E） |
| 文档 | ✅ 完成 | 英文 + 中文 README，CONTRIBUTING，ROADMAP |
| 安全 | ✅ 完成 | 无敏感信息泄露，.gitignore 覆盖完整 |
| CI/CD | ✅ 完成 | GitHub Actions，Python 3.8/3.10/3.12 |
| 版本管理 | ✅ 完成 | v1.3.0 + v1.5.0 + v2.0.0 + v2.1.0 六个里程碑 |

## 6. 是否还有优化空间？

### 已经到极限的部分
- 功能覆盖：19 个实例服务 + 15 个按用量服务 = 34 个服务，已覆盖绝大多数场景
- 平台支持：CLI + MCP + 3 平台 Skill = 5 种使用方式
- 测试覆盖：113 个测试，核心路径全覆盖

### 未来可选方向
- PyPI 发布（`pip install aws-pricing-tool`）
- Docker 镜像
- 集成 AWS Cost Explorer（分析实际账单，而非查价）
- Web UI 仪表板

### 已知限制
- AWS Price List API 对 Bedrock 模型价格更新有延迟，最新模型可能查不到。Bedrock 价格通过 SKILL.md 中的内置参考价表提供，需定期手动更新
- Partial Upfront RI 的预付金额无法从 Price List API 的 effective rate 中精确反推

**当前 v2.1.0 是这个项目的最新版本。**
