# Graph Build Log - 2026-02-01

### ℹ️ Constraint Creation (2026-02-01 23:19:00)
```text
Starting uniqueness constraints checks...
```

### ✅ Constraint for Product (2026-02-01 23:19:00)
```text
Property: id
Query: CREATE CONSTRAINT IF NOT EXISTS FOR (n:Product) REQUIRE n.id IS UNIQUE
```

### ✅ Constraint for ProductCategory (2026-02-01 23:19:00)
```text
Property: category
Query: CREATE CONSTRAINT IF NOT EXISTS FOR (n:ProductCategory) REQUIRE n.category IS UNIQUE
```

### ✅ Constraint for Ingredient (2026-02-01 23:19:00)
```text
Property: ingredients
Query: CREATE CONSTRAINT IF NOT EXISTS FOR (n:Ingredient) REQUIRE n.ingredients IS UNIQUE
```

### ✅ Constraint for CustomerReview (2026-02-01 23:19:00)
```text
Property: review_id
Query: CREATE CONSTRAINT IF NOT EXISTS FOR (n:CustomerReview) REQUIRE n.review_id IS UNIQUE
```

### ✅ Constraint for Sentiment (2026-02-01 23:19:00)
```text
Property: sentiment_label
Query: CREATE CONSTRAINT IF NOT EXISTS FOR (n:Sentiment) REQUIRE n.sentiment_label IS UNIQUE
```

### ✅ Constraint for CustomerExperience (2026-02-01 23:19:00)
```text
Property: experience_phrase
Query: CREATE CONSTRAINT IF NOT EXISTS FOR (n:CustomerExperience) REQUIRE n.experience_phrase IS UNIQUE
```

### ℹ️ Node Import (2026-02-01 23:19:00)
```text
Starting node batch import...
```

### ✅ Import Product (2026-02-01 23:19:00)
```text
File: products.csv
Query: 
                LOAD CSV WITH HEADERS FROM 'file:///products.csv' AS row
                MERGE (n:Product { id: row['id'] })
                
SET n.name = row['name']
```

### ✅ Import ProductCategory (2026-02-01 23:19:00)
```text
File: products.csv
Query: 
                LOAD CSV WITH HEADERS FROM 'file:///products.csv' AS row
                MERGE (n:ProductCategory { category: row['category'] })
                
```

### ✅ Import Ingredient (2026-02-01 23:19:00)
```text
File: products.csv
Query: 
                LOAD CSV WITH HEADERS FROM 'file:///products.csv' AS row
                MERGE (n:Ingredient { ingredients: row['ingredients'] })
                
SET n.name = row['name']
```

### ✅ Import CustomerReview (2026-02-01 23:19:00)
```text
File: reviews.txt
Query: 
                LOAD CSV FROM 'file:///reviews.txt' AS line
                WITH line, linenumber() AS ln
                WHERE line[0] IS NOT NULL
                MERGE (n:CustomerReview { review_id: toString(ln) })
                SET n.text = line[0]
                
```

### ✅ Import Sentiment (2026-02-01 23:19:00)
```text
File: reviews.txt
Query: 
                LOAD CSV FROM 'file:///reviews.txt' AS line
                WITH line, linenumber() AS ln
                WHERE line[0] IS NOT NULL
                MERGE (n:Sentiment { sentiment_label: toString(ln) })
                SET n.text = line[0]
                
```

### ✅ Import CustomerExperience (2026-02-01 23:19:00)
```text
File: reviews.txt
Query: 
                LOAD CSV FROM 'file:///reviews.txt' AS line
                WITH line, linenumber() AS ln
                WHERE line[0] IS NOT NULL
                MERGE (n:CustomerExperience { experience_phrase: toString(ln) })
                SET n.text = line[0]
                
```

### ℹ️ Relationship Import (2026-02-01 23:19:00)
```text
Starting relationship import...
```

### ✅ Import Rel BELONGS_TO (2026-02-01 23:19:00)
```text
Query: 
                 LOAD CSV WITH HEADERS FROM 'file:///products.csv' AS row
                 MATCH (source:Product { id: row['id'] })
                 MATCH (target:ProductCategory { category: row['category'] })
                 MERGE (source)-[r:BELONGS_TO]->(target)
                 
```

### ✅ Import Rel Split CONTAINS_INGREDIENT (2026-02-01 23:19:01)
```text
Query: 
                 LOAD CSV WITH HEADERS FROM 'file:///products.csv' AS row
                 MATCH (source:Product { id: row['id'] })
                 UNWIND split(row['ingredients'], ',') AS item
                 WITH source, trim(item) AS cleaned_item
                 MERGE (target:Ingredient { ingredients: cleaned_item })
                 MERGE (source)-[r:CONTAINS_INGREDIENT]->(target)
                 
```

### ✅ Import Rel MENTIONS_PRODUCT (2026-02-01 23:19:01)
```text
Query: 
                 LOAD CSV WITH HEADERS FROM 'file:///reviews.txt' AS row
                 MATCH (source:CustomerReview { review_id: row['review_id'] })
                 MATCH (target:Product { name: row['name'] })
                 MERGE (source)-[r:MENTIONS_PRODUCT]->(target)
                 
```

### ✅ Import Rel HAS_SENTIMENT (2026-02-01 23:19:01)
```text
Query: 
                 LOAD CSV WITH HEADERS FROM 'file:///reviews.txt' AS row
                 MATCH (source:CustomerReview { review_id: row['review_id'] })
                 MATCH (target:Sentiment { sentiment_label: row['sentiment_label'] })
                 MERGE (source)-[r:HAS_SENTIMENT]->(target)
                 
```

### ✅ Import Rel REPORTED_EXPERIENCE (2026-02-01 23:19:01)
```text
Query: 
                 LOAD CSV WITH HEADERS FROM 'file:///reviews.txt' AS row
                 MATCH (source:CustomerReview { review_id: row['review_id'] })
                 MATCH (target:CustomerExperience { experience_phrase: row['experience_phrase'] })
                 MERGE (source)-[r:REPORTED_EXPERIENCE]->(target)
                 
```

### ✅ Import Rel RELATED_TO_INGREDIENT (2026-02-01 23:19:01)
```text
Query: 
                 LOAD CSV WITH HEADERS FROM 'file:///reviews.txt' AS row
                 MATCH (source:CustomerExperience { experience_phrase: row['experience_phrase'] })
                 MATCH (target:Ingredient { name: row['name'] })
                 MERGE (source)-[r:RELATED_TO_INGREDIENT]->(target)
                 
```

## Unstructured Extraction Results (26 Entities)
- (:) {"name": "House Salad"}
- (:) {"name": "Lettuce"}
- (:) {"name": "Soggy"}
- (:) {"name": "Pepperoni Pizza"}
- (:) {"name": "Chardonnay"}
- (:) {"name": "Chardonnay Grapes"}
- (:) {"name": "Bland"}
- (:) {"name": "Bruschetta"}
- (:) {"name": "Basil"}
- (:) {"name": "Tiramisu"}
- (:) {"name": "Cocoa"}
- (:) {"name": "Rotten"}
- (:) {"name": "Espresso"}
- (:) {"name": "Coffee Beans"}
- (:) {"name": "Spaghetti Carbonara"}
- (:) {"name": "Cheese"}
- (:) {"name": "Gelato"}
- (:) {"name": "Sugar"}
- (:) {"name": "Stale"}
- (:) {"name": "Vanilla"}
- (:) {"name": "Tomato"}
- (:) {"name": "Cold"}
- (:) {"name": "Bread"}
- (:) {"name": "Margherita Pizza"}
- (:) {"name": "Too Salty"}
- (:) {"name": "Chianti Classico"}
