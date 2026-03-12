"""Tests for MCP Server — verifies tool registration, schemas, and mock invocations."""

import pytest
from unittest.mock import patch, MagicMock

from mcp_server import (
    mcp, _query_pricing, _compare_regions, _batch_compare,
    _list_types, _get_regions, _get_services,
)
import pricing_tool as pt
from conftest import EC2_PRODUCT


class TestToolRegistration:
    def test_tool_count(self):
        assert len(mcp._tool_manager._tools) == 6

    def test_tool_names(self):
        names = set(mcp._tool_manager._tools.keys())
        assert names == {
            "query_pricing", "compare_regions", "batch_compare",
            "list_types", "get_regions", "get_services",
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
