---
name: aws-pricing-query
version: 1.0.0
emoji: 💰
description: "Query real-time AWS pricing for 19 instance-based services across 34 regions. Supports EC2, RDS, Aurora, ElastiCache, OpenSearch, Redshift, Neptune, DocumentDB, MemoryDB, MQ, DAX, SageMaker, EMR, GameLift, AppStream, WorkSpaces, ECS, EKS, EVS. Returns On-Demand + 6 RI options. Also calculates usage-based services (S3, Lambda, DynamoDB, CloudFront, etc.) via built-in formulas."
author: neosun100
license: MIT

capabilities:
  - id: query-instance-pricing
    description: "Query real-time pricing for a specific AWS instance type in a given region, returning On-Demand and 6 Reserved Instance options"
  - id: batch-compare-types
    description: "Compare pricing across multiple instance types in the same region"
  - id: cross-region-compare
    description: "Compare pricing for the same instance type across multiple regions, marking the cheapest"
  - id: list-instance-types
    description: "List available instance types for a service in a specific region"
  - id: calculate-usage-pricing
    description: "Calculate usage-based service costs using built-in formulas for S3, Lambda, DynamoDB, CloudFront, API Gateway, SQS, SNS, Kinesis, EFS, ELB, NAT Gateway, Route 53, Athena, Glue, MSK, Bedrock"
  - id: generate-bom
    description: "Generate a complete Bill of Materials with compute, storage, network, and hidden costs"
  - id: graviton-recommendation
    description: "Recommend Graviton ARM alternatives for x86 instance types with cost savings estimate"
  - id: ri-breakeven-analysis
    description: "Calculate Reserved Instance break-even point vs On-Demand pricing"
  - id: calculate-bedrock
    description: "Calculate Amazon Bedrock model inference cost with 20 models from 10 providers and 4 pricing tiers"
  - id: list-bedrock-models
    description: "List all available Bedrock models with reference pricing per 1M tokens"

permissions:
  network: false
  filesystem: false
  shell: true
  env: []

inputs:
  - name: query
    type: string
    required: true
    description: "Natural language pricing query, e.g. 'How much is c6g.xlarge in Tokyo?' or 'Compare Aurora db.r6g.xlarge across Tokyo and Virginia'"

tags:
  - aws
  - pricing
  - cloud
  - cost-optimization
  - devops

outputs:
  - name: text
    type: string
    description: "Formatted pricing result text for display"
  - name: data
    type: object
    description: "Structured pricing data (JSON) for programmatic use"
  - name: error
    type: boolean
    description: "Whether the query encountered an error"

minOpenClawVersion: "2.1.0"
---

# AWS Real-Time Pricing Query Skill

## Skill Description

This skill turns OpenClaw into an AWS pricing consultant. Ask in natural language, get complete cost breakdowns with optimization suggestions.

Covers **19 instance-based services** via AWS Price List API (real-time) and **15+ usage-based services** via built-in pricing formulas.

## Setup

1. Install dependency: `pip3 install boto3`
2. Configure AWS credentials: `aws configure --profile <your-profile>`
3. Edit the tool path and profile below to match your environment

## Configuration

```
Tool path: /your/path/to/pricing_tool.py
AWS profile: --profile your-profile
```

## Usage Examples

- "How much is c6g.xlarge in Tokyo?"
- "Compare c6in.4xlarge across Tokyo, Singapore, and Virginia"
- "2x Aurora MySQL db.r6g.xlarge Tokyo Multi-AZ 500GB — full BOM"
- "Architecture: 2x c6in.4xlarge + Aurora db.r6g.xlarge + Redis cache.r6g.large Tokyo"
- "S3 10TB Standard, 1M GET/month"
- "When does RI break even for c6g.xlarge?"

## How to Execute Queries

### Single instance pricing
```bash
python3 /your/path/to/pricing_tool.py --profile your-profile \
  query <service> -t <instance-type> -r <region> [-e <engine>] [-d "Multi-AZ"] [--os Windows] --json
```

### Batch compare (multiple types, same region)
```bash
python3 /your/path/to/pricing_tool.py --profile your-profile \
  batch <service> -t "type1,type2,type3" -r <region> --json
```

### Cross-region compare
```bash
python3 /your/path/to/pricing_tool.py --profile your-profile \
  compare <service> -t <type> -r "region1,region2,region3" --json
```

### List available types
```bash
python3 /your/path/to/pricing_tool.py --profile your-profile \
  list <service> -r <region> -f <filter> --json
```

## Supported Services (19)

| Service | Command | Type Example | Notes |
|---------|---------|-------------|-------|
| EC2 | ec2 | c6g.xlarge | Linux/Windows/Graviton |
| RDS/Aurora | rds | db.r6g.xlarge | -e aurora-mysql/postgresql/mysql etc. |
| ElastiCache | elasticache | cache.r6g.large | -e redis/memcached |
| OpenSearch | opensearch | m6g.large.search | |
| Redshift | redshift | ra3.xlplus | |
| Neptune | neptune | db.r6g.large | |
| DocumentDB | docdb | db.r6g.large | |
| MemoryDB | memorydb | db.r6g.large | |
| MQ | mq | m5.large | No mq. prefix |
| DAX | dax | r5.large | No dax. prefix |
| SageMaker | sagemaker | ml.m5.xlarge | |
| EMR | emr | m6g.xlarge | No prefix |
| GameLift | gamelift | c5.large | |
| AppStream | appstream | stream.standard.large | |
| WorkSpaces | workspaces | c5.xlarge | |
| ECS | ecs | t3.medium | |
| EKS | eks | t3.medium | |
| EVS | evs | i4i.metal | |

## Region Aliases (34 regions)

Supports Chinese, English, and region codes. Examples:
- 东京 / tokyo / ap-northeast-1
- 新加坡 / singapore / ap-southeast-1
- 弗吉尼亚 / virginia / us-east-1
- 法兰克福 / frankfurt / eu-central-1

## Interaction Rules

1. If the user's query is missing required parameters (region, instance type), ask follow-up questions
2. Always show On-Demand + RI options when querying instance pricing
3. For x86 instance types, suggest Graviton alternatives with savings estimate
4. For architecture queries (multiple services), generate a combined BOM
5. For usage-based services (S3, Lambda, etc.), calculate using built-in formulas without calling the tool
6. Always mention hidden costs (NAT Gateway, data transfer, EBS snapshots, etc.)

## Notes

- MQ, DAX, EMR instance types have NO service prefix (use m5.large, not mq.m5.large)
- Use --json flag for structured output when parsing results
- Cache is enabled by default (7-day TTL); use --no-cache to bypass
- Minimum IAM permission needed: pricing:GetProducts, pricing:GetAttributeValues, pricing:DescribeServices
