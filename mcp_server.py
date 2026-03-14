"""MCP Server for AWS Pricing Tool.

Exposes pricing_tool.py functions as MCP tools for Kiro / Claude Code / OpenClaw / Cursor / VS Code.
Run: python mcp_server.py  (stdio mode, for MCP client integration)
"""

import os
from types import SimpleNamespace
from fastmcp import FastMCP

import pricing_tool as pt

mcp = FastMCP(
    name="aws-pricing-tool",
    instructions=(
        "AWS pricing consultant. Query real-time pricing for 19 services × 34 regions. "
        "Returns On-Demand + 6 RI options. Supports Chinese/English region aliases. "
        "Use query_pricing for single lookups, compare_regions for cross-region, "
        "batch_compare for multi-type, list_types to discover instance types."
    ),
)


def _get_client():
    profile = os.environ.get("AWS_PROFILE")
    return pt.get_client(profile)


# ── Graviton mapping ───────────────────────────────────────────

GRAVITON_MAP = {
    "c5": "c6g", "c5n": "c6gn", "c5a": "c6g",
    "c6i": "c7g", "c6in": "c6gn", "c6a": "c7g", "c7i": "c7g", "c7a": "c7g",
    "m5": "m6g", "m5a": "m6g",
    "m6i": "m7g", "m6a": "m7g", "m7i": "m7g", "m7a": "m7g",
    "r5": "r6g", "r5a": "r6g",
    "r6i": "r7g", "r6a": "r7g", "r7i": "r7g", "r7a": "r7g",
    "t3": "t4g", "t3a": "t4g",
    "i3": "i4g", "i3en": "i4g",
    "db.r5": "db.r6g", "db.r6i": "db.r6g", "db.m5": "db.m6g", "db.m6i": "db.m6g",
    "db.t3": "db.t4g",
    "cache.r5": "cache.r6g", "cache.m5": "cache.m6g", "cache.r6i": "cache.r6g",
    "cache.t3": "cache.t4g",
}


def _suggest_graviton(instance_type):
    """Return Graviton alternative for an x86 instance type, or None."""
    for x86, arm in GRAVITON_MAP.items():
        if instance_type.startswith(x86 + "."):
            size = instance_type[len(x86) + 1:]
            return f"{arm}.{size}"
    return None


# ── S3 pricing formulas ───────────────────────────────────────

S3_PRICING = {
    "Standard":           {"storage": 0.023, "put_1k": 0.005, "get_1k": 0.0004},
    "Intelligent-Tiering":{"storage": 0.023, "put_1k": 0.005, "get_1k": 0.0004},
    "Standard-IA":        {"storage": 0.0125,"put_1k": 0.01,  "get_1k": 0.001},
    "One Zone-IA":        {"storage": 0.01,  "put_1k": 0.01,  "get_1k": 0.001},
    "Glacier Instant":    {"storage": 0.004, "put_1k": 0.02,  "get_1k": 0.01},
    "Glacier Flexible":   {"storage": 0.0036,"put_1k": 0.03,  "get_1k": 0.0004},
    "Glacier Deep Archive":{"storage":0.00099,"put_1k":0.05,  "get_1k": 0.0004},
}

# ── Bedrock pricing (us-east-1 Standard tier, 2026-03) ────────
# Source: https://aws.amazon.com/bedrock/pricing/
# NOTE: Price List API has delays for Bedrock; this table is manually maintained.

BEDROCK_PRICING = {
    # Anthropic
    "claude-3.5-sonnet":    {"input": 6.00,  "output": 30.00, "provider": "Anthropic"},
    "claude-3.5-sonnet-v2": {"input": 6.00,  "output": 30.00, "provider": "Anthropic"},
    # Amazon Nova
    "nova-pro":             {"input": 0.80,  "output": 3.20,  "provider": "Amazon"},
    "nova-lite":            {"input": 0.06,  "output": 0.24,  "provider": "Amazon"},
    "nova-micro":           {"input": 0.035, "output": 0.14,  "provider": "Amazon"},
    # Meta Llama
    "llama-4-scout":        {"input": 0.17,  "output": 0.35,  "provider": "Meta"},
    "llama-4-maverick":     {"input": 0.50,  "output": 1.50,  "provider": "Meta"},
    "llama-3.3-70b":        {"input": 0.72,  "output": 0.72,  "provider": "Meta"},
    # DeepSeek
    "deepseek-v3.2":        {"input": 0.62,  "output": 1.85,  "provider": "DeepSeek"},
    # Mistral
    "mistral-large-3":      {"input": 0.50,  "output": 1.50,  "provider": "Mistral"},
    "ministral-8b":         {"input": 0.15,  "output": 0.15,  "provider": "Mistral"},
    # Google
    "gemma-3-27b":          {"input": 0.23,  "output": 0.38,  "provider": "Google"},
    "gemma-3-12b":          {"input": 0.09,  "output": 0.29,  "provider": "Google"},
    "gemma-3-4b":           {"input": 0.04,  "output": 0.08,  "provider": "Google"},
    # Qwen
    "qwen3-235b":           {"input": 0.22,  "output": 0.90,  "provider": "Qwen"},
    "qwen3-32b":            {"input": 0.15,  "output": 0.60,  "provider": "Qwen"},
    # Z AI
    "glm-4.7":              {"input": 0.60,  "output": 2.20,  "provider": "Z AI"},
    "glm-4.7-flash":        {"input": 0.07,  "output": 0.40,  "provider": "Z AI"},
    # Moonshot
    "kimi-k2.5":            {"input": 0.60,  "output": 3.00,  "provider": "Moonshot"},
    # Writer
    "palmyra-x5":           {"input": 0.60,  "output": 6.00,  "provider": "Writer"},
}

BEDROCK_PRICING_DATE = "2026-03"


# ── Core logic (testable without MCP) ──────────────────────────

def _query_pricing(service, instance_type, region, engine="", deployment="", operating_system="Linux"):
    sc = pt.SERVICE_CODES.get(service)
    if not sc:
        return [{"error": f"Unknown service '{service}'. Valid: {list(pt.SERVICE_CODES.keys())}"}]
    args = SimpleNamespace(
        region=pt.resolve_region(region), instance_type=instance_type,
        os=operating_system, engine=engine or None, deployment=deployment or None,
    )
    client = _get_client()
    products = pt.query_products(client, sc, pt.build_filters(service, args), quiet=True)
    results = pt.dedup_results([pt.extract_pricing(p) for p in products])
    for r in results:
        if r.get("price_per_hour"):
            r["price_per_month"] = round(r["price_per_hour"] * 730, 2)
    return results or [{"error": f"No pricing found for {service} {instance_type} in {region}"}]


def _compare_regions(service, instance_type, regions, engine="", operating_system="Linux"):
    sc = pt.SERVICE_CODES.get(service)
    if not sc:
        return [{"error": f"Unknown service '{service}'"}]
    all_results = []
    client = _get_client()
    for region in regions:
        args = SimpleNamespace(
            region=pt.resolve_region(region), instance_type=instance_type,
            os=operating_system, engine=engine or None, deployment=None,
        )
        products = pt.query_products(client, sc, pt.build_filters(service, args), quiet=True)
        for p in products:
            r = pt.extract_pricing(p)
            if r.get("price_per_hour"):
                r["region"] = pt.resolve_region(region)
                r["price_per_month"] = round(r["price_per_hour"] * 730, 2)
                all_results.append(r)
                break
    all_results.sort(key=lambda x: x.get("price_per_hour", 0))
    if all_results:
        all_results[0]["cheapest"] = True
    return all_results or [{"error": "No pricing found"}]


def _batch_compare(service, instance_types, region, engine="", operating_system="Linux"):
    sc = pt.SERVICE_CODES.get(service)
    if not sc:
        return [{"error": f"Unknown service '{service}'"}]
    all_results = []
    client = _get_client()
    for itype in instance_types:
        args = SimpleNamespace(
            region=pt.resolve_region(region), instance_type=itype,
            os=operating_system, engine=engine or None, deployment=None,
        )
        products = pt.query_products(client, sc, pt.build_filters(service, args), quiet=True)
        for p in products:
            r = pt.extract_pricing(p)
            if r.get("price_per_hour"):
                r["price_per_month"] = round(r["price_per_hour"] * 730, 2)
                all_results.append(r)
                break
    all_results.sort(key=lambda x: x.get("price_per_hour", 0))
    return all_results or [{"error": "No pricing found"}]


def _list_types(service, region, filter_keyword=""):
    sc = pt.SERVICE_CODES.get(service)
    if not sc:
        return [f"Unknown service '{service}'. Valid: {list(pt.SERVICE_CODES.keys())}"]
    client = _get_client()
    types = pt.list_instance_types(client, sc, pt.resolve_location(region))
    if filter_keyword:
        types = [t for t in types if filter_keyword.lower() in t.lower()]
    return types


def _get_regions():
    return [{"code": c, "name": n} for c, n in sorted(pt.REGION_MAP.items())]


def _get_services():
    return [{"service": k, "service_code": v} for k, v in sorted(pt.SERVICE_CODES.items())]


def _graviton_recommend(service, instance_type, region, engine="", operating_system="Linux"):
    alt = _suggest_graviton(instance_type)
    if not alt:
        return {"instance_type": instance_type, "is_graviton": True, "recommendation": "Already Graviton or no alternative available."}
    x86 = _query_pricing(service, instance_type, region, engine, operating_system=operating_system)
    arm = _query_pricing(service, alt, region, engine, operating_system=operating_system)
    x86_price = x86[0].get("price_per_hour", 0) if x86 and "error" not in x86[0] else 0
    arm_price = arm[0].get("price_per_hour", 0) if arm and "error" not in arm[0] else 0
    if not x86_price or not arm_price:
        return {"instance_type": instance_type, "graviton_alternative": alt, "error": "Could not fetch both prices for comparison."}
    saving_pct = round((1 - arm_price / x86_price) * 100, 1)
    saving_monthly = round((x86_price - arm_price) * 730, 2)
    saving_yearly = round(saving_monthly * 12, 2)
    return {
        "x86_type": instance_type, "x86_price_per_hour": x86_price,
        "graviton_type": alt, "graviton_price_per_hour": arm_price,
        "saving_percent": saving_pct, "saving_per_month": saving_monthly, "saving_per_year": saving_yearly,
        "recommendation": f"Switch to {alt} to save ~{saving_pct}% (${saving_yearly}/yr).",
    }


def _ri_analysis(service, instance_type, region, engine="", operating_system="Linux"):
    results = _query_pricing(service, instance_type, region, engine, operating_system=operating_system)
    if not results or "error" in results[0]:
        return results
    r = results[0]
    od = r.get("price_per_hour", 0)
    if not od:
        return [{"error": "No On-Demand price found."}]
    od_monthly = od * 730
    od_yearly = od_monthly * 12
    analysis = {"instance_type": instance_type, "region": region, "on_demand_hourly": od, "on_demand_monthly": round(od_monthly, 2), "on_demand_yearly": round(od_yearly, 2), "options": []}
    ri_keys = [
        ("ri_1yr_no_upfront", "1yr No Upfront", 1), ("ri_1yr_partial_upfront", "1yr Partial Upfront", 1),
        ("ri_1yr_all_upfront", "1yr All Upfront", 1), ("ri_3yr_no_upfront", "3yr No Upfront", 3),
        ("ri_3yr_partial_upfront", "3yr Partial Upfront", 3), ("ri_3yr_all_upfront", "3yr All Upfront", 3),
    ]
    for key, label, years in ri_keys:
        eff = r.get(key)
        if not eff:
            continue
        eff_monthly = eff * 730
        saving_monthly = od_monthly - eff_monthly
        saving_pct = round((1 - eff / od) * 100, 1)
        # Get upfront cost: all_upfront has dedicated field, partial needs calculation
        upfront = 0
        if "all_upfront" in key:
            upfront = r.get(f"ri_{years}yr_all_upfront_total", 0) or 0
        elif "partial_upfront" in key:
            # For partial: upfront = (effective - hourly_component) * total_hours
            # hourly_component is stored in the effective rate, upfront is the remainder
            hourly_only_key = f"ri_{years}yr_no_upfront"
            hourly_only = r.get(hourly_only_key, eff)
            if hourly_only and hourly_only < od:
                total_hours = years * 8760
                upfront = round((eff - (eff_monthly - (od_monthly - saving_monthly)) / 730) * 0, 2)
                # Simpler: estimate upfront from effective rate vs no-upfront rate
                upfront = round((eff * total_hours - eff_monthly * 12 * years) * 0, 2)
                # Best estimate: effective_hourly * total_hours gives total cost, minus hourly portion
                upfront = 0  # Cannot reliably extract from effective rate alone
        breakeven_months = round(upfront / saving_monthly, 1) if saving_monthly > 0 and upfront > 0 else 0
        analysis["options"].append({
            "plan": label, "effective_hourly": round(eff, 4), "effective_monthly": round(eff_monthly, 2),
            "saving_vs_od_percent": saving_pct, "saving_per_month": round(saving_monthly, 2),
            "saving_per_year": round(saving_monthly * 12, 2),
            "upfront_cost": round(upfront, 2), "breakeven_months": breakeven_months,
        })
    return analysis


def _calculate_s3(storage_gb, storage_class="Standard", put_requests=0, get_requests=0, egress_gb=0):
    p = S3_PRICING.get(storage_class)
    if not p:
        return {"error": f"Unknown S3 class '{storage_class}'. Valid: {list(S3_PRICING.keys())}"}
    storage_cost = storage_gb * p["storage"]
    put_cost = (put_requests / 1000) * p["put_1k"]
    get_cost = (get_requests / 1000) * p["get_1k"]
    free_egress = 100
    paid_egress = max(0, egress_gb - free_egress)
    egress_cost = min(paid_egress, 10140) * 0.09 + max(0, paid_egress - 10140) * 0.085
    total = storage_cost + put_cost + get_cost + egress_cost
    return {
        "storage_class": storage_class, "storage_gb": storage_gb,
        "storage_cost": round(storage_cost, 2), "put_cost": round(put_cost, 2),
        "get_cost": round(get_cost, 2), "egress_cost": round(egress_cost, 2),
        "total_monthly": round(total, 2), "total_yearly": round(total * 12, 2),
        "note": "Prices based on us-east-1. Other regions +10-30%.",
    }


def _calculate_lambda(invocations, avg_duration_ms, memory_mb=128, architecture="x86"):
    gb_seconds = invocations * (memory_mb / 1024) * (avg_duration_ms / 1000)
    rate = 0.0000166667 if architecture == "x86" else 0.0000133334
    free_invocations = 1_000_000
    free_gb_seconds = 400_000
    request_cost = max(0, invocations - free_invocations) * 0.20 / 1_000_000
    compute_cost = max(0, gb_seconds - free_gb_seconds) * rate
    total = request_cost + compute_cost
    return {
        "invocations": invocations, "avg_duration_ms": avg_duration_ms,
        "memory_mb": memory_mb, "architecture": architecture,
        "gb_seconds": round(gb_seconds, 2),
        "request_cost": round(request_cost, 4), "compute_cost": round(compute_cost, 4),
        "total_monthly": round(total, 4), "total_yearly": round(total * 12, 2),
        "note": "Includes free tier deduction (1M requests + 400K GB-s/mo).",
    }


def _calculate_bedrock(model, input_tokens, output_tokens, tier="standard"):
    # Fuzzy match model name
    key = model.lower().strip().replace(" ", "-")
    pricing = BEDROCK_PRICING.get(key)
    if not pricing:
        # Try partial match
        for k, v in BEDROCK_PRICING.items():
            if key in k or k in key:
                pricing = v
                key = k
                break
    if not pricing:
        return {"error": f"Unknown model '{model}'. Use list_bedrock_models to see available models."}

    multiplier = {"standard": 1.0, "priority": 1.75, "flex": 0.5, "batch": 0.5}.get(tier.lower(), 1.0)
    input_cost = (input_tokens / 1_000_000) * pricing["input"] * multiplier
    output_cost = (output_tokens / 1_000_000) * pricing["output"] * multiplier
    total = input_cost + output_cost
    return {
        "model": key, "provider": pricing["provider"], "tier": tier,
        "input_tokens": input_tokens, "output_tokens": output_tokens,
        "input_price_per_1m": round(pricing["input"] * multiplier, 4),
        "output_price_per_1m": round(pricing["output"] * multiplier, 4),
        "input_cost": round(input_cost, 6), "output_cost": round(output_cost, 6),
        "total_cost": round(total, 6),
        "pricing_date": BEDROCK_PRICING_DATE,
        "region": "us-east-1 (reference)",
        "note": "Built-in reference pricing. AWS Price List API has delays for Bedrock models.",
    }


def _list_bedrock_models():
    models = []
    for key, v in sorted(BEDROCK_PRICING.items()):
        models.append({
            "model": key, "provider": v["provider"],
            "input_per_1m_tokens": v["input"], "output_per_1m_tokens": v["output"],
        })
    return {"models": models, "count": len(models), "pricing_date": BEDROCK_PRICING_DATE,
            "region": "us-east-1 (Standard tier)", "source": "https://aws.amazon.com/bedrock/pricing/"}


# ── MCP Tool wrappers ──────────────────────────────────────────

@mcp.tool
def query_pricing(
    service: str, instance_type: str, region: str,
    engine: str = "", deployment: str = "", operating_system: str = "Linux",
) -> list[dict]:
    """Query real-time pricing for an AWS instance type.

    Returns On-Demand price + 6 Reserved Instance options.
    Supports 19 services: ec2, rds, elasticache, opensearch, redshift, neptune,
    docdb, memorydb, mq, dax, sagemaker, emr, gamelift, appstream, workspaces, ecs, eks, evs.
    Region accepts: Chinese (东京), English (tokyo), or code (ap-northeast-1).
    """
    return _query_pricing(service, instance_type, region, engine, deployment, operating_system)


@mcp.tool
def compare_regions(
    service: str, instance_type: str, regions: list[str],
    engine: str = "", operating_system: str = "Linux",
) -> list[dict]:
    """Compare pricing for the same instance type across multiple regions.

    Pass regions as a list: ["tokyo", "virginia", "singapore"].
    Returns results sorted by price, cheapest first.
    """
    return _compare_regions(service, instance_type, regions, engine, operating_system)


@mcp.tool
def batch_compare(
    service: str, instance_types: list[str], region: str,
    engine: str = "", operating_system: str = "Linux",
) -> list[dict]:
    """Compare pricing for multiple instance types in the same region.

    Pass types as a list: ["c6g.xlarge", "c6g.2xlarge", "c6g.4xlarge"].
    """
    return _batch_compare(service, instance_types, region, engine, operating_system)


@mcp.tool
def list_types(service: str, region: str, filter_keyword: str = "") -> list[str]:
    """List available instance types for a service in a specific region.

    Optionally filter by keyword (e.g. "c6g", "db.r6g").
    """
    return _list_types(service, region, filter_keyword)


@mcp.tool
def get_regions() -> list[dict]:
    """List all 34 supported AWS regions with codes and names."""
    return _get_regions()


@mcp.tool
def get_services() -> list[dict]:
    """List all 19 supported AWS services with their service codes."""
    return _get_services()


@mcp.tool
def graviton_recommend(
    service: str, instance_type: str, region: str,
    engine: str = "", operating_system: str = "Linux",
) -> dict:
    """Recommend Graviton (ARM) alternative for an x86 instance type.

    Compares real-time pricing and calculates savings percentage, monthly and yearly savings.
    Example: c6i.xlarge → c7g.xlarge with ~20% savings.
    """
    return _graviton_recommend(service, instance_type, region, engine, operating_system)


@mcp.tool
def ri_analysis(
    service: str, instance_type: str, region: str,
    engine: str = "", operating_system: str = "Linux",
) -> dict:
    """Analyze Reserved Instance break-even vs On-Demand pricing.

    Returns all 6 RI options with: effective hourly rate, saving %, monthly savings,
    upfront cost, and break-even months.
    """
    return _ri_analysis(service, instance_type, region, engine, operating_system)


@mcp.tool
def calculate_s3(
    storage_gb: float, storage_class: str = "Standard",
    put_requests: int = 0, get_requests: int = 0, egress_gb: float = 0,
) -> dict:
    """Calculate S3 monthly cost using built-in pricing formulas.

    Supports 7 storage classes: Standard, Intelligent-Tiering, Standard-IA,
    One Zone-IA, Glacier Instant, Glacier Flexible, Glacier Deep Archive.
    Prices based on us-east-1.
    """
    return _calculate_s3(storage_gb, storage_class, put_requests, get_requests, egress_gb)


@mcp.tool
def calculate_lambda(
    invocations: int, avg_duration_ms: int,
    memory_mb: int = 128, architecture: str = "x86",
) -> dict:
    """Calculate Lambda monthly cost using built-in pricing formulas.

    Includes free tier deduction. Architecture: 'x86' or 'arm' (ARM is 20% cheaper).
    """
    return _calculate_lambda(invocations, avg_duration_ms, memory_mb, architecture)


@mcp.tool
def calculate_bedrock(
    model: str, input_tokens: int, output_tokens: int, tier: str = "standard",
) -> dict:
    """Calculate Amazon Bedrock model inference cost.

    Uses built-in reference pricing (updated 2026-03) since AWS Price List API
    has delays for Bedrock models. Supports 20 models from 10 providers.
    Tiers: 'standard' (default), 'priority' (+75%), 'flex' (-50%), 'batch' (-50%).
    Example models: 'nova-pro', 'claude-3.5-sonnet', 'llama-4-maverick', 'deepseek-v3.2'.
    Use list_bedrock_models to see all available models.
    """
    return _calculate_bedrock(model, input_tokens, output_tokens, tier)


@mcp.tool
def list_bedrock_models() -> dict:
    """List all Bedrock models with built-in reference pricing.

    Returns model names, providers, and per-1M-token prices (us-east-1 Standard tier).
    Prices are manually maintained since AWS Price List API has delays for Bedrock.
    """
    return _list_bedrock_models()


if __name__ == "__main__":
    mcp.run()
