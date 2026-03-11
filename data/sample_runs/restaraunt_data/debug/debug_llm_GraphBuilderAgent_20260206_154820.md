
### ℹ️ Constraint Creation (2026-02-06 15:48:25)
```text
Starting uniqueness constraints checks...
```

### ✅ Constraint for Product (2026-02-06 15:48:25)
```text
Property: id
Query: CREATE CONSTRAINT IF NOT EXISTS FOR (n:Product) REQUIRE n.id IS UNIQUE
```

### ✅ Constraint for ProductCategory (2026-02-06 15:48:25)
```text
Property: category
Query: CREATE CONSTRAINT IF NOT EXISTS FOR (n:ProductCategory) REQUIRE n.category IS UNIQUE
```

### ✅ Constraint for Ingredient (2026-02-06 15:48:25)
```text
Property: ingredients
Query: CREATE CONSTRAINT IF NOT EXISTS FOR (n:Ingredient) REQUIRE n.ingredients IS UNIQUE
```

### ✅ Constraint for CustomerReview (2026-02-06 15:48:25)
```text
Property: hash_id
Query: CREATE CONSTRAINT IF NOT EXISTS FOR (n:CustomerReview) REQUIRE n.hash_id IS UNIQUE
```

### ✅ Constraint for Sentiment (2026-02-06 15:48:25)
```text
Property: derived_sentiment
Query: CREATE CONSTRAINT IF NOT EXISTS FOR (n:Sentiment) REQUIRE n.derived_sentiment IS UNIQUE
```

### ✅ Constraint for CustomerExperience (2026-02-06 15:48:25)
```text
Property: extracted_aspect
Query: CREATE CONSTRAINT IF NOT EXISTS FOR (n:CustomerExperience) REQUIRE n.extracted_aspect IS UNIQUE
```

### ℹ️ Node Import (2026-02-06 15:48:25)
```text
Starting node batch import...
```

### ✅ Import Product (2026-02-06 15:48:25)
```text
Query: 
            LOAD CSV WITH HEADERS FROM 'file:///products.csv' AS row
            MERGE (n:Product { id: row['id'] })
            
SET n.name = row['name']
```

### ✅ Import ProductCategory (2026-02-06 15:48:25)
```text
Query: 
            LOAD CSV WITH HEADERS FROM 'file:///products.csv' AS row
            MERGE (n:ProductCategory { category: row['category'] })
            
```

### ✅ Import Ingredient (2026-02-06 15:48:25)
```text
Query: 
            LOAD CSV WITH HEADERS FROM 'file:///products.csv' AS row
            MERGE (n:Ingredient { ingredients: row['ingredients'] })
            
SET n.name = row['name']
```

### ✅ Import CustomerReview (2026-02-06 15:48:25)
```text
Query: 
            LOAD CSV FROM 'file:///reviews.txt' AS line
            WITH line, linenumber() AS ln
            WHERE line[0] IS NOT NULL
            MERGE (n:CustomerReview { hash_id: toString(ln) })
            SET n.review_text = line[0]
            
```

### ✅ Import Sentiment (2026-02-06 15:48:25)
```text
Query: 
            LOAD CSV FROM 'file:///reviews.txt' AS line
            WITH line, linenumber() AS ln
            WHERE line[0] IS NOT NULL
            MERGE (n:Sentiment { derived_sentiment: toString(ln) })
            SET n.text = line[0]
            
```

### ✅ Import CustomerExperience (2026-02-06 15:48:25)
```text
Query: 
            LOAD CSV FROM 'file:///reviews.txt' AS line
            WITH line, linenumber() AS ln
            WHERE line[0] IS NOT NULL
            MERGE (n:CustomerExperience { extracted_aspect: toString(ln) })
            SET n.text = line[0]
            
```

### ℹ️ Relationship Import (2026-02-06 15:48:25)
```text
Starting relationship import...
```

### ✅ Rel BELONGS_TO (2026-02-06 15:48:25)
```text
Query: 
            LOAD CSV WITH HEADERS FROM 'file:///products.csv' AS row
            MATCH (source:Product { id: row['id'] })
            MATCH (target:ProductCategory { category: row['category'] })
            MERGE (source)-[r:BELONGS_TO]->(target)
            
```

### ✅ Rel CONTAINS_INGREDIENT (2026-02-06 15:48:25)
```text
Query: 
            LOAD CSV WITH HEADERS FROM 'file:///products.csv' AS row
            MATCH (source:Product { id: row['id'] })
            MATCH (target:Ingredient { ingredients: row['ingredients'] })
            MERGE (source)-[r:CONTAINS_INGREDIENT]->(target)
            
```

### ✅ Rel DISCUSSES_PRODUCT (2026-02-06 15:48:25)
```text
Query: 
            LOAD CSV WITH HEADERS FROM 'file:///reviews.txt' AS row
            MATCH (source:CustomerReview { review_text: row['review_text'] })
            MATCH (target:Product { name: row['name'] })
            MERGE (source)-[r:DISCUSSES_PRODUCT]->(target)
            
```

### ✅ Rel HAS_SENTIMENT (2026-02-06 15:48:25)
```text
Query: 
            LOAD CSV WITH HEADERS FROM 'file:///reviews.txt' AS row
            MATCH (source:CustomerReview { hash_id: row['hash_id'] })
            MATCH (target:Sentiment { derived_sentiment: row['derived_sentiment'] })
            MERGE (source)-[r:HAS_SENTIMENT]->(target)
            
```

### ✅ Rel REFLECTS_EXPERIENCE (2026-02-06 15:48:25)
```text
Query: 
            LOAD CSV WITH HEADERS FROM 'file:///reviews.txt' AS row
            MATCH (source:CustomerReview { hash_id: row['hash_id'] })
            MATCH (target:CustomerExperience { extracted_aspect: row['extracted_aspect'] })
            MERGE (source)-[r:REFLECTS_EXPERIENCE]->(target)
            
```

### ✅ Rel MENTIONS_INGREDIENT (2026-02-06 15:48:25)
```text
Query: 
            LOAD CSV WITH HEADERS FROM 'file:///reviews.txt' AS row
            MATCH (source:CustomerReview { review_text: row['review_text'] })
            MATCH (target:Ingredient { name: row['name'] })
            MERGE (source)-[r:MENTIONS_INGREDIENT]->(target)
            
```
