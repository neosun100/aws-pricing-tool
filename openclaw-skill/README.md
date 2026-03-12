# AWS Pricing Query — OpenClaw Skill

💰 Query real-time AWS pricing for 19 services × 34 regions via natural language.

## Install

```bash
cp -r openclaw-skill ~/.openclaw/skills/aws-pricing-query
```

## Configure

Edit `skill.md` and `index.js` — update the tool path and AWS profile:

```
# skill.md
Tool path: /your/path/to/pricing_tool.py
AWS profile: --profile your-profile
```

```js
// index.js
const TOOL_PATH = '/your/path/to/pricing_tool.py';
const AWS_PROFILE = 'your-profile';
```

## Prerequisites

- Python 3.8+ with `boto3` installed
- AWS credentials configured (`aws configure --profile <name>`)
- IAM permissions: `pricing:GetProducts`, `pricing:GetAttributeValues`, `pricing:DescribeServices`

## Usage

Just ask naturally in OpenClaw:

```
👤 How much is c6g.xlarge in Tokyo?
👤 Compare Aurora db.r6g.xlarge across Tokyo and Virginia
👤 S3 10TB Standard, 1M GET/month
```

## Files

| File | Description |
|------|-------------|
| `skill.md` | Skill specification (YAML frontmatter + Markdown) |
| `index.js` | Execution entry point (calls pricing_tool.py via shell) |
| `README.md` | This file |
