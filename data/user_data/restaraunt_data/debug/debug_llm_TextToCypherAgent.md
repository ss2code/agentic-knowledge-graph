# Text-to-Cypher Debug Log

## [2026-02-01 23:19:49] INITIAL SCHEMA CONTEXT
```json
{
  "Issue": {
    "count": 6,
    "relationships": {
      "HAS_ISSUE": {
        "count": 11,
        "properties": {},
        "direction": "in",
        "labels": [
          "Ingredient",
          "__KGBuilder__",
          "__Entity__"
        ]
      },
      "FROM_CHUNK": {
        "count": 0,
        "properties": {},
        "direction": "out",
        "labels": [
          "__KGBuilder__",
          "Chunk"
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
  "PART_OF": {
    "count": 10,
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
    "count": 11,
    "type": "relationship",
    "properties": {}
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
      "sentiment_label": {
        "existence": false,
        "type": "STRING",
        "indexed": true,
        "unique": true
      }
    },
    "labels": []
  },
  "FROM_CHUNK": {
    "count": 26,
    "type": "relationship",
    "properties": {}
  },
  "Ingredient": {
    "count": 40,
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
        "count": 10,
        "properties": {},
        "direction": "in",
        "labels": [
          "Product",
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
      },
      "ingredients": {
        "existence": false,
        "type": "STRING",
        "indexed": true,
        "unique": true
      }
    },
    "labels": [
      "__KGBuilder__",
      "__Entity__"
    ]
  },
  "CustomerExperience": {
    "count": 50,
    "relationships": {},
    "type": "node",
    "properties": {
      "experience_phrase": {
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
    "count": 26,
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
    "count": 28,
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
      "FROM_DOCUMENT": {
        "count": 0,
        "properties": {},
        "direction": "out",
        "labels": [
          "__KGBuilder__",
          "Document"
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
    "count": 30,
    "type": "relationship",
    "properties": {}
  }
}
```

---

## [2026-02-01 23:19:49] User Query
**Input:** `what are the top issues`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (i:Issue) RETURN i.name LIMIT 20
```

---
**Execution Results:**
```json
Count: 6
Sample: [{"i.name": "Soggy"}, {"i.name": "Bland"}, {"i.name": "Rotten"}, {"i.name": "Stale"}, {"i.name": "Cold"}]
```

---
## [2026-02-01 23:20:00] User Query
**Input:** `trace product to issue`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (p:Product)-[:CONTAINS_INGREDIENT]->(i:Ingredient)-[:HAS_ISSUE]->(iss:Issue) RETURN p.name AS Product, i.name AS Ingredient, iss.name AS Issue LIMIT 20
```

---
**Execution Results:**
```json
Count: 0
Sample: []
```

---
## [2026-02-01 23:20:18] User Query
**Input:** `trace issue to ingredient`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (i:Ingredient)-[:HAS_ISSUE]->(issue:Issue) RETURN i.name, issue.name LIMIT 20
```

---
**Execution Results:**
```json
Count: 11
Sample: [{"i.name": "Basil", "issue.name": "Soggy"}, {"i.name": "Cheese", "issue.name": "Soggy"}, {"i.name": "Lettuce", "issue.name": "Soggy"}, {"i.name": "Vanilla", "issue.name": "Soggy"}, {"i.name": "Chardonnay Grapes", "issue.name": "Bland"}]
```

---
