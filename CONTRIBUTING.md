# Contributing

Thanks for your interest in contributing!

## Development Setup

```bash
git clone https://github.com/neosun100/aws-pricing-tool.git && cd aws-pricing-tool
pip install boto3 pytest
make test
```

## Running Tests

```bash
make test          # All 186 tests
make lint          # Syntax check
```

No AWS credentials needed — tests use mocked API responses.

## Pull Requests

1. Fork the repo and create a feature branch
2. Add tests for new functionality
3. Run `make test` and ensure all tests pass
4. Submit a PR with a clear description

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `test:` tests
- `chore:` maintenance

## Skill Files

Three AI Skill platforms are supported:

| File | Platform | Notes |
|------|----------|-------|
| `SKILL.md` | Kiro CLI | Single source of truth |
| `CLAUDE_COMMAND.md` | Claude Code | Generated from SKILL.md |
| `openclaw-skill/` | OpenClaw | `skill.md` + `index.js` |

After editing `SKILL.md`, run:

```bash
make skill    # Regenerates CLAUDE_COMMAND.md from SKILL.md
```
