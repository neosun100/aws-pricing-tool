.PHONY: test lint skill clean

test:
	python3 -m pytest -v

lint:
	python3 -m py_compile pricing_tool.py

# Generate CLAUDE_COMMAND.md from SKILL.md (single source of truth)
skill:
	@echo "You are an AWS pricing consultant. Process the following request using the instructions below." > CLAUDE_COMMAND.md
	@echo "" >> CLAUDE_COMMAND.md
	@echo 'User request: $$ARGUMENTS' >> CLAUDE_COMMAND.md
	@echo "" >> CLAUDE_COMMAND.md
	@sed -n '5,$$p' SKILL.md >> CLAUDE_COMMAND.md
	@echo "✅ CLAUDE_COMMAND.md generated from SKILL.md"

clean:
	rm -rf __pycache__ .pytest_cache *.pyc
