# AWS Pricing Tool 🏷️

[English](README.md) | 中文

<p align="center">
  <img src="logo.png" alt="AWS Pricing Tool" width="200">
</p>

> 一条命令查询 AWS 任意服务的实时价格，支持 **19 个服务** × **34 个 Region** × **6 种 RI 方案**。

```bash
pip3 install boto3
python3 pricing_tool.py --version                                          # v2.0.0
python3 pricing_tool.py --profile <your-profile> query ec2 -t c6g.xlarge -r 东京
```

---

## ✨ 功能亮点

- 🌏 **34 个 Region** — 中英文别名随意输入（`东京` / `tokyo` / `ap-northeast-1`）
- 💰 **7 种价格** — On-Demand + 6 种 RI（1yr/3yr × No/Partial/All Upfront）
- 📊 **4 种命令** — `query` 单查 / `batch` 批量 / `compare` 跨区比价 / `list` 列机型
- 📤 **3 种输出** — 终端彩色表格 / `--json` / `--csv`
- ⚡ **本地缓存** — 7 天 TTL，重复查询毫秒级响应
- 🔌 **模块化** — 可 `import pricing_tool` 程序化调用，所有函数返回结构化数据
- 🤖 **Kiro Skill** — 自然语言查价，AI 自动生成完整 BOM 报价单

---

## 🤖 AI Skill 安装与使用

本工具可作为 AI 编程助手的 Skill 使用，支持 **Kiro CLI**、**Claude Code** 和 **OpenClaw** 三个平台。让 AI 成为你的 AWS 定价顾问——用自然语言查价，自动生成完整 BOM。

### 📺 视频教程

![视频教程](aws-pricing-skill-tutorial-v3.mp4)

### 安装方式 A：Kiro CLI

```bash
# 1. 克隆项目并安装依赖
git clone https://github.com/neosun100/aws-pricing-tool.git ~/Code/aws-pricing-tool
pip3 install boto3

# 2. 安装 Skill
mkdir -p ~/.kiro/skills/aws-pricing-query
cp ~/Code/aws-pricing-tool/SKILL.md ~/.kiro/skills/aws-pricing-query/SKILL.md

# 3. 编辑配置（修改工具路径和 AWS Profile）
#    打开 ~/.kiro/skills/aws-pricing-query/SKILL.md
#    修改: 工具: /your/path/to/pricing_tool.py
#    修改: 凭证: --profile your-profile
```

Kiro 中直接用自然语言查价，Skill 会自动匹配关键词触发：
```
👤 c6g.xlarge 东京多少钱
```

### 安装方式 B：Claude Code

```bash
# 1. 克隆项目并安装依赖
git clone https://github.com/neosun100/aws-pricing-tool.git ~/Code/aws-pricing-tool
pip3 install boto3

# 2. 安装为全局 Slash Command
mkdir -p ~/.claude/commands
cp ~/Code/aws-pricing-tool/CLAUDE_COMMAND.md ~/.claude/commands/aws-pricing.md

# 3. 编辑配置（修改工具路径和 AWS Profile）
#    打开 ~/.claude/commands/aws-pricing.md
#    修改: 工具: /your/path/to/pricing_tool.py
#    修改: 凭证: --profile your-profile
```

Claude Code 中用 Slash Command 调用：
```
/user:aws-pricing c6g.xlarge 东京多少钱
```

### 安装方式 C：OpenClaw

```bash
# 1. 克隆项目并安装依赖
git clone https://github.com/neosun100/aws-pricing-tool.git ~/Code/aws-pricing-tool
pip3 install boto3

# 2. 安装 Skill
cp -r ~/Code/aws-pricing-tool/openclaw-skill ~/.openclaw/skills/aws-pricing-query

# 3. 编辑配置（修改工具路径和 AWS Profile）
#    打开 ~/.openclaw/skills/aws-pricing-query/skill.md
#    修改: Tool path → /your/path/to/pricing_tool.py
#    修改: AWS profile → --profile your-profile
#    同时修改 index.js 中的 TOOL_PATH 和 AWS_PROFILE
```

OpenClaw 中直接用自然语言查价：
```
👤 c6g.xlarge 东京多少钱
```

### 安装后配置

无论哪个平台，安装后都需要编辑对应文件，修改以下两行：

```yaml
工具: /your/path/to/pricing_tool.py   # ← 改为你的实际路径
凭证: --profile <your-profile>        # ← 改为你的 AWS Profile
```

### 自然语言使用示例

```
👤 c6g.xlarge 东京多少钱
🤖 → 自动查询 EC2 价格，输出 OD + 6 种 RI，附 Graviton 建议

👤 2台 Aurora MySQL db.r6g.xlarge 东京 Multi-AZ 500G
🤖 → 完整 BOM：实例费 + 存储费 + I/O + 备份 + 数据传输

👤 帮我算个架构：2台c6in.4xlarge + Aurora db.r6g.xlarge + Redis cache.r6g.large 东京
🤖 → 架构模式：逐个服务查询，汇总多层 BOM，附优化建议

👤 对比东京和弗吉尼亚的 c6g.xlarge
🤖 → 跨 Region 比价，★ 标注最便宜

👤 S3 存 10TB Standard，每月 100 万次 GET
🤖 → 按用量计算（内置公式，无需 API）

👤 RI 多久回本？
🤖 → break-even 分析 + Savings Plans 对比
```

### Skill 覆盖范围

| 类型 | 服务数 | 查询方式 |
|------|--------|----------|
| 实例类服务 | 19 个 | Price List API 实时查询 |
| 按用量服务 | 15+ 个 | 内置公式计算（S3/Lambda/DynamoDB/CloudFront 等） |

完整能力：
- 🧾 **完整 BOM** — 计算 + 存储 + IOPS + 数据传输 + 备份 + 隐藏成本
- 💡 **Graviton 推荐** — 自动建议 ARM 替代机型，标注节省比例
- 📊 **RI 回本分析** — break-even 计算 + Savings Plans 对比
- ⚠️ **隐藏成本提醒** — NAT Gateway、EIP、跨 AZ 流量、CloudWatch 等
- 🏗️ **架构模式** — 多服务组合报价，汇总总 BOM
- 📤 **导出报价** — 保存为 Markdown 文件

### Skill 文件说明

| 文件 | 平台 | 说明 |
|------|------|------|
| `SKILL.md` | Kiro CLI | 含 YAML frontmatter 触发关键词，自动匹配 |
| `CLAUDE_COMMAND.md` | Claude Code | 含 `$ARGUMENTS` 占位符，通过 `/user:aws-pricing` 调用 |
| `openclaw-skill/` | OpenClaw | `skill.md` + `index.js`，安装到 `~/.openclaw/skills/` |

三个平台的核心内容相同（参数清单、交互策略、参考价格表、BOM 模板、优化建议），仅头部格式不同。

---

## 快速开始

### 1. 安装

```bash
git clone https://github.com/neosun100/aws-pricing-tool.git && cd aws-pricing-tool
pip3 install boto3
python3 pricing_tool.py --help
```

### 2. 配置 AWS 凭证

```bash
# 方式 A：AWS Profile（推荐）
aws configure --profile my-profile

# 方式 B：SSO
aws sso login --profile my-profile

# 方式 C：环境变量
export AWS_ACCESS_KEY_ID=<key>
export AWS_SECRET_ACCESS_KEY=<secret>
```

最小 IAM 权限：
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["pricing:GetProducts", "pricing:GetAttributeValues", "pricing:DescribeServices"],
    "Resource": "*"
  }]
}
```

### 3. 查询价格

```bash
python3 pricing_tool.py --profile p query ec2 -t c6g.xlarge -r 东京
python3 pricing_tool.py --profile p query rds -t db.r6g.xlarge -r 新加坡 -e aurora-mysql
python3 pricing_tool.py --profile p compare ec2 -t c6g.xlarge -r "东京,新加坡,弗吉尼亚"
```

---

## 命令参考

### `query` — 查询单个实例价格

```bash
python3 pricing_tool.py --profile <p> query <service> -t <type> -r <region> \
    [-e engine] [-d Multi-AZ] [--os Windows] [--json] [--csv]
```

**19 个服务完整示例：**

| 分类 | 服务 | 示例 |
|------|------|------|
| 计算 | `ec2` | `query ec2 -t c6g.xlarge -r 东京` |
| 计算 | `ec2` (Windows) | `query ec2 -t m6i.xlarge -r 东京 --os Windows` |
| 数据库 | `rds` (Aurora) | `query rds -t db.r6g.xlarge -r 东京 -e aurora-mysql` |
| 数据库 | `rds` (Multi-AZ) | `query rds -t db.r6g.large -r 东京 -e mysql -d Multi-AZ` |
| 缓存 | `elasticache` | `query elasticache -t cache.r6g.large -r 东京 -e redis` |
| 搜索 | `opensearch` | `query opensearch -t m6g.large.search -r 东京` |
| 数仓 | `redshift` | `query redshift -t ra3.xlplus -r 东京` |
| 图数据库 | `neptune` | `query neptune -t db.r6g.large -r 东京` |
| 文档数据库 | `docdb` | `query docdb -t db.r6g.large -r 东京` |
| 内存数据库 | `memorydb` | `query memorydb -t db.r6g.large -r 东京` |
| 消息队列 | `mq` ⚠️ | `query mq -t m5.large -r 东京` |
| 缓存加速 | `dax` ⚠️ | `query dax -t r5.large -r 东京` |
| 机器学习 | `sagemaker` | `query sagemaker -t ml.m5.xlarge -r 东京` |
| 大数据 | `emr` ⚠️ | `query emr -t m6g.xlarge -r 东京` |
| 游戏 | `gamelift` | `query gamelift -t c5.large -r 东京` |
| 流式桌面 | `appstream` | `query appstream -t stream.standard.large -r 东京` |
| 虚拟桌面 | `workspaces` | `query workspaces -t c5.xlarge -r 东京` |
| 容器 | `ecs` | `query ecs -t t3.medium -r 东京` |
| 容器 | `eks` | `query eks -t t3.medium -r 东京` |
| VMware | `evs` | `query evs -t i4i.metal -r 东京` |

> ⚠️ MQ / DAX / EMR 的实例类型**无服务前缀**，直接用 `m5.large` 而非 `mq.m5.large`

### `batch` — 批量对比同 Region 多机型

```bash
python3 pricing_tool.py --profile p batch ec2 -t "c6g.xlarge,c6g.2xlarge,c6g.4xlarge" -r 东京
python3 pricing_tool.py --profile p batch ec2 -t "c6g.xlarge,c6g.2xlarge" -r 东京 --json
```

### `compare` — 跨 Region 比价（★ 标注最便宜）

```bash
python3 pricing_tool.py --profile p compare ec2 -t c6in.4xlarge -r "东京,新加坡,弗吉尼亚,法兰克福"
python3 pricing_tool.py --profile p compare ec2 -t c6g.xlarge -r "东京,弗吉尼亚" --csv
```

### `list` — 列出指定 Region 可用机型

```bash
python3 pricing_tool.py --profile p list ec2 -r 东京 -f c6g
python3 pricing_tool.py --profile p list rds -r 东京 -f db.r6g --json
```

> `list` 现在返回指定 Region 的真实可用机型（通过 `GetProducts` API 过滤），而非全局列表。

### 缓存管理

```bash
python3 pricing_tool.py cache-info                    # 查看缓存状态
python3 pricing_tool.py refresh                       # 清除全部缓存
python3 pricing_tool.py --no-cache query ec2 -t ...   # 单次跳过缓存
```

### `regions` — 列出所有支持的 Region

```bash
python3 pricing_tool.py regions                       # 表格输出
python3 pricing_tool.py regions --json                # JSON 输出
```

### 输出格式

所有查询命令（`query`、`batch`、`compare`、`list`）均支持三种输出：

| 格式 | 参数 | 适用场景 |
|------|------|----------|
| 彩色表格 | _(默认)_ | 终端阅读，自动检测 TTY |
| JSON | `--json` | 程序解析、AI Skill 集成 |
| CSV | `--csv` | 导入 Excel / Google Sheets |

```bash
python3 pricing_tool.py --profile p query ec2 -t c6g.xlarge -r 东京 --json
python3 pricing_tool.py --profile p compare ec2 -t c6g.xlarge -r "东京,弗吉尼亚" --csv
python3 pricing_tool.py --version
```

---

## 支持的 Region（34 个）

支持中文、英文别名和标准 Region Code，大小写不敏感。

| 中文 | 英文 | 代码 | | 中文 | 英文 | 代码 |
|:---:|:---:|:---:|---|:---:|:---:|:---:|
| 弗吉尼亚 | virginia | us-east-1 | | 东京 | tokyo | ap-northeast-1 |
| 俄亥俄 | ohio | us-east-2 | | 首尔 | seoul | ap-northeast-2 |
| 加利福尼亚 | california | us-west-1 | | 大阪 | osaka | ap-northeast-3 |
| 俄勒冈 | oregon | us-west-2 | | 新加坡 | singapore | ap-southeast-1 |
| 加拿大 | canada | ca-central-1 | | 悉尼 | sydney | ap-southeast-2 |
| 卡尔加里 | calgary | ca-west-1 | | 雅加达 | jakarta | ap-southeast-3 |
| 圣保罗 | saopaulo | sa-east-1 | | 墨尔本 | melbourne | ap-southeast-4 |
| 墨西哥 | mexico | mx-central-1 | | 马来西亚 | malaysia | ap-southeast-5 |
| 法兰克福 | frankfurt | eu-central-1 | | 泰国 | thailand | ap-southeast-6 |
| 苏黎世 | zurich | eu-central-2 | | 新西兰 | newzealand | ap-southeast-7 |
| 爱尔兰 | ireland | eu-west-1 | | 香港 | hongkong | ap-east-1 |
| 伦敦 | london | eu-west-2 | | 台北 | taipei | ap-east-2 |
| 巴黎 | paris | eu-west-3 | | 孟买 | mumbai | ap-south-1 |
| 米兰 | milan | eu-south-1 | | 海得拉巴 | hyderabad | ap-south-2 |
| 西班牙 | spain | eu-south-2 | | 巴林 | bahrain | me-south-1 |
| 斯德哥尔摩 | stockholm | eu-north-1 | | 阿联酋 | uae | me-central-1 |
| 开普敦 | capetown | af-south-1 | | 特拉维夫 | telaviv | il-central-1 |

---

## 实例命名规则

```
c6in.4xlarge
│││  └── 规格: nano < micro < small < medium < large < xlarge < 2xlarge < ... < metal
││└── 属性: n=网络增强  g=Graviton(ARM)  a=AMD  i=Intel  d=本地SSD
│└── 代数: 5/6/7（越新越便宜）
└── 系列: c=计算  m=通用  r=内存  t=突发  i=存储  p/g=GPU
```

**前缀规则：**

| 服务 | 前缀 | 示例 |
|------|------|------|
| EC2 / GameLift / AppStream / ECS / EKS / EVS | 无 | `c6g.xlarge` |
| RDS / Neptune / DocDB | `db.` | `db.r6g.xlarge` |
| ElastiCache | `cache.` | `cache.r6g.large` |
| OpenSearch | 后缀 `.search` | `m6g.large.search` |
| SageMaker | `ml.` | `ml.m5.xlarge` |
| MQ / DAX / EMR ⚠️ | 无 | `m5.large` |

---

## 使用技巧

```bash
# Graviton vs x86 比价（ARM 通常便宜 20%）
python3 pricing_tool.py --profile p batch ec2 -t "c6i.4xlarge,c6g.4xlarge" -r 东京

# 找最便宜的 Region
python3 pricing_tool.py --profile p compare ec2 -t c6g.xlarge \
    -r "弗吉尼亚,爱尔兰,东京,新加坡,孟买"

# JSON 输出 → jq 处理
python3 pricing_tool.py --profile p query ec2 -t c6g.xlarge -r 东京 --json | jq '.[] | .price_per_hour'

# CSV 输出 → Excel
python3 pricing_tool.py --profile p compare ec2 -t c6g.xlarge \
    -r "东京,新加坡,弗吉尼亚" --csv > compare.csv

# 程序化调用
python3 -c "
from pricing_tool import get_client, query_products, extract_pricing, build_filters, SERVICE_CODES
from types import SimpleNamespace
args = SimpleNamespace(region='ap-northeast-1', instance_type='c6g.xlarge', os='Linux',
                       engine=None, deployment=None)
client = get_client('my-profile')
products = query_products(client, SERVICE_CODES['ec2'], build_filters('ec2', args))
for p in products:
    r = extract_pricing(p)
    if r.get('price_per_hour'):
        print(f'{r[\"instance_type\"]}: \${r[\"price_per_hour\"]:.4f}/hr')
"
```

---

## 常见问题

| 问题 | 解决 |
|------|------|
| 凭证过期 | `aws sso login --profile <p>` 重新登录 |
| 查不到机型 | 用 `list` 确认该 Region 是否有此机型；注意 MQ/DAX/EMR 无前缀 |
| 价格不一致 | 确认 Region / OS / 部署模式（Single-AZ vs Multi-AZ）；用 `--no-cache` 刷新 |
| 查 Spot 价格 | 本工具不支持 Spot，请用 `aws ec2 describe-spot-price-history --instance-types ...` |
| 缓存占用大 | `python3 pricing_tool.py refresh` 清除全部缓存 |

---

## 开发

### 项目结构

```
aws-pricing-tool/
├── pricing_tool.py    # 主程序（单文件，可独立运行）
├── mcp_server.py      # MCP Server（6 个工具，适配所有 MCP 客户端）
├── SKILL.md           # Kiro Skill 定义文件（模板，需配置路径和 Profile）
├── CLAUDE_COMMAND.md  # Claude Code Slash Command 文件（模板）
├── openclaw-skill/    # OpenClaw Skill（skill.md + index.js）
│   ├── skill.md       # OpenClaw skill 规范文件
│   └── index.js       # OpenClaw skill 执行入口
├── conftest.py        # 测试 fixtures（模拟 AWS API 响应）
├── test_unit.py       # 单元测试（66 个）
├── test_e2e.py        # 端到端测试（27 个）
├── test_mcp.py        # MCP Server 测试（40 个）
├── logo.png           # 项目 Logo
├── README.md          # 英文文档
├── README_CN.md       # 中文文档
└── .gitignore
```

### 运行测试

```bash
pip3 install pytest
python3 -m pytest -v                    # 运行全部 93 个测试
python3 -m pytest test_unit.py -v       # 仅单元测试
python3 -m pytest test_e2e.py -v        # 仅 E2E 测试
python3 -m pytest -k "extract_pricing"  # 按名称过滤
```

测试覆盖：

| 文件 | 测试数 | 覆盖范围 |
|------|--------|----------|
| `test_unit.py` | 66 | Region 解析、缓存读写、价格提取（OD + 6 RI）、去重排序、格式化、19 服务 filter、JSON/CSV 输出、颜色 |
| `test_e2e.py` | 27 | CLI 参数解析、--version/--help、query/batch/compare/list 全命令 JSON/CSV/表格输出、缓存命令、错误处理 |

E2E 测试通过 subprocess 调用真实 CLI，使用 mock runner 注入模拟 API 响应，无需 AWS 凭证。

### 技术栈

- Python 3.8+（无第三方依赖，仅 `boto3`）
- AWS Price List API（`us-east-1` 端点）
- 本地 JSON 文件缓存（`~/.cache/aws-pricing/`，7 天 TTL）

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0.0 | 2025-03-13 | MCP Server 升级至 10 个工具：+`graviton_recommend` +`ri_analysis` +`calculate_s3` +`calculate_lambda`；133 个测试（40 MCP + 93 原有）；"定价顾问"能力全部可通过 MCP 调用 |
| v1.5.0 | 2025-03-13 | MCP Server（`mcp_server.py`）6 个工具；支持 Kiro/Claude Code/OpenClaw/Cursor/VS Code；113 个测试（20 MCP + 93 原有） |
| v1.3.0 | 2025-03-12 | OpenClaw skill 支持（`openclaw-skill/`）；3 平台 AI Skill（Kiro + Claude Code + OpenClaw）；`.gitignore` 增强敏感文件过滤 |
| v1.2.0 | 2025-02-27 | 全命令 `--json`/`--csv` 输出；终端彩色；`list` 按 Region 过滤；`--version`；19 服务 filter 补全；3yr_No_Upfront RI 修复；`regions` 命令；93 个测试 |
| v1.0.0 | 2025-02-25 | 初始版本：19 服务 × 34 Region，query/batch/compare/list，本地缓存 |
