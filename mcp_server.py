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


if __name__ == "__main__":
    mcp.run()
