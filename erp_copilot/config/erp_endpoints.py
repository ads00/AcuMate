"""
ERP API Endpoints Configuration
Add your specific endpoint configurations here.
The LLM will use these exact configurations to suggest actions.
"""

# Endpoint configurations for different ERP actions
# Add your actual endpoint details here
ERP_ENDPOINTS = {
    
    # Example structure - replace with your actual endpoints:
    # "action_name": {
    #     "description": "Description of what this endpoint does",
    #     "method": "PUT|POST|GET",
    #     "path": "/entity/Default/20.200.001/EntityName",
    #     "query_params": "optional query parameters",
    #     "body": {
    #         "YourField": {"value": "YourValue"},
    #         "Details": [
    #             {
    #                 "DetailField": {"value": "DetailValue"}
    #             }
    #         ]
    #     },
    #     "triggers": ["open_screen_SalesOrder", "add_item_to_order"] # When to suggest this action
    # }
    
    # Placeholder - you can replace this with your actual endpoints
    "create_sales_order": {
        "description": "Create a new Sales Order",
        "method": "PUT",
        "path": "/entity/Default/20.200.001/SalesOrder",
        "query_params": "$expand=Details/Allocations",
        "body": {
            "OrderNbr": {
                "value": "000471",
                "error": "<string>"
            },
            "DestinationWarehouseID": {
                "value": "RETAIL",
                "error": "<string>"
            },
            "OrderType": {
                "value": "SO",
                "error": "<string>"
            },
            "Details": [
                {
                "Branch": {
                    "value": "PRODWHOLE",
                    "error": "<string>"
                },
                "InventoryID": {
                    "value": "ADMCHARGE",
                    "error": "<string>"
                },
                "WarehouseID": {
                    "value": "WHOLESALE",
                    "error": "<string>"
                },
                "LineDescription": {
                    "value": "Administrative Charges",
                    "error": "<string>"
                },
                "OrderQty": {
                    "value": "30.00",
                    "error": "<string>"
                },
                "LineNbr": {
                        "value": "2",
                        "error": "<string>"
                    },
                "UnitPrice": {
                    "value": "10.00",
                    "error": "<string>"
                }
                }
            ]
        },
        "triggers": ["open_screen_SalesOrder", "customer_selected"]
    },
    
    "create_purchase_order": {
        "description": "Create a new Purchase Order", 
        "method": "PUT",
        "path": "/entity/Default/20.200.001/PurchaseOrder",
        "query_params": "=null",
        "body": {
                       "Branch": {
                "value": "PRODWHOLE"
            },
            "CurrencyID": {
                "value": "USD"
            },
            "CurrencyRate": {
                "value": 1.00000000
            },
            "CurrencyRateTypeID": {},
            "CurrencyReciprocalRate": {
                "value": 1.00000000
            },
            "Description": {
                "value": "Blanket order for Diet Coke"
            },
            "Hold": {
                "value": False
            },
            "Location": {
                "value": "MAIN"
            },
            "Owner": {
                "value": "3205"
            },
            "Project": {
                "value": "X"
            },
            "PromisedOn": {
                "value": "2015-03-02T00:00:00+05:30"
            },
            "Status": {
                "value": "Open"
            },
            "TaxTotal": {
                "value": 0.0000
            },
            "Terms": {
                "value": "30D"
            },
            "Type": {
                "value": "Blanket"
            },
            "VendorID": {
                "value": "AAVENDOR"
            },
            "Details": [
            {
                "Branch": {
                    "value": "PRODWHOLE",
                    "error": "<string>"
                },
                "InventoryID": {
                    "value": "ADMCHARGE",
                    "error": "<string>"
                },
                "WarehouseID": {
                    "value": "WHOLESALE",
                    "error": "<string>"
                },
                "LineDescription": {
                    "value": "Administrative Charges",
                    "error": "<string>"
                },
                "OrderQty": {
                    "value": "30.00",
                    "error": "<string>"
                },
                "LineNbr": {
                        "value": "2",
                        "error": "<string>"
                    },
                "UnitPrice": {
                    "value": "10.00",
                    "error": "<string>"
                }
            }
            ],
        },
        "triggers": ["open_screen_PurchaseOrder", "vendor_selected"]
    }
    
    # Add more endpoints as needed...
}

# Action mapping - maps user actions to potential endpoint suggestions
ACTION_MAPPINGS = {
    "open_screen": {
        "SalesOrder": ["create_sales_order"],
        "PurchaseOrder": ["create_purchase_order"],
        "TransferOrder": ["create_transfer_order"], 
        "StockItem": ["create_stock_item"]
    },
    "add_item": {
        "any": ["create_sales_order", "create_purchase_order"]
    },
    "select_customer": {
        "any": ["create_sales_order"]
    },
    "select_vendor": {
        "any": ["create_purchase_order"]
    }
}
