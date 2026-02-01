# Text-to-Cypher Debug Log

## [2026-02-01 23:05:21] INITIAL SCHEMA CONTEXT
```json
{
  "Ingredient": {
    "count": 33,
    "relationships": {
      "CONTAINS_INGREDIENT": {
        "count": 30,
        "properties": {},
        "direction": "in",
        "labels": [
          "Product"
        ]
      }
    },
    "type": "node",
    "properties": {
      "name": {
        "existence": false,
        "type": "STRING",
        "indexed": true,
        "unique": true
      }
    },
    "labels": []
  },
  "BELONGS_TO": {
    "count": 10,
    "type": "relationship",
    "properties": {}
  },
  "ProductCategory": {
    "count": 4,
    "relationships": {
      "BELONGS_TO": {
        "count": 10,
        "properties": {},
        "direction": "in",
        "labels": [
          "Product"
        ]
      }
    },
    "type": "node",
    "properties": {
      "category": {
        "existence": false,
        "type": "STRING",
        "indexed": true,
        "unique": true
      }
    },
    "labels": []
  },
  "Product": {
    "count": 10,
    "relationships": {
      "BELONGS_TO": {
        "count": 0,
        "properties": {},
        "direction": "out",
        "labels": [
          "ProductCategory"
        ]
      },
      "CONTAINS_INGREDIENT": {
        "count": 0,
        "properties": {},
        "direction": "out",
        "labels": [
          "Ingredient"
        ]
      }
    },
    "type": "node",
    "properties": {
      "name": {
        "existence": false,
        "type": "STRING",
        "indexed": false,
        "unique": false
      },
      "id": {
        "existence": false,
        "type": "STRING",
        "indexed": true,
        "unique": true
      }
    },
    "labels": []
  },
  "CustomerReview": {
    "count": 50,
    "relationships": {},
    "type": "node",
    "properties": {
      "review_id": {
        "existence": false,
        "type": "STRING",
        "indexed": true,
        "unique": true
      },
      "text": {
        "existence": false,
        "type": "STRING",
        "indexed": false,
        "unique": false
      }
    },
    "labels": []
  },
  "Sentiment": {
    "count": 50,
    "relationships": {},
    "type": "node",
    "properties": {
      "text": {
        "existence": false,
        "type": "STRING",
        "indexed": false,
        "unique": false
      },
      "polarity": {
        "existence": false,
        "type": "STRING",
        "indexed": true,
        "unique": true
      }
    },
    "labels": []
  },
  "CustomerComplaint": {
    "count": 50,
    "relationships": {},
    "type": "node",
    "properties": {
      "issue": {
        "existence": false,
        "type": "STRING",
        "indexed": true,
        "unique": true
      },
      "text": {
        "existence": false,
        "type": "STRING",
        "indexed": false,
        "unique": false
      }
    },
    "labels": []
  },
  "CONTAINS_INGREDIENT": {
    "count": 30,
    "type": "relationship",
    "properties": {}
  }
}
```

---

## [2026-02-01 23:05:21] User Query
**Input:** `list ingredient`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (i:Ingredient) RETURN i.name LIMIT 20
```

---
**Execution Results:**
```json
Count: 20
Sample: [{"i.name": "Flour"}, {"i.name": "Tomato"}, {"i.name": "Cheese"}, {"i.name": "Basil"}, {"i.name": "Pepperoni"}]
```

---
## [2026-02-01 23:05:26] User Query
**Input:** `list product`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (p:Product) RETURN p.name LIMIT 20
```

---
**Execution Results:**
```json
Count: 10
Sample: [{"p.name": "Margherita Pizza"}, {"p.name": "Pepperoni Pizza"}, {"p.name": "House Salad"}, {"p.name": "Tiramisu"}, {"p.name": "Chianti Classico"}]
```

---
## [2026-02-01 23:05:33] User Query
**Input:** `what are the top issues`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (n:CustomerComplaint) RETURN n.issue LIMIT 20
```

---
**Execution Results:**
```json
Count: 20
Sample: [{"n.issue": "19"}, {"n.issue": "20"}, {"n.issue": "21"}, {"n.issue": "22"}, {"n.issue": "23"}]
```

---
## [2026-02-01 23:05:42] User Query
**Input:** `name top issue`
**Model Used:** `gemini-2.0-flash`

**Error:** Returned N/A

---
