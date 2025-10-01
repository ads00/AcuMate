# ====== LLM Configuration ======
import pathlib
import textwrap

class LLMConfig:
    """Configuration for the LLM copilot functionality."""
    
    MODEL = "gpt-4"  # or "gpt-4.1" if you prefer
    
    # === CONFIG ===
    SOURCE_URL = "https://help.acumatica.com/"
    ALLOWED_DOMAINS = {"help.acumatica.com"}
    
    INSTRUCTIONS = f"""
You are an ERP copilot.
- You may ONLY use information from: {SOURCE_URL}
"""
    
    # Data directory for knowledge base
    DATA_DIR = pathlib.Path("./databed")
    
    @classmethod
    def ensure_data_dir(cls):
        """Ensure the data directory exists."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        return cls.DATA_DIR
    
    @classmethod
    def get_rules_content(cls):
        """Get the rules content for the knowledge base."""
        return """
# ERP Copilot Rules
- Prefer minimal, safe suggestions.
- Never fabricate endpoints or parameters.
- Dont use the values on the endpoints based on user input and suggestion change the values
"""
    
    @classmethod
    def get_api_shapes_content(cls):
        """Get the API shapes content for the knowledge base."""
        return """
# Acumatica API shapes (examples)
## Create Stock item API
curl --location --request PUT 'http://localhost/Test1/entity/Default/20.200.001/SalesOrder?%24expand=Details%2FAllocations' \\
--header 'Content-Type: application/json' \\
--header 'Accept: application/json' \\
--header 'Cookie: .ASPXAUTH=; ASP.NET_SessionId=lyh5xgen4j54mxcrhssnggwe; Locale=TimeZone=GMTM0800A&Culture=en-US; UserBranch=16; requestid=0DA9FC4229A051A411F09DF1877BA794; requeststat=+st:856+sc:~/entity/default/20.200.001/salesorder?%24expand=details%2fallocations+start:638948289199792133+tg:' \\
--data '{
    "OrderType": {
        "value": "SO"
    },
  "OrderNbr": {
    "value": "000470"
  },
  "CustomerID": {
    "value": "ABCHOLDING"
  },
  "Details": [
    {
      "InventoryID": {
        "value": "ADVERT"
      },
      "WarehouseID": {
        "value": "WHOLESALE"
      },
      "OrderQty": {
        "value": "1.00"
      },
      "UnitPrice": {
        "value": "10.00"
      }
    }
  ]
}'

## Read AR Invoices (filtered)
GET /entity/Default/22.200.001/ARInvoice
Query: $filter=CustomerID eq '{CustomerID}' and InvoiceDate ge {ISO_DATE}

## Create Transfer Order API
curl --location --request PUT 'http://localhost/Test1/entity/Default/20.200.001/SalesOrder?%24expand=Details%2FAllocations' \\
--header 'Content-Type: application/json' \\
--header 'Cookie: .ASPXAUTH=39CE484D69B5AC9DAD15146B9C1A896D5E57982130905E37E334C32C33A5B61B8AD27114705046A5F73A8EEA685929F72F2D6DB6F927ED7510CD3C7D6CBB3E986982D2CFD3E69D2FB2F296D8CC5AFFF1460A93B4CE48DAEAC3ECC0B262DA40686091F729DBC30F18E62872CC4BFA0CCEA28303DD; ASP.NET_SessionId=lyh5xgen4j54mxcrhssnggwe; Locale=TimeZone=GMTM0800A&Culture=en-US; UserBranch=16; requestid=0DA9FC4229A051A411F09DFD35DC243E; requeststat=+st:649+sc:~/entity/default/20.200.001/salesorder?%24expand=details%2fallocations+start:638948339346755042+tg:' \\
--data '{
  "OrderNbr": {
    "value": "000471",
    "error": "<string>"
  },
  "DestinationWarehouseID": {
    "value": "RETAIL",
    "error": "<string>"
  },
  "OrderType": {
            "value": "TR",
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
}'

# Create Purchase Order API
curl --location --request PUT 'http://localhost/Test1/entity/Default/20.200.001/PurchaseOrder?=null' \\
--header 'Content-Type: application/json' \\
--header 'Cookie: .ASPXAUTH=01093E84A8ADC70A0255828BBF3B75E717A301A4BE72B9C75252DCE469297C0E11D6D5DE45823137CECB2FD2ED11F61E9AF86A4627F452A5CD27777DAD808D9FCB6DDB52CF770A61599596416875873A08C52BAFCD7785E36211273BA60EB9F43A4220EBAFD0891456E20C00A48AFA7F3C6C98C1; ASP.NET_SessionId=lyh5xgen4j54mxcrhssnggwe; Locale=TimeZone=GMTM0800A&Culture=en-US; UserBranch=16; requestid=0DA9FC4229A051A411F09E0FCB9F10D9; requeststat=+st:402+sc:~/entity/default/20.200.001/purchaseorder+start:638948419173899860+tg:' \\
--data '{
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
            "value": false
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
  ]
}'
"""
    
    @classmethod
    def get_examples_content(cls):
        """Get the examples content for the knowledge base."""
        return """
# Few-shot examples (how to talk)
Q: User opened Sales Order; selected ABC; added Item A. What next?
A: "Customers like ABC often add Item B & C. Add them?"
Suggested request:
- Method: PUT
- URL: /entity/Default/22.200.001/SalesOrder/{OrderRef}
- Body: '{
  "OrderNbr": {
    "value": "000471",
    "error": "<string>"
  },
  "DestinationWarehouseID": {
    "value": "RETAIL",
    "error": "<string>"
  },
  "OrderType": {
            "value": "TR",
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
}'
Sources: api_shapes.md, rules.md
"""
    
    @classmethod
    def get_prompt_template(cls):
        """Get the prompt template for LLM requests."""
        return textwrap.dedent("""
User Actions:
{user_actions}

Task:
Scope & Sources
- Use ONLY the attached knowledge base ("databed") via File Search. If the databed does not contain enough information to answer, reply exactly: Not in databed.
- Do NOT invent vendors, endpoints, parameters, or numbers.

Goal
- Propose ONE short, business-focused suggestion that improves the user's outcome (e.g., better vendor choice, lower cost, faster lead time, higher margin, better fill rate) based on the databed's rules, metrics, and examples.
- Do NOT repeat or recheck validations; assume the transactional/validation logic is handled by software.

Decision Style
- Be decisive and concise (1–2 sentences). Prefer practical business value over restating data.
- If the databed provides vendor selection guidance (price, lead-time, reliability/service level, preferred/blocked lists, escalation rules), use it to choose the best vendor now. If the databed defines tie-breakers or weights, apply them. If scores are equal, pick the lowest total landed cost; if still tied, pick the shortest lead time; if still tied, pick the preferred vendor list order from the databed.

Action Output
- If the databed includes an EXACT endpoint for the suggested change, include a single proposed action with {{method, url, body}} that matches the databed's shapes (no extra fields). Use placeholders (e.g., {{OrderRef}}, {{VendorID}}) only if the databed examples use them or if the user context did not supply values.
- If there is no suitable endpoint in the databed, set action to null.

Safety & Formatting
- Dont give any technical terms in the suggestion this is meant for ERP users
- Never expose secrets or tokens. Never fabricate endpoints or parameters not present in the databed.
- Return the result using the response schema you've been given.
- Include a brief 'Sources' list of the filenames/section names retrieved from the databed.
""").strip()
