# Graph Build Log - 2026-01-31

### ℹ️ Constraint Creation (2026-01-31 09:48:59)
```text
Starting uniqueness constraints checks...
```

### ✅ Constraint for Product (2026-01-31 09:48:59)
```text
Property: id
Query: CREATE CONSTRAINT IF NOT EXISTS FOR (n:Product) REQUIRE n.id IS UNIQUE
```

### ✅ Constraint for ProductCategory (2026-01-31 09:48:59)
```text
Property: category
Query: CREATE CONSTRAINT IF NOT EXISTS FOR (n:ProductCategory) REQUIRE n.category IS UNIQUE
```

### ✅ Constraint for Ingredient (2026-01-31 09:48:59)
```text
Property: ingredients
Query: CREATE CONSTRAINT IF NOT EXISTS FOR (n:Ingredient) REQUIRE n.ingredients IS UNIQUE
```

### ✅ Constraint for Review (2026-01-31 09:48:59)
```text
Property: hash_id
Query: CREATE CONSTRAINT IF NOT EXISTS FOR (n:Review) REQUIRE n.hash_id IS UNIQUE
```

### ℹ️ Node Import (2026-01-31 09:48:59)
```text
Starting node batch import...
```

### ✅ Import Product (2026-01-31 09:49:00)
```text
File: products.csv
Query: 
                LOAD CSV WITH HEADERS FROM 'file:///products.csv' AS row
                MERGE (n:Product { id: row['id'] })
                
SET n.name = row['name']
```

### ✅ Import ProductCategory (2026-01-31 09:49:00)
```text
File: products.csv
Query: 
                LOAD CSV WITH HEADERS FROM 'file:///products.csv' AS row
                MERGE (n:ProductCategory { category: row['category'] })
                
```

### ✅ Import Ingredient (2026-01-31 09:49:00)
```text
File: products.csv
Query: 
                LOAD CSV WITH HEADERS FROM 'file:///products.csv' AS row
                MERGE (n:Ingredient { ingredients: row['ingredients'] })
                
SET n.name = row['name']
```

### ✅ Import Review (2026-01-31 09:49:00)
```text
File: reviews.txt
Query: 
                LOAD CSV FROM 'file:///reviews.txt' AS line
                WITH line, linenumber() AS ln
                WHERE line[0] IS NOT NULL
                MERGE (n:Review { hash_id: toString(ln) })
                SET n.text = line[0]
                
```

### ℹ️ Relationship Import (2026-01-31 09:49:00)
```text
Starting relationship import...
```

### ✅ Import Rel BELONGS_TO (2026-01-31 09:49:00)
```text
Query: 
                 LOAD CSV WITH HEADERS FROM 'file:///products.csv' AS row
                 MATCH (source:Product { id: row['id'] })
                 MATCH (target:ProductCategory { category: row['category'] })
                 MERGE (source)-[r:BELONGS_TO]->(target)
                 
```

### ✅ Import Rel Split CONTAINS (2026-01-31 09:49:00)
```text
Query: 
                 LOAD CSV WITH HEADERS FROM 'file:///products.csv' AS row
                 MATCH (source:Product { id: row['id'] })
                 UNWIND split(row['ingredients'], ',') AS item
                 WITH source, trim(item) AS cleaned_item
                 MERGE (target:Ingredient { ingredients: cleaned_item })
                 MERGE (source)-[r:CONTAINS]->(target)
                 
```

### ✅ Import Rel ABOUT_PRODUCT (2026-01-31 09:49:00)
```text
Query: 
                 LOAD CSV WITH HEADERS FROM 'file:///reviews.txt' AS row
                 MATCH (source:Review { text: row['text'] })
                 MATCH (target:Product { name: row['name'] })
                 MERGE (source)-[r:ABOUT_PRODUCT]->(target)
                 
```

### ✅ Import Rel MENTIONS_INGREDIENT (2026-01-31 09:49:00)
```text
Query: 
                 LOAD CSV WITH HEADERS FROM 'file:///reviews.txt' AS row
                 MATCH (source:Review { text: row['text'] })
                 MATCH (target:Ingredient { name: row['name'] })
                 MERGE (source)-[r:MENTIONS_INGREDIENT]->(target)
                 
```
