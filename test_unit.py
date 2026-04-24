"""Unit tests for pricing_tool.py core functions."""

import json, os, tempfile, time
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest
import pricing_tool as pt
from conftest import (
    EC2_PRODUCT, EC2_PRODUCT_2, EC2_PRODUCT_ZERO, RDS_PRODUCT, EC2_PRODUCT_VIRGINIA,
    ELASTICACHE_PRODUCT,
)


# ── resolve_region ──────────────────────────────────────────────

class TestResolveRegion:
    def test_chinese_alias(self):
        assert pt.resolve_region("东京") == "ap-northeast-1"
        assert pt.resolve_region("弗吉尼亚") == "us-east-1"
        assert pt.resolve_region("新加坡") == "ap-southeast-1"

    def test_english_alias(self):
        assert pt.resolve_region("tokyo") == "ap-northeast-1"
        assert pt.resolve_region("virginia") == "us-east-1"
        assert pt.resolve_region("singapore") == "ap-southeast-1"

    def test_case_insensitive(self):
        assert pt.resolve_region("Tokyo") == "ap-northeast-1"
        assert pt.resolve_region("VIRGINIA") == "us-east-1"

    def test_raw_region_code_passthrough(self):
        assert pt.resolve_region("ap-northeast-1") == "ap-northeast-1"
        assert pt.resolve_region("us-east-1") == "us-east-1"

    def test_whitespace_stripped(self):
        assert pt.resolve_region("  tokyo  ") == "ap-northeast-1"

    def test_unknown_returns_as_is(self):
        assert pt.resolve_region("unknown-region") == "unknown-region"


# ── resolve_location ────────────────────────────────────────────

class TestResolveLocation:
    def test_region_code(self):
        assert pt.resolve_location("ap-northeast-1") == "Asia Pacific (Tokyo)"
        assert pt.resolve_location("us-east-1") == "US East (N. Virginia)"

    def test_alias_to_location(self):
        assert pt.resolve_location("东京") == "Asia Pacific (Tokyo)"
        assert pt.resolve_location("tokyo") == "Asia Pacific (Tokyo)"

    def test_unknown_passthrough(self):
        assert pt.resolve_location("unknown") == "unknown"


# ── cache functions ─────────────────────────────────────────────

class TestCache:
    def test_cache_key_deterministic(self):
        k1 = pt._cache_key("test", "a", "b")
        k2 = pt._cache_key("test", "a", "b")
        assert k1 == k2
        assert k1.endswith(".json")
        assert "test_" in k1

    def test_cache_key_different_inputs(self):
        k1 = pt._cache_key("test", "a")
        k2 = pt._cache_key("test", "b")
        assert k1 != k2

    def test_cache_put_get(self, tmp_path):
        path = str(tmp_path / "test.json")
        data = {"key": "value", "num": 42}
        pt.cache_put(path, data)
        with patch.object(pt, "CACHE_TTL", 9999):
            result = pt.cache_get(path)
        assert result == data

    def test_cache_get_expired(self, tmp_path):
        path = str(tmp_path / "expired.json")
        pt.cache_put(path, {"old": True})
        # Set mtime to past
        old_time = time.time() - 999999
        os.utime(path, (old_time, old_time))
        assert pt.cache_get(path) is None

    def test_cache_get_missing(self):
        assert pt.cache_get("/nonexistent/path.json") is None

    def test_cache_get_corrupt(self, tmp_path):
        path = str(tmp_path / "bad.json")
        with open(path, "w") as f:
            f.write("not json{{{")
        assert pt.cache_get(path) is None


# ── extract_pricing ─────────────────────────────────────────────

class TestExtractPricing:
    def test_basic_fields(self):
        r = pt.extract_pricing(EC2_PRODUCT)
        assert r["instance_type"] == "c6g.xlarge"
        assert r["vcpu"] == "4"
        assert r["memory"] == "8 GiB"
        assert r["os"] == "Linux"
        assert r["region"] == "ap-northeast-1"

    def test_on_demand_price(self):
        r = pt.extract_pricing(EC2_PRODUCT)
        assert r["price_per_hour"] == pytest.approx(0.1360)
        assert r["price_unit"] == "Hrs"

    def test_all_six_ri_terms(self):
        r = pt.extract_pricing(EC2_PRODUCT)
        assert r["ri_1yr_no_upfront"] == pytest.approx(0.0860)
        assert r["ri_1yr_partial_upfront"] is not None
        assert r["ri_1yr_all_upfront"] is not None
        assert r["ri_3yr_no_upfront"] == pytest.approx(0.0550)
        assert r["ri_3yr_partial_upfront"] is not None
        assert r["ri_3yr_all_upfront"] is not None

    def test_ri_effective_rate_calculation(self):
        r = pt.extract_pricing(EC2_PRODUCT)
        # 1yr Partial: hourly + upfront/8760
        expected = 0.0410 + 355.0 / 8760
        assert r["ri_1yr_partial_upfront"] == pytest.approx(expected, rel=1e-3)
        # 1yr All: 0 + 700/8760
        assert r["ri_1yr_all_upfront"] == pytest.approx(700.0 / 8760, rel=1e-3)

    def test_all_upfront_total(self):
        r = pt.extract_pricing(EC2_PRODUCT)
        assert r["ri_1yr_all_upfront_total"] == 700.0
        assert r["ri_3yr_all_upfront_total"] == 1400.0

    def test_zero_price_product(self):
        r = pt.extract_pricing(EC2_PRODUCT_ZERO)
        assert "price_per_hour" not in r

    def test_rds_engine_field(self):
        r = pt.extract_pricing(RDS_PRODUCT)
        assert r["os"] == "Aurora MySQL"
        assert r["price_per_hour"] == pytest.approx(0.35)

    def test_elasticache_engine_field(self):
        r = pt.extract_pricing(ELASTICACHE_PRODUCT)
        assert r["os"] == "Redis"
        assert r["instance_type"] == "cache.r6g.large"
        assert r["price_per_hour"] == pytest.approx(0.261)
        assert r["ri_1yr_no_upfront"] == pytest.approx(0.178)

    def test_empty_product(self):
        r = pt.extract_pricing({})
        assert r["instance_type"] == ""
        assert "price_per_hour" not in r


# ── dedup_results ───────────────────────────────────────────────

class TestDedupResults:
    def test_removes_zero_price(self):
        results = [
            pt.extract_pricing(EC2_PRODUCT),
            pt.extract_pricing(EC2_PRODUCT_ZERO),
        ]
        unique = pt.dedup_results(results)
        assert len(unique) == 1
        assert unique[0]["instance_type"] == "c6g.xlarge"

    def test_removes_duplicates(self):
        r = pt.extract_pricing(EC2_PRODUCT)
        unique = pt.dedup_results([r, r.copy()])
        assert len(unique) == 1

    def test_sorts_by_price(self):
        r1 = pt.extract_pricing(EC2_PRODUCT)       # 0.136
        r2 = pt.extract_pricing(EC2_PRODUCT_2)      # 0.272
        unique = pt.dedup_results([r2, r1])
        assert unique[0]["price_per_hour"] < unique[1]["price_per_hour"]

    def test_empty_input(self):
        assert pt.dedup_results([]) == []

    def test_keeps_different_types(self):
        r1 = pt.extract_pricing(EC2_PRODUCT)
        r2 = pt.extract_pricing(EC2_PRODUCT_2)
        unique = pt.dedup_results([r1, r2])
        assert len(unique) == 2


# ── fmt ─────────────────────────────────────────────────────────

class TestFmt:
    def test_normal_price(self):
        s = pt.fmt(0.136)
        assert "$0.1360/hr" in s
        assert "$99.28/mo" in s

    def test_zero(self):
        assert pt.fmt(0) == "N/A"

    def test_none(self):
        assert pt.fmt(None) == "N/A"

    def test_small_price(self):
        s = pt.fmt(0.0001)
        assert "$0.0001/hr" in s


# ── build_filters ───────────────────────────────────────────────

class TestBuildFilters:
    def _args(self, **kw):
        defaults = {"region": "ap-northeast-1", "instance_type": "c6g.xlarge",
                     "engine": None, "deployment": None, "os": "Linux"}
        defaults.update(kw)
        return SimpleNamespace(**defaults)

    def test_ec2(self):
        f = pt.build_filters("ec2", self._args())
        assert f["operatingSystem"] == "Linux"
        assert f["tenancy"] == "Shared"
        assert f["preInstalledSw"] == "NA"
        assert f["capacitystatus"] == "Used"
        assert f["location"] == "Asia Pacific (Tokyo)"

    def test_ec2_windows(self):
        f = pt.build_filters("ec2", self._args(os="Windows"))
        assert f["operatingSystem"] == "Windows"

    def test_rds_with_engine(self):
        f = pt.build_filters("rds", self._args(engine="aurora-mysql"))
        assert f["databaseEngine"] == "Aurora MySQL"
        assert f["deploymentOption"] == "Single-AZ"

    def test_rds_multi_az(self):
        f = pt.build_filters("rds", self._args(engine="mysql", deployment="Multi-AZ"))
        assert f["deploymentOption"] == "Multi-AZ"

    def test_elasticache(self):
        f = pt.build_filters("elasticache", self._args(engine="redis"))
        assert f["cacheEngine"] == "Redis"

    def test_redshift(self):
        f = pt.build_filters("redshift", self._args())
        assert f["productFamily"] == "Compute Instance"

    def test_opensearch(self):
        f = pt.build_filters("opensearch", self._args())
        assert f["productFamily"] == "Compute Instance"

    def test_neptune(self):
        f = pt.build_filters("neptune", self._args())
        assert f["productFamily"] == "Database Instance"

    def test_docdb(self):
        f = pt.build_filters("docdb", self._args())
        assert f["productFamily"] == "Database Instance"

    def test_memorydb(self):
        f = pt.build_filters("memorydb", self._args())
        assert f["productFamily"] == "MemoryDB Node"

    def test_mq(self):
        f = pt.build_filters("mq", self._args())
        assert f["productFamily"] == "Broker Instances"

    def test_sagemaker(self):
        f = pt.build_filters("sagemaker", self._args())
        assert f["productFamily"] == "ML Instance"

    def test_all_services_have_location(self):
        """Every service should at least set location filter."""
        for svc in pt.SERVICE_CODES:
            f = pt.build_filters(svc, self._args())
            assert "location" in f, f"{svc} missing location filter"

    def test_ecs_filters(self):
        f = pt.build_filters("ecs", self._args())
        assert f["operatingSystem"] == "Linux"
        assert f["tenancy"] == "Shared"

    def test_eks_filters(self):
        f = pt.build_filters("eks", self._args())
        assert f["operatingSystem"] == "Linux"

    def test_evs_filters(self):
        f = pt.build_filters("evs", self._args())
        assert f["productFamily"] == "Compute Instance"

    def test_timestream_filters(self):
        f = pt.build_filters("timestream", self._args())
        assert f["productFamily"] == "Compute Instance"


# ── output helpers ──────────────────────────────────────────────

class TestOutputHelpers:
    def test_output_json(self, capsys):
        pt._output_json([{"a": 1}])
        out = capsys.readouterr().out
        assert json.loads(out) == [{"a": 1}]

    def test_output_csv(self, capsys):
        pt._output_csv([{"name": "x", "val": 1}], ["name", "val"])
        out = capsys.readouterr().out
        assert "name,val" in out
        assert "x,1" in out

    def test_output_csv_extra_fields_ignored(self, capsys):
        pt._output_csv([{"name": "x", "val": 1, "extra": "y"}], ["name", "val"])
        out = capsys.readouterr().out
        assert "extra" not in out


# ── print_results ───────────────────────────────────────────────

class TestPrintResults:
    def _results(self):
        return [pt.extract_pricing(EC2_PRODUCT)]

    def test_json_output(self, capsys):
        r = pt.print_results(self._results(), "ec2", output_json=True)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert len(data) == 1
        assert data[0]["instance_type"] == "c6g.xlarge"
        assert r is not None

    def test_json_includes_monthly(self, capsys):
        pt.print_results(self._results(), "ec2", output_json=True)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "monthly" in data[0]
        assert data[0]["monthly"] == pytest.approx(data[0]["price_per_hour"] * 730, rel=0.01)

    def test_csv_output(self, capsys):
        r = pt.print_results(self._results(), "ec2", output_csv=True)
        out = capsys.readouterr().out
        assert "instance_type" in out
        assert "c6g.xlarge" in out
        assert "monthly" in out

    def test_table_output(self, capsys):
        pt.print_results(self._results(), "ec2")
        out = capsys.readouterr().out
        assert "EC2" in out
        assert "c6g.xlarge" in out
        assert "On-Demand" in out

    def test_empty_results(self, capsys):
        pt.print_results([], "ec2")
        out = capsys.readouterr().out
        assert "No pricing results found" in out

    def test_returns_unique(self):
        r = pt.print_results(self._results(), "ec2", output_json=True)
        assert isinstance(r, list)


# ── color functions ─────────────────────────────────────────────

class TestColor:
    def test_color_disabled(self):
        with patch.object(pt, "_USE_COLOR", False):
            assert pt._green("hi") == "hi"
            assert pt._bold("hi") == "hi"

    def test_color_enabled(self):
        with patch.object(pt, "_USE_COLOR", True):
            assert "\033[32m" in pt._green("hi")
            assert "\033[1m" in pt._bold("hi")


# ── _check_output_flags ────────────────────────────────────────

class TestCheckOutputFlags:
    def test_json_only(self):
        args = SimpleNamespace(json=True, csv=False)
        assert pt._check_output_flags(args) == (True, False)

    def test_csv_only(self):
        args = SimpleNamespace(json=False, csv=True)
        assert pt._check_output_flags(args) == (False, True)

    def test_neither(self):
        args = SimpleNamespace(json=False, csv=False)
        assert pt._check_output_flags(args) == (False, False)

    def test_both_exits(self):
        args = SimpleNamespace(json=True, csv=True)
        with pytest.raises(SystemExit):
            pt._check_output_flags(args)


# ── cmd_regions ─────────────────────────────────────────────────

class TestCmdRegions:
    def test_regions_json(self, capsys):
        args = SimpleNamespace(json=True)
        data = pt.cmd_regions(args)
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert len(parsed) == 34
        assert all("code" in r and "name" in r for r in parsed)

    def test_regions_table(self, capsys):
        args = SimpleNamespace(json=False)
        pt.cmd_regions(args)
        out = capsys.readouterr().out
        assert "ap-northeast-1" in out
        assert "us-east-1" in out


# ── cmd_refresh / cmd_cache_info ────────────────────────────────

class TestCmdRefresh:
    def test_refresh_clears_cache(self, tmp_path):
        cache_dir = str(tmp_path / "cache")
        os.makedirs(cache_dir)
        for i in range(3):
            with open(os.path.join(cache_dir, f"test_{i}.json"), "w") as f:
                f.write("{}")
        with patch.object(pt, "CACHE_DIR", cache_dir):
            args = SimpleNamespace()
            pt.cmd_refresh(args)
        remaining = [f for f in os.listdir(cache_dir) if f.endswith(".json")]
        assert len(remaining) == 0

    def test_refresh_no_cache_dir(self, capsys):
        with patch.object(pt, "CACHE_DIR", "/nonexistent/path"):
            pt.cmd_refresh(SimpleNamespace())
        assert "No cache" in capsys.readouterr().out


class TestCmdCacheInfo:
    def test_cache_info_with_files(self, tmp_path, capsys):
        cache_dir = str(tmp_path / "cache")
        os.makedirs(cache_dir)
        with open(os.path.join(cache_dir, "test.json"), "w") as f:
            f.write('{"data": 1}')
        with patch.object(pt, "CACHE_DIR", cache_dir):
            pt.cmd_cache_info(SimpleNamespace())
        out = capsys.readouterr().out
        assert "Files: 1" in out
        assert "TTL:" in out

    def test_cache_info_no_dir(self, capsys):
        with patch.object(pt, "CACHE_DIR", "/nonexistent"):
            pt.cmd_cache_info(SimpleNamespace())
        assert "No cache" in capsys.readouterr().out


# ── query_products error handling ───────────────────────────────

class TestQueryProducts:
    def test_api_exception_returns_empty(self):
        mock_client = MagicMock()
        mock_client.get_paginator.return_value.paginate.side_effect = Exception("API error")
        result = pt.query_products(mock_client, "AmazonEC2", {"location": "test"}, use_cache=False, quiet=True)
        assert result == []

    def test_caches_results(self, tmp_path):
        mock_client = MagicMock()
        mock_client.get_paginator.return_value.paginate.return_value = [
            {"PriceList": [json.dumps(EC2_PRODUCT)]}
        ]
        cache_path = str(tmp_path / "test.json")
        with patch.object(pt, "_cache_key", return_value=cache_path):
            with patch.object(pt, "cache_get", return_value=None):
                result = pt.query_products(mock_client, "AmazonEC2", {}, use_cache=True, quiet=True)
        assert len(result) == 1
        # Verify cache was written
        assert os.path.exists(cache_path)

    def test_returns_cached_when_available(self):
        cached_data = [{"cached": True}]
        with patch.object(pt, "cache_get", return_value=cached_data):
            result = pt.query_products(MagicMock(), "AmazonEC2", {}, use_cache=True, quiet=True)
        assert result == cached_data

    def test_empty_results_not_cached(self, tmp_path):
        mock_client = MagicMock()
        mock_client.get_paginator.return_value.paginate.return_value = [{"PriceList": []}]
        cache_path = str(tmp_path / "empty.json")
        with patch.object(pt, "_cache_key", return_value=cache_path):
            with patch.object(pt, "cache_get", return_value=None):
                result = pt.query_products(mock_client, "AmazonEC2", {}, use_cache=True, quiet=True)
        assert result == []
        assert not os.path.exists(cache_path)


# ── list_instance_types ─────────────────────────────────────────

class TestListInstanceTypes:
    def test_api_exception_returns_empty(self):
        mock_client = MagicMock()
        mock_client.get_paginator.return_value.paginate.side_effect = Exception("fail")
        result = pt.list_instance_types(mock_client, "AmazonEC2", "test", use_cache=False)
        assert result == []

    def test_returns_sorted(self):
        mock_client = MagicMock()
        mock_client.get_paginator.return_value.paginate.return_value = [
            {"PriceList": [
                json.dumps({"product": {"attributes": {"instanceType": "m5.xlarge"}}}),
                json.dumps({"product": {"attributes": {"instanceType": "c5.large"}}}),
                json.dumps({"product": {"attributes": {"instanceType": "c5.large"}}}),  # dup
            ]}
        ]
        with patch.object(pt, "cache_get", return_value=None):
            with patch.object(pt, "cache_put"):
                result = pt.list_instance_types(mock_client, "AmazonEC2", "test", use_cache=True)
        assert result == ["c5.large", "m5.xlarge"]  # sorted, deduped


# ── extract_pricing edge cases ──────────────────────────────────

class TestExtractPricingEdgeCases:
    def test_invalid_price_value(self):
        """Non-numeric price should be skipped."""
        product = {
            "product": {"attributes": {"instanceType": "test"}},
            "terms": {"OnDemand": {"OD1": {"priceDimensions": {
                "D1": {"unit": "Hrs", "pricePerUnit": {"USD": "invalid"}}
            }}}, "Reserved": {}},
        }
        r = pt.extract_pricing(product)
        assert "price_per_hour" not in r

    def test_missing_usd_field(self):
        product = {
            "product": {"attributes": {"instanceType": "test"}},
            "terms": {"OnDemand": {"OD1": {"priceDimensions": {
                "D1": {"unit": "Hrs", "pricePerUnit": {}}
            }}}, "Reserved": {}},
        }
        r = pt.extract_pricing(product)
        assert "price_per_hour" not in r
