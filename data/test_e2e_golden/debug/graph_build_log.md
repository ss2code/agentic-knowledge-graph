# Graph Build Log - 2026-02-01

### ℹ️ Constraint Creation (2026-02-01 22:56:29)
```text
Starting uniqueness constraints checks...
```

### ✅ Constraint for Product (2026-02-01 22:56:29)
```text
Property: id
Query: CREATE CONSTRAINT IF NOT EXISTS FOR (n:Product) REQUIRE n.id IS UNIQUE
```

### ✅ Constraint for Ingredient (2026-02-01 22:56:29)
```text
Property: id
Query: CREATE CONSTRAINT IF NOT EXISTS FOR (n:Ingredient) REQUIRE n.id IS UNIQUE
```

### ℹ️ Node Import (2026-02-01 22:56:29)
```text
Starting node batch import...
```

### ✅ Import Product (2026-02-01 22:56:29)
```text
File: products.csv
Query: 
                LOAD CSV WITH HEADERS FROM 'file:///products.csv' AS row
                MERGE (n:Product { id: row['id'] })
                
SET n.name = row['name']
```

### ✅ Import Ingredient (2026-02-01 22:56:29)
```text
File: products.csv
Query: 
                LOAD CSV WITH HEADERS FROM 'file:///products.csv' AS row
                MERGE (n:Ingredient { id: row['id'] })
                
SET n.name = row['name']
```

### ℹ️ Relationship Import (2026-02-01 22:56:29)
```text
Starting relationship import...
```

## Unstructured Extraction Results (1 Entities)
- (:) {"name": "TestProduct"}
