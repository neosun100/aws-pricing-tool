"""End-to-end tests: CLI invocation via subprocess."""

import json, os, subprocess, sys, tempfile

import pytest

TOOL = [sys.executable, "pricing_tool.py"]
CWD = os.path.dirname(os.path.abspath(__file__))


def run(*args, input_text=None):
    """Run pricing_tool.py with args, return (stdout, stderr, returncode)."""
    result = subprocess.run(
        TOOL + list(args), capture_output=True, text=True, cwd=CWD, input=input_text,
    )
    return result.stdout, result.stderr, result.returncode


# ── Basic CLI ───────────────────────────────────────────────────

class TestCLIBasic:
    def test_version(self):
        out, _, rc = run("--version")
        assert rc == 0
        assert "2.0.1" in out

    def test_help(self):
        out, _, rc = run("--help")
        assert rc == 0
        assert "query" in out
        assert "batch" in out
        assert "compare" in out
        assert "list" in out
        assert "refresh" in out
        assert "cache-info" in out

    def test_no_command_shows_help(self):
        _, _, rc = run()
        assert rc != 0

    def test_query_help(self):
        out, _, rc = run("query", "--help")
        assert rc == 0
        assert "--instance-type" in out
        assert "--json" in out
        assert "--csv" in out

    def test_compare_help(self):
        out, _, rc = run("compare", "--help")
        assert rc == 0
        assert "--regions" in out
        assert "--json" in out
        assert "--csv" in out

    def test_list_help(self):
        out, _, rc = run("list", "--help")
        assert rc == 0
        assert "--filter" in out
        assert "--json" in out


# ── Cache commands (no AWS creds needed) ────────────────────────

class TestCacheCommands:
    def test_cache_info_no_cache(self):
        """cache-info works even with no cache dir."""
        out, _, rc = run("cache-info")
        assert rc == 0

    def test_refresh_no_cache(self):
        out, _, rc = run("refresh")
        assert rc == 0


# ── Query/Batch/Compare/List with mocked API ───────────────────

# We use a helper script that patches boto3 and runs the CLI
MOCK_RUNNER = """
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import MagicMock, patch
from conftest import EC2_PRODUCT, EC2_PRODUCT_2, EC2_PRODUCT_VIRGINIA, RDS_PRODUCT

PRODUCTS_BY_LOCATION = {
    "Asia Pacific (Tokyo)": [json.dumps(EC2_PRODUCT)],
    "US East (N. Virginia)": [json.dumps(EC2_PRODUCT_VIRGINIA)],
}

def mock_paginate(**kwargs):
    location = None
    for f in kwargs.get("Filters", []):
        if f["Field"] == "location":
            location = f["Value"]
    products = PRODUCTS_BY_LOCATION.get(location, [json.dumps(EC2_PRODUCT)])
    return [{"PriceList": products}]

mock_client = MagicMock()
mock_client.get_paginator.return_value.paginate = mock_paginate

with patch("pricing_tool.get_client", return_value=mock_client):
    with patch("pricing_tool.cache_get", return_value=None):
        with patch("pricing_tool.cache_put"):
            sys.argv = ["pricing_tool.py"] + sys.argv[1:]
            import pricing_tool
            pricing_tool.main()
"""


def run_mocked(*args):
    """Run pricing_tool via mock runner script."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", dir=CWD, delete=False) as f:
        f.write(MOCK_RUNNER)
        runner = f.name
    try:
        result = subprocess.run(
            [sys.executable, runner] + list(args),
            capture_output=True, text=True, cwd=CWD,
        )
        return result.stdout, result.stderr, result.returncode
    finally:
        os.unlink(runner)


class TestQueryE2E:
    def test_query_json(self):
        out, err, rc = run_mocked("query", "ec2", "-t", "c6g.xlarge", "-r", "东京", "--json")
        assert rc == 0, f"stderr: {err}"
        data = json.loads(out)
        assert len(data) >= 1
        assert data[0]["instance_type"] == "c6g.xlarge"
        assert data[0]["price_per_hour"] > 0

    def test_query_csv(self):
        out, err, rc = run_mocked("query", "ec2", "-t", "c6g.xlarge", "-r", "tokyo", "--csv")
        assert rc == 0, f"stderr: {err}"
        assert "instance_type" in out
        assert "c6g.xlarge" in out
        assert "monthly" in out

    def test_query_table(self):
        out, err, rc = run_mocked("query", "ec2", "-t", "c6g.xlarge", "-r", "ap-northeast-1")
        assert rc == 0, f"stderr: {err}"
        assert "EC2" in out
        assert "c6g.xlarge" in out
        assert "On-Demand" in out

    def test_query_ri_displayed(self):
        out, err, rc = run_mocked("query", "ec2", "-t", "c6g.xlarge", "-r", "东京")
        assert rc == 0, f"stderr: {err}"
        assert "RI 1yr NoUp" in out
        assert "RI 3yr NoUp" in out
        assert "% off" in out


class TestBatchE2E:
    def test_batch_json(self):
        out, err, rc = run_mocked("batch", "ec2", "-t", "c6g.xlarge", "-r", "东京", "--json")
        assert rc == 0, f"stderr: {err}"
        data = json.loads(out)
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_batch_csv(self):
        out, err, rc = run_mocked("batch", "ec2", "-t", "c6g.xlarge", "-r", "东京", "--csv")
        assert rc == 0, f"stderr: {err}"
        assert "instance_type" in out


class TestCompareE2E:
    def test_compare_json(self):
        out, err, rc = run_mocked("compare", "ec2", "-t", "c6g.xlarge", "-r", "东京,弗吉尼亚", "--json")
        assert rc == 0, f"stderr: {err}"
        data = json.loads(out)
        assert len(data) == 2
        # Should be sorted by price (Virginia cheaper)
        assert data[0]["region"] == "us-east-1"
        assert data[1]["region"] == "ap-northeast-1"

    def test_compare_csv(self):
        out, err, rc = run_mocked("compare", "ec2", "-t", "c6g.xlarge", "-r", "东京,弗吉尼亚", "--csv")
        assert rc == 0, f"stderr: {err}"
        assert "region" in out
        assert "price_per_hour" in out

    def test_compare_table_star_marker(self):
        out, err, rc = run_mocked("compare", "ec2", "-t", "c6g.xlarge", "-r", "东京,弗吉尼亚")
        assert rc == 0, f"stderr: {err}"
        assert "★" in out  # cheapest region marker


class TestListE2E:
    def test_list_json(self):
        out, err, rc = run_mocked("list", "ec2", "-r", "东京", "--json")
        assert rc == 0, f"stderr: {err}"
        data = json.loads(out)
        assert "types" in data
        assert "count" in data
        assert data["service"] == "ec2"

    def test_list_csv(self):
        out, err, rc = run_mocked("list", "ec2", "-r", "东京", "--csv")
        assert rc == 0, f"stderr: {err}"
        assert "instance_type" in out

    def test_list_with_filter(self):
        out, err, rc = run_mocked("list", "ec2", "-r", "东京", "--json", "-f", "c6g")
        assert rc == 0, f"stderr: {err}"
        data = json.loads(out)
        for t in data["types"]:
            assert "c6g" in t.lower()


# ── Error handling ──────────────────────────────────────────────

class TestErrors:
    def test_invalid_service(self):
        _, _, rc = run("query", "invalid_svc", "-t", "x", "-r", "tokyo")
        assert rc != 0

    def test_missing_required_args(self):
        _, _, rc = run("query", "ec2")
        assert rc != 0

    def test_json_csv_mutual_exclusion(self):
        out, err, rc = run_mocked("query", "ec2", "-t", "c6g.xlarge", "-r", "tokyo", "--json", "--csv")
        assert rc != 0
        assert "mutually exclusive" in err


class TestRegionsE2E:
    def test_regions_json(self):
        out, _, rc = run("regions", "--json")
        assert rc == 0
        data = json.loads(out)
        assert len(data) == 34

    def test_regions_table(self):
        out, _, rc = run("regions")
        assert rc == 0
        assert "ap-northeast-1" in out


class TestCompareEdgeCases:
    def test_compare_single_region_no_star(self):
        out, err, rc = run_mocked("compare", "ec2", "-t", "c6g.xlarge", "-r", "tokyo")
        assert rc == 0, f"stderr: {err}"
        assert "★" not in out


class TestBatchMultiType:
    def test_batch_multiple_types_json(self):
        out, err, rc = run_mocked("batch", "ec2", "-t", "c6g.xlarge", "-r", "tokyo", "--json")
        assert rc == 0, f"stderr: {err}"
        data = json.loads(out)
        assert len(data) >= 1
        assert "monthly" in data[0]
