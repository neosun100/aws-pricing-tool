# AWS Pricing Tool 🏷️

<p align="center">
  <img src="logo.png" alt="AWS Pricing Tool" width="200">
</p>

> 一条命令查询 AWS 任意服务的实时价格，支持 **34 个服务** × **34 个 Region** × **6 种 RI 方案**。

```bash
# 30 秒上手
pip3 install boto3
python3 pricing_tool.py --profile <your-profile> query ec2 -t c6g.xlarge -r 东京
```

---

## 快速开始

### 第 1 步：安装

```bash
git clone https://github.com/neosun100/aws-pricing-tool.git && cd aws-pricing-tool
pip3 install boto3
python3 pricing_tool.py --help
```

### 第 2 步：配置 AWS 凭证

```bash
# 方式 A：AWS Profile（推荐）
aws configure --profile my-profile

# 方式 B：Isengard（Amazon 内部）
isengardcli credentials <account> --role <role>

# 方式 C：SSO
aws sso login --profile my-profile

# 方式 D：环境变量
export AWS_ACCESS_KEY_ID=<key>
export AWS_SECRET_ACCESS_KEY=<secret>
```

最小 IAM 权限：
```json
{
  "Version": "2012-10-17",
  "Statement": [{"Effect": "Allow", "Action": ["pricing:GetProducts", "pricing:GetAttributeValues", "pricing:DescribeServices"], "Resource": "*"}]
}
```

### 第 3 步：查询价格

```bash
python3 pricing_tool.py --profile my-profile query ec2 -t c6g.xlarge -r 东京
python3 pricing_tool.py --profile my-profile query rds -t db.r6g.xlarge -r 新加坡 -e aurora-mysql
python3 pricing_tool.py --profile my-profile compare ec2 -t c6g.xlarge -r "东京,新加坡,弗吉尼亚"
```

---

## 命令参考

### `query` — 查询价格

```bash
python3 pricing_tool.py --profile <p> query <service> -t <type> -r <region> [-e engine] [-d Multi-AZ] [--os Windows] [--json]
```

**19 个服务完整示例：**

```bash
# EC2
python3 pricing_tool.py --profile p query ec2 -t c6in.4xlarge -r 东京
python3 pricing_tool.py --profile p query ec2 -t m6i.xlarge -r 东京 --os Windows

# RDS / Aurora
python3 pricing_tool.py --profile p query rds -t db.r6g.xlarge -r 东京 -e aurora-mysql
python3 pricing_tool.py --profile p query rds -t db.r6g.large -r 东京 -e mysql -d Multi-AZ

# ElastiCache
python3 pricing_tool.py --profile p query elasticache -t cache.r6g.large -r 东京 -e redis

# OpenSearch / Redshift
python3 pricing_tool.py --profile p query opensearch -t m6g.large.search -r 东京
python3 pricing_tool.py --profile p query redshift -t ra3.xlplus -r 东京

# Neptune / DocumentDB / MemoryDB
python3 pricing_tool.py --profile p query neptune -t db.r6g.large -r 东京
python3 pricing_tool.py --profile p query docdb -t db.r6g.large -r 东京
python3 pricing_tool.py --profile p query memorydb -t db.r6g.large -r 东京

# MQ / DAX（⚠️ 无服务前缀）
python3 pricing_tool.py --profile p query mq -t m5.large -r 东京
python3 pricing_tool.py --profile p query dax -t r5.large -r 东京

# SageMaker / EMR（⚠️ EMR 无前缀）
python3 pricing_tool.py --profile p query sagemaker -t ml.m5.xlarge -r 东京
python3 pricing_tool.py --profile p query emr -t m6g.xlarge -r 东京

# GameLift / AppStream / WorkSpaces / ECS / EKS / EVS
python3 pricing_tool.py --profile p query gamelift -t c5.large -r 东京
python3 pricing_tool.py --profile p query appstream -t stream.standard.large -r 东京
python3 pricing_tool.py --profile p query workspaces -t c5.xlarge -r 东京
python3 pricing_tool.py --profile p query ecs -t t3.medium -r 东京
python3 pricing_tool.py --profile p query eks -t t3.medium -r 东京
python3 pricing_tool.py --profile p query evs -t i4i.metal -r 东京
```

### `batch` — 批量对比

```bash
python3 pricing_tool.py --profile p batch ec2 -t "c6g.xlarge,c6g.2xlarge,c6g.4xlarge" -r 东京
```

### `compare` — 跨 Region 比价（★ 标注最便宜）

```bash
python3 pricing_tool.py --profile p compare ec2 -t c6in.4xlarge -r "东京,新加坡,弗吉尼亚,法兰克福"
```

### `list` — 列出可用机型

```bash
python3 pricing_tool.py --profile p list ec2 -r 东京 -f c6g
python3 pricing_tool.py --profile p list rds -r 东京 -f db.r6g
```

### 缓存管理

```bash
python3 pricing_tool.py cache-info                    # 查看缓存
python3 pricing_tool.py refresh                       # 清除缓存
python3 pricing_tool.py --no-cache query ec2 -t ...   # 跳过缓存
```

---

## 支持的 Region（34 个，中英文别名）

| 中文 | 英文 | 代码 | | 中文 | 英文 | 代码 |
|:---:|:---:|:---:|---|:---:|:---:|:---:|
| 弗吉尼亚 | virginia | us-east-1 | | 东京 | tokyo | ap-northeast-1 |
| 俄亥俄 | ohio | us-east-2 | | 首尔 | seoul | ap-northeast-2 |
| 俄勒冈 | oregon | us-west-2 | | 新加坡 | singapore | ap-southeast-1 |
| 法兰克福 | frankfurt | eu-central-1 | | 香港 | hongkong | ap-east-1 |
| 爱尔兰 | ireland | eu-west-1 | | 孟买 | mumbai | ap-south-1 |
| 伦敦 | london | eu-west-2 | | 悉尼 | sydney | ap-southeast-2 |
| 巴黎 | paris | eu-west-3 | | 雅加达 | jakarta | ap-southeast-3 |
| 斯德哥尔摩 | stockholm | eu-north-1 | | 大阪 | osaka | ap-northeast-3 |
| 圣保罗 | saopaulo | sa-east-1 | | 台北 | taipei | ap-east-2 |
| 加拿大 | canada | ca-central-1 | | 墨尔本 | melbourne | ap-southeast-4 |
| 巴林 | bahrain | me-south-1 | | 泰国 | thailand | ap-southeast-6 |
| 开普敦 | capetown | af-south-1 | | 新西兰 | newzealand | ap-southeast-7 |

完整 34 个 Region 均支持，含 苏黎世、米兰、西班牙、卡尔加里、墨西哥、阿联酋、特拉维夫、海得拉巴、马来西亚 等。

---

## 实例命名规则

```
c6in.4xlarge
│││  └── 规格: nano < micro < small < medium < large < xlarge < 2xlarge < ... < metal
││└── 属性: n=网络增强  g=Graviton(ARM)  a=AMD  i=Intel  d=本地SSD
│└── 代数: 5/6/7（越新越便宜）
└── 系列: c=计算  m=通用  r=内存  t=突发  i=存储  p/g=GPU
```

**前缀规则：** EC2 无前缀 | RDS/Neptune/DocDB `db.` | ElastiCache `cache.` | OpenSearch 后缀 `.search` | SageMaker `ml.` | **MQ/DAX/EMR ⚠️ 无前缀**

---

## 使用技巧

```bash
# Graviton vs x86 比价（ARM 通常便宜 20%）
python3 pricing_tool.py --profile p query ec2 -t c6i.4xlarge -r 东京
python3 pricing_tool.py --profile p query ec2 -t c6g.4xlarge -r 东京

# 找最便宜的 Region
python3 pricing_tool.py --profile p compare ec2 -t c6g.xlarge -r "弗吉尼亚,爱尔兰,东京,新加坡,孟买"

# JSON 输出用于程序处理
python3 pricing_tool.py --profile p query ec2 -t c6g.xlarge -r 东京 --json | python3 -m json.tool
```

---

## 常见问题

| 问题 | 解决 |
|------|------|
| 凭证过期 | `aws sso login` 或 `isengardcli credentials ...` |
| 查不到机型 | 用 `list` 确认；MQ/DAX/EMR 无前缀 |
| 价格不一致 | 确认 Region/OS/部署模式；用 `--no-cache` |
| 查 Spot 价格 | `aws ec2 describe-spot-price-history --instance-types ...` |
