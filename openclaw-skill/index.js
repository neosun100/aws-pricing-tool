// index.js — OpenClaw skill entry point for AWS Pricing Tool
// Executes pricing_tool.py via shell and returns structured results.

const TOOL_PATH = '/your/path/to/pricing_tool.py';
const AWS_PROFILE = 'your-profile';

export async function execute(inputs, context) {
  const { query } = inputs;

  // Parse natural language query into CLI arguments
  const cmd = buildCommand(query);
  if (!cmd) {
    return {
      text: 'Could not parse the pricing query. Please specify a service, instance type, and region.\n' +
            'Example: "EC2 c6g.xlarge in Tokyo" or "Compare RDS db.r6g.xlarge across Tokyo and Virginia"',
      error: true,
    };
  }

  try {
    const result = await context.shell.exec(cmd, { timeout: 30000 });
    if (result.exitCode !== 0) {
      return { text: `Pricing query failed: ${result.stderr || result.stdout}`, error: true };
    }

    // Try to parse JSON output
    try {
      const data = JSON.parse(result.stdout);
      return { text: formatPricingResult(data), data, error: false };
    } catch {
      // Return raw text output if not JSON
      return { text: result.stdout, error: false };
    }
  } catch (err) {
    return { text: `Execution error: ${err.message}`, error: true };
  }
}

function buildCommand(query) {
  // Base command
  const base = `python3 ${TOOL_PATH} --profile ${AWS_PROFILE}`;

  // The AI agent will typically parse the natural language and call
  // this skill with appropriate parameters. The shell command is
  // constructed by the agent based on the skill.md instructions.
  // This function provides a fallback for direct invocation.

  const q = query.toLowerCase();

  if (q.includes('compare') || q.includes('对比') || q.includes('比较')) {
    return `${base} compare --json`;
  }
  if (q.includes('batch') || q.includes('批量')) {
    return `${base} batch --json`;
  }
  if (q.includes('list') || q.includes('列出') || q.includes('有哪些')) {
    return `${base} list --json`;
  }
  if (q.includes('cache') || q.includes('缓存')) {
    return `${base} cache-info`;
  }
  if (q.includes('region') || q.includes('区域')) {
    return `${base} regions --json`;
  }

  // Default: pass as query (agent should construct full command)
  return `${base} query --json`;
}

function formatPricingResult(data) {
  if (!Array.isArray(data) || data.length === 0) {
    return 'No pricing data found for the specified query.';
  }

  const lines = [];
  for (const item of data) {
    if (item.instance_type) {
      lines.push(`${item.instance_type}: $${item.price_per_hour}/hr ($${item.price_per_month}/mo)`);
    }
  }
  return lines.join('\n') || JSON.stringify(data, null, 2);
}
