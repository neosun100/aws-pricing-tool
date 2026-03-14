"""Tests for MCP Server — verifies tool registration, schemas, and mock invocations."""

import pytest
from unittest.mock import patch, MagicMock

from mcp_server import (
    mcp, _query_pricing, _compare_regions, _batch_compare,
    _list_types, _get_regions, _get_services,
    _graviton_recommend, _ri_analysis, _calculate_s3, _calculate_lambda,
    _calculate_bedrock, _list_bedrock_models,
    _suggest_graviton, GRAVITON_MAP, S3_PRICING, BEDROCK_PRICING,
)
import pricing_tool as pt
from conftest import EC2_PRODUCT


class TestToolRegistration:
    def test_tool_count(self):
        assert len(mcp._tool_manager._tools) == 12

    def test_tool_names(self):
        names = set(mcp._tool_manager._tools.keys())
        assert names == {
            "query_pricing", "compare_regions", "batch_compare",
            "list_types", "get_regions", "get_services",
            "graviton_recommend", "ri_analysis", "calculate_s3", "calculate_lambda",
            "calculate_bedrock", "list_bedrock_models",
        }


class TestGetRegions:
    def test_returns_all(self):
        result = _get_regions()
        assert len(result) == len(pt.REGION_MAP)
        assert any(r["code"] == "ap-northeast-1" for r in result)

    def test_structure(self):
        for r in _get_regions():
            assert "code" in r and "name" in r


class TestGetServices:
    def test_returns_all(self):
        result = _get_services()
        assert len(result) == len(pt.SERVICE_CODES)
        assert any(s["service"] == "ec2" for s in result)

    def test_structure(self):
        for s in _get_services():
            assert "service" in s and "service_code" in s


class TestQueryPricing:
    @patch("mcp_server._get_client")
    def test_valid_query(self, mock_client):
        mock_client.return_value = MagicMock()
        with patch("pricing_tool.query_products", return_value=[EC2_PRODUCT]):
            result = _query_pricing("ec2", "c6g.xlarge", "tokyo")
            assert len(result) > 0
            assert result[0]["instance_type"] == "c6g.xlarge"
            assert "price_per_hour" in result[0]
            assert "price_per_month" in result[0]

    def test_invalid_service(self):
        result = _query_pricing("bad_svc", "c6g.xlarge", "tokyo")
        assert "error" in result[0]

    @patch("mcp_server._get_client")
    def test_no_results(self, mock_client):
        mock_client.return_value = MagicMock()
        with patch("pricing_tool.query_products", return_value=[]):
            result = _query_pricing("ec2", "nonexistent", "tokyo")
            assert "error" in result[0]

    @patch("mcp_server._get_client")
    def test_chinese_region(self, mock_client):
        mock_client.return_value = MagicMock()
        with patch("pricing_tool.query_products", return_value=[EC2_PRODUCT]):
            result = _query_pricing("ec2", "c6g.xlarge", "东京")
            assert len(result) > 0

    @patch("mcp_server._get_client")
    def test_monthly_price(self, mock_client):
        mock_client.return_value = MagicMock()
        with patch("pricing_tool.query_products", return_value=[EC2_PRODUCT]):
            result = _query_pricing("ec2", "c6g.xlarge", "tokyo")
            r = result[0]
            assert r["price_per_month"] == round(r["price_per_hour"] * 730, 2)

    @patch("mcp_server._get_client")
    def test_ri_fields(self, mock_client):
        mock_client.return_value = MagicMock()
        with patch("pricing_tool.query_products", return_value=[EC2_PRODUCT]):
            result = _query_pricing("ec2", "c6g.xlarge", "tokyo")
            r = result[0]
            assert "ri_1yr_no_upfront" in r
            assert "ri_3yr_all_upfront" in r


class TestCompareRegions:
    @patch("mcp_server._get_client")
    def test_multi_region(self, mock_client):
        mock_client.return_value = MagicMock()
        with patch("pricing_tool.query_products", return_value=[EC2_PRODUCT]):
            result = _compare_regions("ec2", "c6g.xlarge", ["tokyo", "virginia"])
            assert len(result) == 2
            assert result[0].get("cheapest") is True

    def test_invalid_service(self):
        result = _compare_regions("bad", "c6g.xlarge", ["tokyo"])
        assert "error" in result[0]

    @patch("mcp_server._get_client")
    def test_sorted_by_price(self, mock_client):
        mock_client.return_value = MagicMock()
        with patch("pricing_tool.query_products", return_value=[EC2_PRODUCT]):
            result = _compare_regions("ec2", "c6g.xlarge", ["tokyo", "virginia", "singapore"])
            prices = [r["price_per_hour"] for r in result]
            assert prices == sorted(prices)


class TestBatchCompare:
    @patch("mcp_server._get_client")
    def test_multi_type(self, mock_client):
        mock_client.return_value = MagicMock()
        with patch("pricing_tool.query_products", return_value=[EC2_PRODUCT]):
            result = _batch_compare("ec2", ["c6g.xlarge", "c6g.2xlarge"], "tokyo")
            assert isinstance(result, list)

    def test_invalid_service(self):
        result = _batch_compare("bad", ["c6g.xlarge"], "tokyo")
        assert "error" in result[0]


class TestListTypes:
    @patch("mcp_server._get_client")
    def test_list(self, mock_client):
        mock_client.return_value = MagicMock()
        with patch("pricing_tool.list_instance_types", return_value=["c6g.xlarge", "c6g.2xlarge", "m6g.large"]):
            result = _list_types("ec2", "tokyo")
            assert "c6g.xlarge" in result

    @patch("mcp_server._get_client")
    def test_filter(self, mock_client):
        mock_client.return_value = MagicMock()
        with patch("pricing_tool.list_instance_types", return_value=["c6g.xlarge", "c6g.2xlarge", "m6g.large"]):
            result = _list_types("ec2", "tokyo", filter_keyword="c6g")
            assert all("c6g" in t for t in result)
            assert "m6g.large" not in result

    def test_invalid_service(self):
        result = _list_types("bad", "tokyo")
        assert any("Unknown" in str(r) for r in result)


# ── v2.0 new tools ─────────────────────────────────────────────

class TestSuggestGraviton:
    def test_x86_to_arm(self):
        assert _suggest_graviton("c6i.xlarge") == "c7g.xlarge"
        assert _suggest_graviton("m5.2xlarge") == "m6g.2xlarge"
        assert _suggest_graviton("t3.medium") == "t4g.medium"

    def test_db_prefix(self):
        assert _suggest_graviton("db.r5.large") == "db.r6g.large"
        assert _suggest_graviton("db.m6i.xlarge") == "db.m6g.xlarge"

    def test_cache_prefix(self):
        assert _suggest_graviton("cache.r5.large") == "cache.r6g.large"

    def test_already_graviton(self):
        assert _suggest_graviton("c6g.xlarge") is None
        assert _suggest_graviton("m7g.large") is None

    def test_unknown_type(self):
        assert _suggest_graviton("p4d.24xlarge") is None

    def test_amd_variants(self):
        assert _suggest_graviton("c5a.xlarge") == "c6g.xlarge"
        assert _suggest_graviton("m5a.large") == "m6g.large"
        assert _suggest_graviton("r5a.2xlarge") == "r6g.2xlarge"
        assert _suggest_graviton("c7a.xlarge") == "c7g.xlarge"

    def test_newer_generations(self):
        assert _suggest_graviton("m7a.large") == "m7g.large"
        assert _suggest_graviton("r7a.xlarge") == "r7g.xlarge"

    def test_db_t3(self):
        assert _suggest_graviton("db.t3.medium") == "db.t4g.medium"

    def test_cache_t3(self):
        assert _suggest_graviton("cache.t3.medium") == "cache.t4g.medium"

    def test_storage_optimized(self):
        assert _suggest_graviton("i3.xlarge") == "i4g.xlarge"


class TestGravitonRecommend:
    @patch("mcp_server._get_client")
    def test_with_x86(self, mock_client):
        mock_client.return_value = MagicMock()
        with patch("pricing_tool.query_products", return_value=[EC2_PRODUCT]):
            result = _graviton_recommend("ec2", "c6i.xlarge", "tokyo")
            assert "x86_type" in result
            assert "graviton_type" in result
            assert "saving_percent" in result

    def test_already_graviton(self):
        result = _graviton_recommend("ec2", "c6g.xlarge", "tokyo")
        assert result.get("is_graviton") is True


class TestRiAnalysis:
    @patch("mcp_server._get_client")
    def test_basic(self, mock_client):
        mock_client.return_value = MagicMock()
        with patch("pricing_tool.query_products", return_value=[EC2_PRODUCT]):
            result = _ri_analysis("ec2", "c6g.xlarge", "tokyo")
            assert "on_demand_hourly" in result
            assert "on_demand_monthly" in result
            assert "on_demand_yearly" in result
            assert "options" in result
            assert isinstance(result["options"], list)

    @patch("mcp_server._get_client")
    def test_options_have_breakeven(self, mock_client):
        mock_client.return_value = MagicMock()
        with patch("pricing_tool.query_products", return_value=[EC2_PRODUCT]):
            result = _ri_analysis("ec2", "c6g.xlarge", "tokyo")
            for opt in result["options"]:
                assert "plan" in opt
                assert "saving_vs_od_percent" in opt
                assert "breakeven_months" in opt
                assert "saving_per_year" in opt
                assert "effective_monthly" in opt

    @patch("mcp_server._get_client")
    def test_savings_positive(self, mock_client):
        mock_client.return_value = MagicMock()
        with patch("pricing_tool.query_products", return_value=[EC2_PRODUCT]):
            result = _ri_analysis("ec2", "c6g.xlarge", "tokyo")
            for opt in result["options"]:
                assert opt["saving_vs_od_percent"] > 0
                assert opt["saving_per_month"] > 0

    def test_invalid_service(self):
        result = _ri_analysis("bad", "c6g.xlarge", "tokyo")
        assert isinstance(result, list)
        assert "error" in result[0]


class TestCalculateS3:
    def test_standard(self):
        result = _calculate_s3(1000, "Standard", 100000, 1000000, 50)
        assert result["storage_cost"] == 23.0
        assert result["total_monthly"] > 0
        assert "total_yearly" in result

    def test_glacier(self):
        result = _calculate_s3(10000, "Glacier Deep Archive")
        assert result["storage_cost"] == 9.9
        assert result["total_monthly"] == 9.9

    def test_egress_free_tier(self):
        result = _calculate_s3(100, "Standard", egress_gb=50)
        assert result["egress_cost"] == 0  # under 100GB free

    def test_egress_paid(self):
        result = _calculate_s3(100, "Standard", egress_gb=200)
        assert result["egress_cost"] == 9.0  # (200-100)*0.09

    def test_invalid_class(self):
        result = _calculate_s3(100, "BadClass")
        assert "error" in result

    def test_zero_storage(self):
        result = _calculate_s3(0, "Standard")
        assert result["total_monthly"] == 0


class TestCalculateLambda:
    def test_basic(self):
        result = _calculate_lambda(10_000_000, 200, 256, "x86")
        assert result["total_monthly"] > 0
        assert result["gb_seconds"] > 0

    def test_free_tier(self):
        result = _calculate_lambda(500_000, 100, 128, "x86")
        assert result["total_monthly"] == 0  # under free tier

    def test_arm_cheaper(self):
        x86 = _calculate_lambda(50_000_000, 500, 512, "x86")
        arm = _calculate_lambda(50_000_000, 500, 512, "arm")
        assert arm["total_monthly"] < x86["total_monthly"]

    def test_structure(self):
        result = _calculate_lambda(1_000_000, 100, 128)
        assert "invocations" in result
        assert "gb_seconds" in result
        assert "request_cost" in result
        assert "compute_cost" in result


class TestCalculateBedrock:
    def test_exact_model(self):
        result = _calculate_bedrock("nova-pro", 1_000_000, 500_000)
        assert result["model"] == "nova-pro"
        assert result["provider"] == "Amazon"
        assert result["input_cost"] == 0.8
        assert result["output_cost"] == 1.6
        assert result["total_cost"] == 2.4

    def test_fuzzy_match(self):
        result = _calculate_bedrock("claude-3.5-sonnet", 1_000_000, 100_000)
        assert result["provider"] == "Anthropic"
        assert result["total_cost"] > 0

    def test_partial_match(self):
        result = _calculate_bedrock("deepseek", 1_000_000, 1_000_000)
        assert result["provider"] == "DeepSeek"

    def test_unknown_model(self):
        result = _calculate_bedrock("nonexistent-model-xyz", 1000, 1000)
        assert "error" in result

    def test_tier_standard(self):
        std = _calculate_bedrock("nova-pro", 1_000_000, 0, "standard")
        assert std["input_price_per_1m"] == 0.8

    def test_tier_priority(self):
        pri = _calculate_bedrock("nova-pro", 1_000_000, 0, "priority")
        assert pri["input_price_per_1m"] == 1.4  # 0.8 * 1.75

    def test_tier_flex(self):
        flex = _calculate_bedrock("nova-pro", 1_000_000, 0, "flex")
        assert flex["input_price_per_1m"] == 0.4  # 0.8 * 0.5

    def test_tier_batch(self):
        batch = _calculate_bedrock("nova-pro", 1_000_000, 0, "batch")
        assert batch["input_price_per_1m"] == 0.4  # 0.8 * 0.5

    def test_has_metadata(self):
        result = _calculate_bedrock("nova-lite", 1000, 1000)
        assert "pricing_date" in result
        assert "region" in result
        assert "note" in result

    def test_zero_tokens(self):
        result = _calculate_bedrock("nova-micro", 0, 0)
        assert result["total_cost"] == 0

    def test_all_providers_covered(self):
        providers = {v["provider"] for v in BEDROCK_PRICING.values()}
        assert len(providers) >= 10  # At least 10 providers


class TestListBedrockModels:
    def test_returns_all(self):
        result = _list_bedrock_models()
        assert result["count"] == len(BEDROCK_PRICING)
        assert result["count"] >= 20

    def test_structure(self):
        result = _list_bedrock_models()
        for m in result["models"]:
            assert "model" in m
            assert "provider" in m
            assert "input_per_1m_tokens" in m
            assert "output_per_1m_tokens" in m

    def test_has_source(self):
        result = _list_bedrock_models()
        assert "source" in result
        assert "pricing_date" in result
