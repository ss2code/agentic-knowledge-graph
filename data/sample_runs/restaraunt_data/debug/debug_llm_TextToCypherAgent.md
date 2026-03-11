# Text-to-Cypher Debug Log (Run Fresh)

## [2026-02-06 15:59:05] INITIAL SCHEMA CONTEXT
```json
{
  "Issue": {
    "count": 12,
    "relationships": {
      "FROM_CHUNK": {
        "count": 0,
        "properties": {},
        "direction": "out",
        "labels": [
          "__KGBuilder__",
          "Chunk"
        ]
      },
      "PART_OF": {
        "count": 0,
        "properties": {},
        "direction": "out",
        "labels": [
          "Ingredient",
          "__KGBuilder__",
          "__Entity__"
        ]
      },
      "HAS_ISSUE": {
        "count": 21,
        "properties": {},
        "direction": "in",
        "labels": [
          "Product",
          "__KGBuilder__",
          "__Entity__"
        ]
      }
    },
    "type": "node",
    "properties": {
      "description": {
        "existence": false,
        "type": "STRING",
        "indexed": false,
        "unique": false
      }
    },
    "labels": []
  },
  "Product": {
    "count": 20,
    "relationships": {
      "FROM_CHUNK": {
        "count": 0,
        "properties": {},
        "direction": "out",
        "labels": [
          "__KGBuilder__",
          "Chunk"
        ]
      },
      "BELONGS_TO": {
        "count": 0,
        "properties": {},
        "direction": "out",
        "labels": [
          "ProductCategory"
        ]
      },
      "HAS_ISSUE": {
        "count": 0,
        "properties": {},
        "direction": "out",
        "labels": [
          "__KGBuilder__",
          "__Entity__",
          "Issue"
        ]
      },
      "MENTIONS": {
        "count": 0,
        "properties": {},
        "direction": "out",
        "labels": [
          "Ingredient",
          "__KGBuilder__",
          "__Entity__"
        ]
      },
      "CORRESPONDS_TO": {
        "count": 0,
        "properties": {
          "score": {
            "existence": false,
            "type": "FLOAT",
            "array": false,
            "indexed": false
          },
          "created_at": {
            "existence": false,
            "type": "DATE_TIME",
            "array": false,
            "indexed": false
          }
        },
        "direction": "out",
        "labels": [
          "Product"
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
  "PART_OF": {
    "count": 11,
    "type": "relationship",
    "properties": {}
  },
  "Document": {
    "count": 1,
    "relationships": {
      "FROM_DOCUMENT": {
        "count": 1,
        "properties": {},
        "direction": "in",
        "labels": [
          "__KGBuilder__",
          "Chunk"
        ]
      }
    },
    "type": "node",
    "properties": {
      "path": {
        "existence": false,
        "type": "STRING",
        "indexed": false,
        "unique": false
      },
      "createdAt": {
        "existence": false,
        "type": "STRING",
        "indexed": false,
        "unique": false
      },
      "title": {
        "existence": false,
        "type": "STRING",
        "indexed": false,
        "unique": false
      }
    },
    "labels": []
  },
  "Chunk": {
    "count": 1,
    "relationships": {
      "FROM_DOCUMENT": {
        "count": 0,
        "properties": {},
        "direction": "out",
        "labels": [
          "__KGBuilder__",
          "Document"
        ]
      },
      "FROM_CHUNK": {
        "count": 10,
        "properties": {},
        "direction": "in",
        "labels": [
          "Product",
          "Ingredient",
          "__KGBuilder__",
          "__Entity__",
          "Issue"
        ]
      }
    },
    "type": "node",
    "properties": {
      "index": {
        "existence": false,
        "type": "INTEGER",
        "indexed": false,
        "unique": false
      },
      "text": {
        "existence": false,
        "type": "STRING",
        "indexed": false,
        "unique": false
      },
      "embedding": {
        "existence": false,
        "type": "LIST",
        "indexed": false,
        "unique": false
      }
    },
    "labels": []
  },
  "HAS_ISSUE": {
    "count": 21,
    "type": "relationship",
    "properties": {}
  },
  "MENTIONS": {
    "count": 10,
    "type": "relationship",
    "properties": {}
  },
  "Sentiment": {
    "count": 50,
    "relationships": {},
    "type": "node",
    "properties": {
      "derived_sentiment": {
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
  "FROM_CHUNK": {
    "count": 32,
    "type": "relationship",
    "properties": {}
  },
  "Ingredient": {
    "count": 20,
    "relationships": {
      "FROM_CHUNK": {
        "count": 0,
        "properties": {},
        "direction": "out",
        "labels": [
          "__KGBuilder__",
          "Chunk"
        ]
      },
      "PART_OF": {
        "count": 11,
        "properties": {},
        "direction": "in",
        "labels": [
          "__KGBuilder__",
          "__Entity__",
          "Issue"
        ]
      },
      "MENTIONS": {
        "count": 10,
        "properties": {},
        "direction": "in",
        "labels": [
          "Product",
          "__KGBuilder__",
          "__Entity__"
        ]
      },
      "CORRESPONDS_TO": {
        "count": 0,
        "properties": {
          "score": {
            "existence": false,
            "type": "FLOAT",
            "array": false,
            "indexed": false
          },
          "created_at": {
            "existence": false,
            "type": "DATE_TIME",
            "array": false,
            "indexed": false
          }
        },
        "direction": "out",
        "labels": [
          "Ingredient"
        ]
      },
      "CONTAINS_INGREDIENT": {
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
      "name": {
        "existence": false,
        "type": "STRING",
        "indexed": false,
        "unique": false
      },
      "ingredients": {
        "existence": false,
        "type": "STRING",
        "indexed": true,
        "unique": true
      }
    },
    "labels": []
  },
  "CustomerExperience": {
    "count": 50,
    "relationships": {},
    "type": "node",
    "properties": {
      "extracted_aspect": {
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
  "__Entity__": {
    "count": 32,
    "relationships": {
      "FROM_CHUNK": {
        "count": 0,
        "properties": {},
        "direction": "out",
        "labels": [
          "__KGBuilder__",
          "Chunk"
        ]
      },
      "PART_OF": {
        "count": 0,
        "properties": {},
        "direction": "out",
        "labels": [
          "Ingredient",
          "__KGBuilder__",
          "__Entity__"
        ]
      },
      "HAS_ISSUE": {
        "count": 0,
        "properties": {},
        "direction": "out",
        "labels": [
          "__KGBuilder__",
          "__Entity__",
          "Issue"
        ]
      },
      "MENTIONS": {
        "count": 0,
        "properties": {},
        "direction": "out",
        "labels": [
          "Ingredient",
          "__KGBuilder__",
          "__Entity__"
        ]
      },
      "CORRESPONDS_TO": {
        "count": 0,
        "properties": {
          "score": {
            "existence": false,
            "type": "FLOAT",
            "array": false,
            "indexed": false
          },
          "created_at": {
            "existence": false,
            "type": "DATE_TIME",
            "array": false,
            "indexed": false
          }
        },
        "direction": "out",
        "labels": [
          "Product",
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
      "description": {
        "existence": false,
        "type": "STRING",
        "indexed": false,
        "unique": false
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
  "__KGBuilder__": {
    "count": 34,
    "relationships": {
      "FROM_CHUNK": {
        "count": 0,
        "properties": {},
        "direction": "out",
        "labels": [
          "__KGBuilder__",
          "Chunk"
        ]
      },
      "PART_OF": {
        "count": 0,
        "properties": {},
        "direction": "out",
        "labels": [
          "Ingredient",
          "__KGBuilder__",
          "__Entity__"
        ]
      },
      "FROM_DOCUMENT": {
        "count": 0,
        "properties": {},
        "direction": "out",
        "labels": [
          "__KGBuilder__",
          "Document"
        ]
      },
      "HAS_ISSUE": {
        "count": 0,
        "properties": {},
        "direction": "out",
        "labels": [
          "__KGBuilder__",
          "__Entity__",
          "Issue"
        ]
      },
      "MENTIONS": {
        "count": 0,
        "properties": {},
        "direction": "out",
        "labels": [
          "Ingredient",
          "__KGBuilder__",
          "__Entity__"
        ]
      },
      "CORRESPONDS_TO": {
        "count": 0,
        "properties": {
          "score": {
            "existence": false,
            "type": "FLOAT",
            "array": false,
            "indexed": false
          },
          "created_at": {
            "existence": false,
            "type": "DATE_TIME",
            "array": false,
            "indexed": false
          }
        },
        "direction": "out",
        "labels": [
          "Product",
          "Ingredient"
        ]
      }
    },
    "type": "node",
    "properties": {
      "path": {
        "existence": false,
        "type": "STRING",
        "indexed": false,
        "unique": false
      },
      "createdAt": {
        "existence": false,
        "type": "STRING",
        "indexed": false,
        "unique": false
      },
      "name": {
        "existence": false,
        "type": "STRING",
        "indexed": false,
        "unique": false
      },
      "index": {
        "existence": false,
        "type": "INTEGER",
        "indexed": false,
        "unique": false
      },
      "description": {
        "existence": false,
        "type": "STRING",
        "indexed": false,
        "unique": false
      },
      "text": {
        "existence": false,
        "type": "STRING",
        "indexed": false,
        "unique": false
      },
      "embedding": {
        "existence": false,
        "type": "LIST",
        "indexed": false,
        "unique": false
      },
      "title": {
        "existence": false,
        "type": "STRING",
        "indexed": false,
        "unique": false
      }
    },
    "labels": []
  },
  "FROM_DOCUMENT": {
    "count": 1,
    "type": "relationship",
    "properties": {}
  },
  "CustomerReview": {
    "count": 50,
    "relationships": {},
    "type": "node",
    "properties": {
      "review_text": {
        "existence": false,
        "type": "STRING",
        "indexed": false,
        "unique": false
      },
      "hash_id": {
        "existence": false,
        "type": "STRING",
        "indexed": true,
        "unique": true
      }
    },
    "labels": []
  },
  "CORRESPONDS_TO": {
    "count": 11,
    "type": "relationship",
    "properties": {
      "score": {
        "existence": false,
        "type": "FLOAT",
        "array": false,
        "indexed": false
      },
      "created_at": {
        "existence": false,
        "type": "DATE_TIME",
        "array": false,
        "indexed": false
      }
    }
  },
  "CONTAINS_INGREDIENT": {
    "count": 10,
    "type": "relationship",
    "properties": {}
  }
}
```

---

## [2026-02-06 15:59:05] User Query
**Input:** `list all the issues along with frequency of occurance`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (i:Issue) RETURN i.description, count(i) AS frequency ORDER BY frequency DESC LIMIT 20
```

---
**Execution Results:**
```json
[
  {
    "i.description": "slow service",
    "frequency": 1
  },
  {
    "i.description": "soggy Lettuce",
    "frequency": 1
  },
  {
    "i.description": "bland Chardonnay Grapes",
    "frequency": 1
  },
  {
    "i.description": "soggy Basil",
    "frequency": 1
  },
  {
    "i.description": "rotten Cocoa",
    "frequency": 1
  },
  {
    "i.description": "rotten Coffee Beans",
    "frequency": 1
  },
  {
    "i.description": "soggy Cheese",
    "frequency": 1
  },
  {
    "i.description": "stale Sugar",
    "frequency": 1
  },
  {
    "i.description": "soggy Vanilla",
    "frequency": 1
  },
  {
    "i.description": "cold Tomato",
    "frequency": 1
  },
  {
    "i.description": "stale Bread",
    "frequency": 1
  },
  {
    "i.description": "too salty Coffee Beans",
    "frequency": 1
  }
]
```

---
## [2026-02-06 15:59:45] User Query
**Input:** `trace each issue to the product`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (p:Product)-[:HAS_ISSUE]->(i:Issue) RETURN p.name, i.description LIMIT 20
```

---
**Execution Results:**
```json
[
  {
    "p.name": "Espresso",
    "i.description": "slow service"
  },
  {
    "p.name": "Bruschetta",
    "i.description": "slow service"
  },
  {
    "p.name": "Spaghetti Carbonara",
    "i.description": "slow service"
  },
  {
    "p.name": "Margherita Pizza",
    "i.description": "slow service"
  },
  {
    "p.name": "Chardonnay",
    "i.description": "slow service"
  },
  {
    "p.name": "House Salad",
    "i.description": "slow service"
  },
  {
    "p.name": "Chianti Classico",
    "i.description": "slow service"
  },
  {
    "p.name": "Gelato",
    "i.description": "slow service"
  },
  {
    "p.name": "Pepperoni Pizza",
    "i.description": "slow service"
  },
  {
    "p.name": "Tiramisu",
    "i.description": "slow service"
  },
  {
    "p.name": "House Salad",
    "i.description": "soggy Lettuce"
  },
  {
    "p.name": "Chardonnay",
    "i.description": "bland Chardonnay Grapes"
  },
  {
    "p.name": "Bruschetta",
    "i.description": "soggy Basil"
  },
  {
    "p.name": "Tiramisu",
    "i.description": "rotten Cocoa"
  },
  {
    "p.name": "Espresso",
    "i.description": "rotten Coffee Beans"
  },
  {
    "p.name": "Spaghetti Carbonara",
    "i.description": "soggy Cheese"
  },
  {
    "p.name": "Gelato",
    "i.description": "stale Sugar"
  },
  {
    "p.name": "Gelato",
    "i.description": "soggy Vanilla"
  },
  {
    "p.name": "House Salad",
    "i.description": "cold Tomato"
  },
  {
    "p.name": "Bruschetta",
    "i.description": "stale Bread"
  }
]
```

---
## [2026-02-06 16:00:30] User Query
**Input:** `list all the products that showed slow service`
**Model Used:** `gemini-2.0-flash`

**Error:** Returned N/A

---
## [2026-02-06 16:01:06] User Query
**Input:** `which products were "slow service"`
**Model Used:** `gemini-2.0-flash`

**Error:** Returned N/A

---
## [2026-02-06 16:01:36] User Query
**Input:** `which product had issue stale Bread`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (p:Product)-[:HAS_ISSUE]->(i:Issue) WHERE i.description = "stale Bread" RETURN p.name LIMIT 20
```

---
**Execution Results:**
```json
[
  {
    "p.name": "Bruschetta"
  }
]
```

---
## [2026-02-06 16:01:50] User Query
**Input:** `which product had issue slow service`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (p:Product)-[r:HAS_ISSUE]->(i:Issue) WHERE i.description = "slow service" RETURN p.name LIMIT 20
```

---
**Execution Results:**
```json
[
  {
    "p.name": "Espresso"
  },
  {
    "p.name": "Bruschetta"
  },
  {
    "p.name": "Spaghetti Carbonara"
  },
  {
    "p.name": "Margherita Pizza"
  },
  {
    "p.name": "Chardonnay"
  },
  {
    "p.name": "House Salad"
  },
  {
    "p.name": "Chianti Classico"
  },
  {
    "p.name": "Gelato"
  },
  {
    "p.name": "Pepperoni Pizza"
  },
  {
    "p.name": "Tiramisu"
  }
]
```

---
