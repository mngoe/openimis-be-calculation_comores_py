CLASS_RULE_PARAM_VALIDATION = [
    {
        "class": "ContributionPlan",
        "parameters": [
            {
                "type": "number",
                "name": "lumpsum",
                "label": {
                    "en": "Lump sum",
                    "fr": "Montant forfaitaire"
                },
                "rights": {
                    "read": "150201",
                    "write": "150202",
                    "update": "150203",
                    "replace": "150206",
                },
                "relevance": "True",
                # "condition": "INPUT>100",
                "default": "0"
            },
            {
                "type": "number",
                "name": "childsum",
                "label": {
                    "en": "Child sum",
                    "fr": "Montant pour enfant"
                },
                "rights": {
                    "read": "150201",
                    "write": "150202",
                    "update": "150203",
                    "replace": "150206",
                },
                "relevance": "True",
                # "condition": "INPUT>100",
                "default": "0"
            },
            {
                "type": "number",
                "name": "adultmalesum",
                "label": {
                    "en": "Amount for adult man",
                    "fr": "Montant pour homme adulte"
                },
                "rights": {
                    "read": "150201",
                    "write": "150202",
                    "update": "150203",
                    "replace": "150206",
                },
                "relevance": "True",
                # "condition": "INPUT>100",
                "default": "0"
            },
            {
                "type": "number",
                "name": "adultfemalesum",
                "label": {
                    "en": "Amount for adult woman",
                    "fr": "Montant pour femme adulte"
                },
                "rights": {
                    "read": "150201",
                    "write": "150202",
                    "update": "150203",
                    "replace": "150206",
                },
                "relevance": "True",
                # "condition": "INPUT>100",
                "default": "0"
            },
        ],
    },
]

FROM_TO = [
        {"from": "Policy", "to": "Invoice"},
        {"from": "ContractContributionPlanDetails", "to": "InvoiceLine"}
]

DESCRIPTION_CONTRIBUTION_VALUATION = F"" \
    F"This calculation will, for the selected level and product," \
    F" calculate how much the insuree will have to" \
    F" pay based on the familly and the product modeling,"
