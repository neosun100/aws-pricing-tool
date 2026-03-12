# v1.4.0 Roadmap — MCP Server + Multi-Platform Enhancement

## 背景

AWS 官方已发布 `aws-pricing-mcp-server`（awslabs），OpenClaw 原生支持 MCP 协议。
当前项目通过 shell 调用 CLI 的方式集成 OpenClaw，但 MCP 是更原生、更强大的集成方式。

v1.4.0 的核心目标：**将 pricing_tool.py 封装为 MCP Server**，让 Kiro / Claude Code / OpenClaw / Cursor / VS Code 等所有 MCP 客户端都能直接调用，无需 shell 中转。

---

## 架构对比

### 当前 v1.3.0（Shell 调用）
```
用户 → AI Agent → shell.exec("python3 pricing_tool.py ...") → 解析文本输出
```
- 需要每个平台单独适配（SKILL.md / CLAUDE_COMMAND.md / openclaw-skill/）
- 输出是文本，需要 AI 解析
- 无法利用 MCP 的工具发现、schema 验证等能力

### 目标 v1.4.0（MCP Server）
```
用户 → AI Agent → MCP Client → aws-pricing-mcp-server → AWS Price List API
                              → pricing-tool-mcp-server → 本地计算 + API
```
- 一个 MCP Server 适配所有平台（Kiro / Claude Code / OpenClaw / Cursor / VS Code）
- 结构化 JSON 输入输出，AI 直接理解
- 支持工具发现（agent 自动知道有哪些能力）
- 与 AWS 官方 MCP Server 互补（官方不含 BOM/Graviton 推荐/RI 回本分析）

---

## TODO List

### P0 — MCP Server 核心（必做）

- [ ] **创建 `mcp_server.py`** — 基于 FastMCP (Python) 封装 pricing_tool.py 的核心函数为 MCP tools
  - `query_pricing` — 查询单个实例价格
  - `batch_compare` — 批量对比同 Region 多机型
  - `compare_regions` — 跨 Region 比价
  - `list_types` — 列出可用机型
  - `calculate_usage` — 按用量服务计算（S3/Lambda/DynamoDB 等内置公式）
  - `get_regions` — 列出支持的 34 个 Region
- [ ] **MCP Server 配置文件** — 提供 Kiro / Claude Code / OpenClaw / Cursor / VS Code 的 mcp.json 配置示例
- [ ] **pyproject.toml / setup.py** — 支持 `uvx aws-pricing-tool@latest` 或 `pip install` 安装
- [ ] **测试** — MCP Server 的单元测试（mock AWS API，验证 tool schema 和返回格式）

### P1 — 差异化功能（与 AWS 官方 MCP Server 互补）

AWS 官方 `aws-pricing-mcp-server` 提供基础查价能力，但缺少以下功能：

- [ ] **完整 BOM 生成** — 计算+存储+IOPS+数据传输+备份+隐藏成本，一键汇总
- [ ] **Graviton 推荐** — 自动检测 x86 机型，建议 ARM 替代并计算节省比例
- [ ] **RI 回本分析** — break-even 计算，对比 OD/RI 1yr/RI 3yr/Savings Plans
- [ ] **隐藏成本提醒** — NAT Gateway、EIP、跨 AZ 流量、CloudWatch 等
- [ ] **架构模式** — 多服务组合报价（EC2 + Aurora + Redis），汇总总 BOM
- [ ] **中文 Region 别名** — 支持 "东京" / "tokyo" / "ap-northeast-1" 三种输入
- [ ] **15+ 按用量服务内置公式** — S3/Lambda/DynamoDB/CloudFront/API Gateway 等无需 API 调用

### P2 — 平台适配

- [ ] **OpenClaw MCP 配置** — `openclaw.json` 中添加 MCP server 配置，替代当前 shell skill
- [ ] **Kiro MCP 配置** — `~/.kiro/settings/mcp.json` 配置示例
- [ ] **Claude Code MCP 配置** — `.claude/settings/mcp.json` 配置示例
- [ ] **Docker 支持** — Dockerfile，支持 `docker run` 方式运行 MCP Server
- [ ] **保留向后兼容** — 现有 CLI / SKILL.md / CLAUDE_COMMAND.md / openclaw-skill/ 继续可用

### P3 — 文档与发布

- [ ] **README 更新** — 添加 MCP Server 安装和配置说明（5 个平台的配置示例）
- [ ] **README_CN 同步更新**
- [ ] **CONTRIBUTING.md 更新** — MCP Server 开发指南
- [ ] **Changelog 更新** — v1.4.0 记录
- [ ] **GitHub Release** — 打 tag v1.4.0
- [ ] **PyPI 发布**（可选）— 支持 `pip install aws-pricing-tool` 或 `uvx` 安装

---

## MCP Server 技术方案

### 依赖
```
fastmcp>=2.0.0
boto3>=1.26.0
```

### Tool Schema 示例
```python
@mcp.tool()
def query_pricing(
    service: str,       # ec2, rds, elasticache, opensearch, ...
    instance_type: str,  # c6g.xlarge, db.r6g.xlarge, ...
    region: str,         # tokyo, ap-northeast-1, 东京
    engine: str = None,  # aurora-mysql, redis, ...
    deployment: str = None,  # Multi-AZ
    os: str = "Linux",
) -> dict:
    """Query real-time pricing for an AWS instance type.
    Returns On-Demand + 6 RI options (1yr/3yr × No/Partial/All Upfront).
    Supports 19 services × 34 regions. Region accepts Chinese/English/code."""
```

### MCP 客户端配置示例（通用）
```json
{
  "mcpServers": {
    "aws-pricing-tool": {
      "command": "uvx",
      "args": ["aws-pricing-tool@latest"],
      "env": {
        "AWS_PROFILE": "your-profile",
        "AWS_REGION": "us-east-1"
      }
    }
  }
}
```

---

## 与 AWS 官方 MCP Server 的定位差异

| 能力 | AWS 官方 aws-pricing-mcp-server | 本项目 aws-pricing-tool |
|------|-------------------------------|------------------------|
| 基础查价 | ✅ | ✅ |
| 服务发现 | ✅ | ✅ |
| CDK/Terraform 扫描 | ✅ | ❌ |
| CSV/JSON 批量下载 | ✅ | ❌ |
| 中文 Region 别名 | ❌ | ✅ |
| 完整 BOM 生成 | ❌ | ✅ |
| Graviton 推荐 | ❌ | ✅ |
| RI 回本分析 | ❌ | ✅ |
| 隐藏成本提醒 | ❌ | ✅ |
| 架构模式报价 | ❌ | ✅ |
| 按用量服务公式 | ❌ | ✅（15+ 服务） |
| 本地缓存 | ❌ | ✅（7 天 TTL） |
| 零依赖 CLI | ❌ | ✅ |

**定位：AWS 官方做"查价引擎"，本项目做"定价顾问"。**

---

## 时间线估算

| 阶段 | 内容 | 预估 |
|------|------|------|
| Phase 1 | MCP Server 核心 + 测试 | 2-3 天 |
| Phase 2 | 差异化功能（BOM/Graviton/RI） | 1-2 天 |
| Phase 3 | 5 平台配置 + Docker | 1 天 |
| Phase 4 | 文档 + 发布 | 1 天 |

---

## 参考资料

- AWS 官方 MCP Server: https://awslabs.github.io/mcp/servers/aws-pricing-mcp-server
- AWS Billing MCP Server: https://aws.amazon.com/blogs/aws-cloud-financial-management/aws-announces-billing-and-cost-management-mcp-server/
- FastMCP (Python): https://github.com/jlowin/fastmcp
- OpenClaw MCP 集成: https://docs.openclaw.ai (MCP 原生支持)
- MCP 协议规范: https://modelcontextprotocol.io
