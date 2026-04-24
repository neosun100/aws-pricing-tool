"""Fixtures: realistic AWS Pricing API response structures."""

# A full EC2 product with OnDemand + 6 RI terms
EC2_PRODUCT = {
    "product": {
        "productFamily": "Compute Instance",
        "attributes": {
            "instanceType": "c6g.xlarge",
            "vcpu": "4",
            "memory": "8 GiB",
            "storage": "EBS only",
            "networkPerformance": "Up to 10 Gigabit",
            "operatingSystem": "Linux",
            "regionCode": "ap-northeast-1",
            "location": "Asia Pacific (Tokyo)",
            "tenancy": "Shared",
            "preInstalledSw": "NA",
            "capacitystatus": "Used",
        },
    },
    "terms": {
        "OnDemand": {
            "OD1": {
                "priceDimensions": {
                    "OD1.1": {
                        "unit": "Hrs",
                        "pricePerUnit": {"USD": "0.1360"},
                        "description": "Linux/UNIX c6g.xlarge",
                    }
                }
            }
        },
        "Reserved": {
            "RI_1yr_NoUp": {
                "termAttributes": {"LeaseContractLength": "1yr", "PurchaseOption": "No Upfront"},
                "priceDimensions": {
                    "D1": {"unit": "Hrs", "pricePerUnit": {"USD": "0.0860"}, "description": ""},
                },
            },
            "RI_1yr_PartUp": {
                "termAttributes": {"LeaseContractLength": "1yr", "PurchaseOption": "Partial Upfront"},
                "priceDimensions": {
                    "D1": {"unit": "Hrs", "pricePerUnit": {"USD": "0.0410"}, "description": ""},
                    "D2": {"unit": "Quantity", "pricePerUnit": {"USD": "355.0"}, "description": ""},
                },
            },
            "RI_1yr_AllUp": {
                "termAttributes": {"LeaseContractLength": "1yr", "PurchaseOption": "All Upfront"},
                "priceDimensions": {
                    "D1": {"unit": "Hrs", "pricePerUnit": {"USD": "0"}, "description": ""},
                    "D2": {"unit": "Quantity", "pricePerUnit": {"USD": "700.0"}, "description": ""},
                },
            },
            "RI_3yr_NoUp": {
                "termAttributes": {"LeaseContractLength": "3yr", "PurchaseOption": "No Upfront"},
                "priceDimensions": {
                    "D1": {"unit": "Hrs", "pricePerUnit": {"USD": "0.0550"}, "description": ""},
                },
            },
            "RI_3yr_PartUp": {
                "termAttributes": {"LeaseContractLength": "3yr", "PurchaseOption": "Partial Upfront"},
                "priceDimensions": {
                    "D1": {"unit": "Hrs", "pricePerUnit": {"USD": "0.0250"}, "description": ""},
                    "D2": {"unit": "Quantity", "pricePerUnit": {"USD": "600.0"}, "description": ""},
                },
            },
            "RI_3yr_AllUp": {
                "termAttributes": {"LeaseContractLength": "3yr", "PurchaseOption": "All Upfront"},
                "priceDimensions": {
                    "D1": {"unit": "Hrs", "pricePerUnit": {"USD": "0"}, "description": ""},
                    "D2": {"unit": "Quantity", "pricePerUnit": {"USD": "1400.0"}, "description": ""},
                },
            },
        },
    },
}

# A second EC2 product (different type, same region) for batch/dedup tests
EC2_PRODUCT_2 = {
    "product": {
        "productFamily": "Compute Instance",
        "attributes": {
            "instanceType": "c6g.2xlarge",
            "vcpu": "8",
            "memory": "16 GiB",
            "storage": "EBS only",
            "networkPerformance": "Up to 10 Gigabit",
            "operatingSystem": "Linux",
            "regionCode": "ap-northeast-1",
            "location": "Asia Pacific (Tokyo)",
        },
    },
    "terms": {
        "OnDemand": {
            "OD1": {
                "priceDimensions": {
                    "OD1.1": {"unit": "Hrs", "pricePerUnit": {"USD": "0.2720"}, "description": ""}
                }
            }
        },
        "Reserved": {},
    },
}

# Product with zero price (should be filtered by dedup)
EC2_PRODUCT_ZERO = {
    "product": {"attributes": {"instanceType": "t3.nano", "operatingSystem": "Linux"}},
    "terms": {
        "OnDemand": {
            "OD1": {"priceDimensions": {"D1": {"unit": "Hrs", "pricePerUnit": {"USD": "0"}}}}
        },
        "Reserved": {},
    },
}

# RDS product for engine filter tests
RDS_PRODUCT = {
    "product": {
        "productFamily": "Database Instance",
        "attributes": {
            "instanceType": "db.r6g.xlarge",
            "vcpu": "4",
            "memory": "32 GiB",
            "databaseEngine": "Aurora MySQL",
            "regionCode": "ap-northeast-1",
            "location": "Asia Pacific (Tokyo)",
            "deploymentOption": "Single-AZ",
            "storage": "EBS only",
            "networkPerformance": "Up to 10 Gigabit",
        },
    },
    "terms": {
        "OnDemand": {
            "OD1": {
                "priceDimensions": {
                    "D1": {"unit": "Hrs", "pricePerUnit": {"USD": "0.3500"}, "description": ""}
                }
            }
        },
        "Reserved": {
            "RI1": {
                "termAttributes": {"LeaseContractLength": "1yr", "PurchaseOption": "No Upfront"},
                "priceDimensions": {
                    "D1": {"unit": "Hrs", "pricePerUnit": {"USD": "0.2200"}, "description": ""},
                },
            },
        },
    },
}

# EC2 product in a different region (for compare tests)
EC2_PRODUCT_VIRGINIA = {
    "product": {
        "productFamily": "Compute Instance",
        "attributes": {
            "instanceType": "c6g.xlarge",
            "vcpu": "4",
            "memory": "8 GiB",
            "operatingSystem": "Linux",
            "regionCode": "us-east-1",
            "location": "US East (N. Virginia)",
            "storage": "EBS only",
            "networkPerformance": "Up to 10 Gigabit",
        },
    },
    "terms": {
        "OnDemand": {
            "OD1": {
                "priceDimensions": {
                    "D1": {"unit": "Hrs", "pricePerUnit": {"USD": "0.1020"}, "description": ""}
                }
            }
        },
        "Reserved": {
            "RI1": {
                "termAttributes": {"LeaseContractLength": "1yr", "PurchaseOption": "No Upfront"},
                "priceDimensions": {
                    "D1": {"unit": "Hrs", "pricePerUnit": {"USD": "0.0640"}, "description": ""},
                },
            },
        },
    },
}


# ElastiCache product for engine filter tests
ELASTICACHE_PRODUCT = {
    "product": {
        "productFamily": "Cache Instance",
        "attributes": {
            "instanceType": "cache.r6g.large",
            "vcpu": "2",
            "memory": "13.07 GiB",
            "cacheEngine": "Redis",
            "regionCode": "ap-northeast-1",
            "location": "Asia Pacific (Tokyo)",
            "networkPerformance": "Up to 10 Gigabit",
        },
    },
    "terms": {
        "OnDemand": {
            "OD1": {
                "priceDimensions": {
                    "D1": {"unit": "Hrs", "pricePerUnit": {"USD": "0.2610"}, "description": ""}
                }
            }
        },
        "Reserved": {
            "RI1": {
                "termAttributes": {"LeaseContractLength": "1yr", "PurchaseOption": "No Upfront"},
                "priceDimensions": {
                    "D1": {"unit": "Hrs", "pricePerUnit": {"USD": "0.1780"}, "description": ""},
                },
            },
        },
    },
}
