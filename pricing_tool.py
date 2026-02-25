#!/usr/bin/env python3
"""AWS Pricing Query Tool - Real-time pricing with local cache."""

import argparse, hashlib, json, os, sys, time
import boto3

PRICING_REGION = "us-east-1"
CACHE_DIR = os.path.expanduser("~/.cache/aws-pricing")
CACHE_TTL = 7 * 86400  # 7 days

REGION_MAP = {
    # US
    "us-east-1": "US East (N. Virginia)", "us-east-2": "US East (Ohio)",
    "us-west-1": "US West (N. California)", "us-west-2": "US West (Oregon)",
    # Asia Pacific
    "ap-east-1": "Asia Pacific (Hong Kong)", "ap-east-2": "Asia Pacific (Taipei)",
    "ap-south-1": "Asia Pacific (Mumbai)", "ap-south-2": "Asia Pacific (Hyderabad)",
    "ap-southeast-1": "Asia Pacific (Singapore)", "ap-southeast-2": "Asia Pacific (Sydney)",
    "ap-southeast-3": "Asia Pacific (Jakarta)", "ap-southeast-4": "Asia Pacific (Melbourne)",
    "ap-southeast-5": "Asia Pacific (Malaysia)", "ap-southeast-6": "Asia Pacific (Thailand)",
    "ap-southeast-7": "Asia Pacific (New Zealand)",
    "ap-northeast-1": "Asia Pacific (Tokyo)", "ap-northeast-2": "Asia Pacific (Seoul)",
    "ap-northeast-3": "Asia Pacific (Osaka)",
    # Europe
    "eu-central-1": "EU (Frankfurt)", "eu-central-2": "Europe (Zurich)",
    "eu-west-1": "EU (Ireland)", "eu-west-2": "EU (London)",
    "eu-west-3": "EU (Paris)", "eu-south-1": "EU (Milan)",
    "eu-south-2": "Europe (Spain)", "eu-north-1": "EU (Stockholm)",
    # Americas
    "ca-central-1": "Canada (Central)", "ca-west-1": "Canada West (Calgary)",
    "sa-east-1": "South America (Sao Paulo)", "mx-central-1": "Mexico (Central)",
    # Middle East / Africa / Israel
    "af-south-1": "Africa (Cape Town)", "il-central-1": "Israel (Tel Aviv)",
    "me-south-1": "Middle East (Bahrain)", "me-central-1": "Middle East (UAE)",
}

REGION_ALIASES = {
    # Chinese
    "东京": "ap-northeast-1", "新加坡": "ap-southeast-1", "首尔": "ap-northeast-2",
    "大阪": "ap-northeast-3", "香港": "ap-east-1", "台北": "ap-east-2",
    "孟买": "ap-south-1", "海得拉巴": "ap-south-2",
    "悉尼": "ap-southeast-2", "雅加达": "ap-southeast-3", "墨尔本": "ap-southeast-4",
    "马来西亚": "ap-southeast-5", "泰国": "ap-southeast-6", "曼谷": "ap-southeast-6",
    "新西兰": "ap-southeast-7", "奥克兰": "ap-southeast-7",
    "法兰克福": "eu-central-1", "苏黎世": "eu-central-2",
    "爱尔兰": "eu-west-1", "伦敦": "eu-west-2", "巴黎": "eu-west-3",
    "米兰": "eu-south-1", "西班牙": "eu-south-2", "斯德哥尔摩": "eu-north-1",
    "弗吉尼亚": "us-east-1", "俄亥俄": "us-east-2",
    "加利福尼亚": "us-west-1", "俄勒冈": "us-west-2",
    "开普敦": "af-south-1", "特拉维夫": "il-central-1",
    "巴林": "me-south-1", "阿联酋": "me-central-1",
    "圣保罗": "sa-east-1", "加拿大": "ca-central-1", "卡尔加里": "ca-west-1",
    "墨西哥": "mx-central-1", "北京": "cn-north-1", "宁夏": "cn-northwest-1",
    # English
    "tokyo": "ap-northeast-1", "singapore": "ap-southeast-1", "seoul": "ap-northeast-2",
    "osaka": "ap-northeast-3", "hongkong": "ap-east-1", "taipei": "ap-east-2",
    "mumbai": "ap-south-1", "hyderabad": "ap-south-2",
    "sydney": "ap-southeast-2", "jakarta": "ap-southeast-3", "melbourne": "ap-southeast-4",
    "malaysia": "ap-southeast-5", "thailand": "ap-southeast-6", "bangkok": "ap-southeast-6",
    "newzealand": "ap-southeast-7", "auckland": "ap-southeast-7",
    "frankfurt": "eu-central-1", "zurich": "eu-central-2",
    "ireland": "eu-west-1", "london": "eu-west-2", "paris": "eu-west-3",
    "milan": "eu-south-1", "spain": "eu-south-2", "stockholm": "eu-north-1",
    "virginia": "us-east-1", "ohio": "us-east-2",
    "california": "us-west-1", "oregon": "us-west-2",
    "capetown": "af-south-1", "telaviv": "il-central-1",
    "bahrain": "me-south-1", "uae": "me-central-1",
    "saopaulo": "sa-east-1", "canada": "ca-central-1", "calgary": "ca-west-1",
    "mexico": "mx-central-1",
}

SERVICE_CODES = {
    "ec2": "AmazonEC2", "rds": "AmazonRDS", "elasticache": "AmazonElastiCache",
    "opensearch": "AmazonES", "redshift": "AmazonRedshift",
    "neptune": "AmazonNeptune", "docdb": "AmazonDocDB", "memorydb": "AmazonMemoryDB",
    "mq": "AmazonMQ", "sagemaker": "AmazonSageMaker",
    "dax": "AmazonDAX", "gamelift": "AmazonGameLift", "emr": "ElasticMapReduce",
    "timestream": "AmazonTimestream", "appstream": "AmazonAppStream",
    "workspaces": "AmazonWorkSpacesInstances", "ecs": "AmazonECS",
    "eks": "AmazonEKS", "evs": "AmazonEVS",
}

RDS_ENGINES = {
    "aurora-mysql": "Aurora MySQL", "aurora-postgresql": "Aurora PostgreSQL",
    "mysql": "MySQL", "postgresql": "PostgreSQL", "mariadb": "MariaDB",
    "oracle-ee": "Oracle", "oracle-se2": "Oracle",
    "sqlserver-ee": "SQL Server", "sqlserver-se": "SQL Server", "sqlserver-web": "SQL Server",
}

def _cache_key(prefix, *parts):
    h = hashlib.md5(json.dumps(parts, sort_keys=True).encode()).hexdigest()[:12]
    return os.path.join(CACHE_DIR, f"{prefix}_{h}.json")

def cache_get(path):
    try:
        if os.path.exists(path) and (time.time() - os.path.getmtime(path)) < CACHE_TTL:
            with open(path) as f:
                return json.load(f)
    except Exception:
        pass
    return None

def cache_put(path, data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False)

def get_client(profile=None):
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    return session.client("pricing", region_name=PRICING_REGION)

def resolve_region(region):
    return REGION_ALIASES.get(region.lower().strip(), region)

def resolve_location(region):
    return REGION_MAP.get(resolve_region(region), region)

def query_products(client, service_code, filters, use_cache=True):
    cpath = _cache_key("products", service_code, filters)
    if use_cache:
        cached = cache_get(cpath)
        if cached is not None:
            print("  (cached)", file=sys.stderr)
            return cached
    api_filters = [{"Type": "TERM_MATCH", "Field": k, "Value": v} for k, v in filters.items() if v]
    products = []
    try:
        paginator = client.get_paginator("get_products")
        for page in paginator.paginate(ServiceCode=service_code, Filters=api_filters):
            for item in page["PriceList"]:
                products.append(json.loads(item) if isinstance(item, str) else item)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return products
    if products:
        cache_put(cpath, products)
    return products

def list_instance_types(client, service_code, location):
    cpath = _cache_key("types", service_code, location)
    cached = cache_get(cpath)
    if cached is not None:
        return cached
    types = []
    try:
        paginator = client.get_paginator("get_attribute_values")
        for page in paginator.paginate(ServiceCode=service_code, AttributeName="instanceType"):
            for v in page.get("AttributeValues", []):
                types.append(v["Value"])
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return types
    types.sort()
    if types:
        cache_put(cpath, types)
    return types

TERM_HOURS = {"1yr": 8760, "3yr": 26280}

def extract_pricing(product):
    attrs = product.get("product", {}).get("attributes", {})
    terms = product.get("terms", {})
    result = {
        "instance_type": attrs.get("instanceType", attrs.get("instancetype", "")),
        "vcpu": attrs.get("vcpu", ""), "memory": attrs.get("memory", ""),
        "region": attrs.get("regionCode", attrs.get("location", "")),
        "os": attrs.get("operatingSystem", attrs.get("cacheEngine", attrs.get("databaseEngine", ""))),
        "storage": attrs.get("storage", attrs.get("storageType", "")),
        "network": attrs.get("networkPerformance", ""),
    }
    for _, term in terms.get("OnDemand", {}).items():
        for _, dim in term.get("priceDimensions", {}).items():
            try:
                price = float(dim.get("pricePerUnit", {}).get("USD", "0"))
            except (ValueError, TypeError):
                continue
            if price > 0:
                result["price_per_hour"] = price
                result["price_unit"] = dim.get("unit", "Hrs")
                result["description"] = dim.get("description", "")
                break
    ri_map = {}
    for _, term in terms.get("Reserved", {}).items():
        ta = term.get("termAttributes", {})
        length, option = ta.get("LeaseContractLength", ""), ta.get("PurchaseOption", "")
        key = f"{length}_{option}".replace(" ", "_")
        hourly, upfront = 0.0, 0.0
        for _, dim in term.get("priceDimensions", {}).items():
            try:
                p = float(dim.get("pricePerUnit", {}).get("USD", "0"))
            except (ValueError, TypeError):
                continue
            if "Hrs" in dim.get("unit", ""):
                hourly = p
            elif "Quantity" in dim.get("unit", ""):
                upfront = p
        hours = TERM_HOURS.get(length, 8760)
        effective = hourly + (upfront / hours) if (hourly > 0 or upfront > 0) else 0
        if effective > 0:
            ri_map[key] = effective
            ri_map[f"{key}_upfront"] = upfront
    for k in ["1yr_No_Upfront", "1yr_Partial_Upfront", "1yr_All_Upfront",
              "3yr_No_Upfront", "3yr_Partial_Upfront", "3yr_All_Upfront"]:
        result[f"ri_{k.lower()}"] = ri_map.get(k)
    result["ri_1yr_all_upfront_total"] = ri_map.get("1yr_All_Upfront_upfront")
    result["ri_3yr_all_upfront_total"] = ri_map.get("3yr_All_Upfront_upfront")
    return result

def dedup_results(results):
    seen, unique = set(), []
    for r in results:
        if not r.get("price_per_hour"): continue
        key = (r["instance_type"], r["os"], r.get("price_per_hour"))
        if key not in seen:
            seen.add(key); unique.append(r)
    unique.sort(key=lambda x: x.get("price_per_hour", 0))
    return unique

def fmt(price):
    return f"${price:.4f}/hr (${price * 730:.2f}/mo)" if price else "N/A"

def _print_ri(r, key, label):
    val = r.get(f"ri_{key}")
    if not val or not r.get("price_per_hour"): return
    saving = (1 - val / r["price_per_hour"]) * 100
    extra = ""
    if "all_upfront" in key:
        total = r.get(f"ri_{key}_total")
        if total: extra = f"  [预付${total:,.0f}]"
    print(f"  {label:<14} : {fmt(val)}  ({saving:.0f}% off){extra}")

def print_results(results, service, output_json=False):
    unique = dedup_results(results)
    if output_json:
        print(json.dumps(unique, indent=2, ensure_ascii=False)); return
    if not unique:
        print("No pricing results found."); return
    print(f"\n{'='*100}")
    print(f" AWS {service.upper()} Pricing | {len(unique)} result(s)")
    print(f"{'='*100}")
    for r in unique:
        print(f"\n  Instance Type : {r['instance_type']}")
        for k, label in [("vcpu","vCPU"),("memory","Memory"),("network","Network"),("os","Engine/OS"),("storage","Storage")]:
            if r.get(k): print(f"  {label:<14} : {r[k]}")
        print(f"  {'On-Demand':<14} : {fmt(r.get('price_per_hour'))}")
        _print_ri(r, "1yr_no_upfront", "RI 1yr NoUp")
        _print_ri(r, "1yr_partial_upfront", "RI 1yr PartUp")
        _print_ri(r, "1yr_all_upfront", "RI 1yr AllUp")
        _print_ri(r, "3yr_partial_upfront", "RI 3yr PartUp")
        _print_ri(r, "3yr_all_upfront", "RI 3yr AllUp")
        print(f"  {'─'*60}")
    print()

def build_filters(service, args):
    f = {"location": resolve_location(args.region)}
    if args.instance_type: f["instanceType"] = args.instance_type
    if service == "ec2":
        f.update({"operatingSystem": getattr(args, "os", "Linux") or "Linux",
                  "tenancy": "Shared", "preInstalledSw": "NA", "capacitystatus": "Used"})
    elif service == "rds":
        f["deploymentOption"] = getattr(args, "deployment", None) or "Single-AZ"
        engine = getattr(args, "engine", None)
        if engine: f["databaseEngine"] = RDS_ENGINES.get(engine, engine)
    elif service == "elasticache":
        engine = getattr(args, "engine", None)
        if engine: f["cacheEngine"] = engine.capitalize()
    elif service == "redshift":
        f["productFamily"] = "Compute Instance"
    return f

def cmd_query(args):
    client = get_client(args.profile)
    sc = SERVICE_CODES.get(args.service)
    if not sc: print(f"Unknown service: {args.service}"); sys.exit(1)
    filters = build_filters(args.service, args)
    no_cache = getattr(args, "no_cache", False)
    products = query_products(client, sc, filters, use_cache=not no_cache)
    print_results([extract_pricing(p) for p in products], args.service, getattr(args, "json", False))

def cmd_batch(args):
    client = get_client(args.profile)
    sc = SERVICE_CODES.get(args.service)
    if not sc: print(f"Unknown service: {args.service}"); sys.exit(1)
    no_cache = getattr(args, "no_cache", False)
    types = [t.strip() for t in args.instance_types.split(",")]
    all_results = []
    for it in types:
        args.instance_type = it
        filters = build_filters(args.service, args)
        products = query_products(client, sc, filters, use_cache=not no_cache)
        all_results.extend([extract_pricing(p) for p in products])
    if getattr(args, "json", False):
        print(json.dumps(dedup_results(all_results), indent=2, ensure_ascii=False))
    else:
        unique = dedup_results(all_results)
        if not unique: print("No pricing results found."); return
        print(f"\n{'='*100}")
        print(f" AWS {args.service.upper()} Batch Pricing | {args.region} | {len(unique)} result(s)")
        print(f"{'='*100}")
        print(f"\n  {'Instance Type':<25} {'vCPU':>6} {'Memory':>12} {'On-Demand/hr':>15} {'Monthly':>12} {'RI 1yr NoUp':>15}")
        print(f"  {'─'*90}")
        for r in unique:
            ri = fmt(r.get("ri_1yr_no_upfront")).split(" ")[0] if r.get("ri_1yr_no_upfront") else "N/A"
            print(f"  {r['instance_type']:<25} {r.get('vcpu',''):>6} {r.get('memory',''):>12} ${r['price_per_hour']:>12.4f} ${r['price_per_hour']*730:>10.2f} {ri:>15}")
        print()

def cmd_compare(args):
    client = get_client(args.profile)
    sc = SERVICE_CODES.get(args.service)
    no_cache = getattr(args, "no_cache", False)
    regions = [r.strip() for r in args.regions.split(",")]
    print(f"\n{'='*90}")
    print(f" {args.service.upper()} {args.instance_type} - Cross-Region Comparison")
    print(f"{'='*90}")
    print(f"\n  {'Region':<25} {'On-Demand/hr':>15} {'Monthly':>12} {'RI 1yr NoUp/hr':>16} {'RI Monthly':>12}")
    print(f"  {'─'*82}")
    rows = []
    for region in regions:
        region = resolve_region(region)
        args.region = region
        filters = build_filters(args.service, args)
        products = query_products(client, sc, filters, use_cache=not no_cache)
        for p in products:
            r = extract_pricing(p)
            if r.get("price_per_hour"):
                rows.append((region, r["price_per_hour"], r.get("ri_1yr_no_upfront"))); break
    rows.sort(key=lambda x: x[1])
    cheapest = rows[0][1] if rows else 0
    for region, price, ri in rows:
        marker = " ★" if price == cheapest and len(rows) > 1 else ""
        ri_str = f"${ri:.4f}" if ri else "N/A"
        ri_mo = f"${ri*730:.2f}" if ri else "N/A"
        print(f"  {region:<25} ${price:>12.4f} ${price*730:>10.2f} {ri_str:>16} {ri_mo:>12}{marker}")
    print()

def cmd_list(args):
    client = get_client(args.profile)
    sc = SERVICE_CODES.get(args.service)
    if not sc: print(f"Unknown service: {args.service}"); return
    types = list_instance_types(client, sc, resolve_location(args.region))
    prefix = args.filter.lower() if args.filter else ""
    if prefix: types = [t for t in types if t.lower().startswith(prefix) or prefix in t.lower()]
    print(f"\n{args.service.upper()} instance types ({len(types)} found):")
    print(f"  (Note: types are global, not all may be available in every region)")
    for t in types: print(f"  {t}")
    print()

def cmd_refresh(args):
    if not os.path.exists(CACHE_DIR): print("No cache to clear."); return
    count = 0
    for f in os.listdir(CACHE_DIR):
        if f.endswith(".json"): os.remove(os.path.join(CACHE_DIR, f)); count += 1
    print(f"Cleared {count} cached files from {CACHE_DIR}")

def cmd_cache_info(args):
    if not os.path.exists(CACHE_DIR): print("No cache directory."); return
    files = [f for f in os.listdir(CACHE_DIR) if f.endswith(".json")]
    total_size = sum(os.path.getsize(os.path.join(CACHE_DIR, f)) for f in files)
    print(f"\nCache: {CACHE_DIR}\nFiles: {len(files)}\nSize:  {total_size / 1024:.1f} KB\nTTL:   {CACHE_TTL // 86400} days")
    if files:
        from datetime import datetime
        oldest = min(os.path.getmtime(os.path.join(CACHE_DIR, f)) for f in files)
        newest = max(os.path.getmtime(os.path.join(CACHE_DIR, f)) for f in files)
        print(f"Oldest: {datetime.fromtimestamp(oldest).strftime('%Y-%m-%d %H:%M')}")
        print(f"Newest: {datetime.fromtimestamp(newest).strftime('%Y-%m-%d %H:%M')}")
    print()

def main():
    parser = argparse.ArgumentParser(description="AWS Pricing Query Tool (with local cache)")
    parser.add_argument("--profile", help="AWS CLI profile name")
    parser.add_argument("--no-cache", action="store_true", help="Skip cache, query API directly")
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("query", help="Query pricing for any service")
    p.add_argument("service", choices=SERVICE_CODES.keys())
    p.add_argument("-t", "--instance-type", required=True)
    p.add_argument("-r", "--region", required=True)
    p.add_argument("-e", "--engine", help="Engine (RDS/ElastiCache)")
    p.add_argument("-d", "--deployment", help="Single-AZ / Multi-AZ")
    p.add_argument("--os", default="Linux", help="OS for EC2")
    p.add_argument("--json", action="store_true", help="JSON output")
    p = sub.add_parser("batch", help="Batch query multiple instance types")
    p.add_argument("service", choices=SERVICE_CODES.keys())
    p.add_argument("-t", "--instance-types", required=True, help="Comma-separated types")
    p.add_argument("-r", "--region", required=True)
    p.add_argument("-e", "--engine"); p.add_argument("-d", "--deployment")
    p.add_argument("--os", default="Linux"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("compare", help="Compare across regions")
    p.add_argument("service", choices=SERVICE_CODES.keys())
    p.add_argument("-t", "--instance-type", required=True)
    p.add_argument("-r", "--regions", required=True, help="Comma-separated regions")
    p.add_argument("-e", "--engine"); p.add_argument("-d", "--deployment")
    p.add_argument("--os", default="Linux")
    p = sub.add_parser("list", help="List instance types (fast)")
    p.add_argument("service", choices=SERVICE_CODES.keys())
    p.add_argument("-r", "--region", required=True)
    p.add_argument("-f", "--filter", help="Prefix filter (e.g. c6in, db.r6g)")
    sub.add_parser("refresh", help="Clear local price cache")
    sub.add_parser("cache-info", help="Show cache status")
    args = parser.parse_args()
    if not args.command: parser.print_help(); sys.exit(1)
    cmds = {"query": cmd_query, "batch": cmd_batch, "compare": cmd_compare,
            "list": cmd_list, "refresh": cmd_refresh, "cache-info": cmd_cache_info}
    cmds[args.command](args)

if __name__ == "__main__":
    main()
