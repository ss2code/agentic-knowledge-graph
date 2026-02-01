# Text-to-Cypher Debug Log

## [2026-02-01 21:22:25] User Query
**Input:** `What are the top issues, sort descending order`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (i:Issue) RETURN i.name ORDER BY i.name DESC LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 6

## [2026-02-01 21:23:04] User Query
**Input:** `list all the issues and how frequently they occured`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (i:Issue) RETURN i.name, count(i) AS issue_count ORDER BY issue_count DESC LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 6

## [2026-02-01 21:23:27] User Query
**Input:** `which products were stale`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (i:Ingredient)-[:HAS_ISSUE]->(b:Issue) WHERE b.name = "stale" RETURN i LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 0

## [2026-02-01 21:23:57] User Query
**Input:** `What was stale`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (i:Issue) WHERE i.name = "stale" RETURN i LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 0

## [2026-02-01 21:24:05] User Query
**Input:** `list issues`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (i:Issue) RETURN i.name LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 6

## [2026-02-01 21:24:17] User Query
**Input:** `which Product was Cold`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (p:Product) RETURN p.name LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 20

## [2026-02-01 21:24:50] User Query
**Input:** `which "Product" was "Cold"`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (p:Product)<-[:PART_OF]-(i:Ingredient) WHERE i.ingredient_name = "Cold" RETURN p LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 0

## [2026-02-01 21:25:31] User Query
**Input:** `What was the names of the product that had an issue called Cold`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (i:Issue {name: "Cold"})<-[:HAS_ISSUE]-(ing:Ingredient)<-[:PART_OF]-(p:Product) RETURN p.name LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 2

## [2026-02-01 21:26:11] User Query
**Input:** `what was the names of the product that had an issue called Soggy`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (i:Issue)<-[:HAS_ISSUE]-(ing:Ingredient)<-[:PART_OF]-(p:Product) WHERE i.name = "Soggy" RETURN p.name LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 4

## [2026-02-01 21:26:25] User Query
**Input:** `list the names of the Issue`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (n:Issue) RETURN n.name LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 6

## [2026-02-01 21:26:45] User Query
**Input:** `list the names of the product that had an issue called Bland`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (i:Issue {name: "Bland"})<-[:HAS_ISSUE]-(ing:Ingredient)<-[:PART_OF]-(p:Product) RETURN p.name LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 1

## [2026-02-01 21:27:16] User Query
**Input:** `show me the schema for the graph`
**Model Used:** `gemini-2.0-flash`

**Error:** Returned N/A

---
## [2026-02-01 21:27:47] User Query
**Input:** `get the schema for the graph`
**Model Used:** `gemini-2.0-flash`

**Error:** Returned N/A

---
## [2026-02-01 21:28:26] User Query
**Input:** `list all the nodes in the graph`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (n) RETURN n LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 20

## [2026-02-01 21:29:02] User Query
**Input:** `list the nodes in the graph and format it in a comma separated manner`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (n) RETURN labels(n) LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 20

## [2026-02-01 21:29:19] User Query
**Input:** `how many issues are in the graph`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (n:Issue) RETURN count(n)
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 1

## [2026-02-01 21:29:42] User Query
**Input:** `how many ingredients are there in the graph, list them`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (i:Ingredient) RETURN i.ingredient_name LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 20

## [2026-02-01 21:30:18] User Query
**Input:** `which product names use the ingredient Flour`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (i:Ingredient {ingredient_name: "Flour"})<-[:PART_OF]-(p:Product) RETURN p.name LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 0

## [2026-02-01 21:31:03] User Query
**Input:** `which product have ingredient Basil`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (i:Ingredient {ingredient_name: "Basil"})<-[:PART_OF]-(p:Product) RETURN p.name LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 0

## [2026-02-01 21:31:24] User Query
**Input:** `Basil is used in which Product`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (i:Ingredient {ingredient_name: "Basil"})-[:PART_OF]-(p:Product) RETURN p.name LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 0

## [2026-02-01 21:31:39] User Query
**Input:** `what are the Products`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (n:Product) RETURN n.id, n.name LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 20

## [2026-02-01 21:32:00] User Query
**Input:** `what are the ingredients in Tiramisu`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (i:Ingredient)<-[:PART_OF]-(p:Product {name: "Tiramisu"}) RETURN i.ingredient_name LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 1

## [2026-02-01 21:39:56] User Query
**Input:** `what are the ingredient names in Tiramisu`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (i:Ingredient)-[:PART_OF]->(p:Product) WHERE p.name = "Tiramisu" RETURN i.ingredient_name LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 0

## [2026-02-01 21:40:29] User Query
**Input:** `Tiramisu has what Ingredient`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (p:Product {name: "Tiramisu"})-[:PART_OF]->(i:Ingredient) RETURN i.ingredient_name LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 1

## [2026-02-01 21:41:03] User Query
**Input:** `how many ingredient does Tiramisu have`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (i:Ingredient)-[:PART_OF]->(p:Product {name: "Tiramisu"}) RETURN count(i) LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 1

## [2026-02-01 21:42:24] User Query
**Input:** `Ingredient name in the graph is called "name" and not "ingredient_name". What is the name of ingredient in "Tiramisu"`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (p:Product)-[:PART_OF]->(i:Ingredient) WHERE p.name = "Tiramisu" RETURN i.name LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 1

## [2026-02-01 21:42:47] User Query
**Input:** `what is the name of the ingredient in Coffee`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (p:Product)-[:PART_OF]->(i:Ingredient) WHERE p.name = "Coffee" RETURN i.ingredient_name LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 0

## [2026-02-01 21:43:14] User Query
**Input:** `what is the name of the ingredient in Coffee. ingredient name is called "name"`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (p:Product)-[:PART_OF]->(i:Ingredient) WHERE p.name = "Coffee" RETURN i.name LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 0

## [2026-02-01 21:43:40] User Query
**Input:** `MATCH (p:Product)-[:PART_OF]->(i:Ingredient) WHERE p.name = "Tiramisu" RETURN i.name LIMIT 20`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (p:Product)-[:PART_OF]->(i:Ingredient) WHERE p.name = "Tiramisu" RETURN i.ingredient_name LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 1

## [2026-02-01 21:44:09] User Query
**Input:** `MATCH (p:Product)-[:PART_OF]->(i:Ingredient) WHERE p.name = "Tiramisu" RETURN i.name. Run this query as is.`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (p:Product)-[:PART_OF]->(i:Ingredient) WHERE p.name = "Tiramisu" RETURN i.name LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 1

## [2026-02-01 21:44:46] User Query
**Input:** `MATCH (p:Product)-[:PART_OF]->(i:Ingredient) WHERE p.name = "Tiramisu" RETURN i.name. Run this query as is chato Coffee`
**Model Used:** `gemini-2.0-flash`

**Generated Cypher:**
```cypher
MATCH (p:Product)-[:PART_OF]->(i:Ingredient) WHERE p.name = "Tiramisu" RETURN i.name LIMIT 20
```
**Results Count:** N/A
**Sample Result:** `Pending Execution`

---
-> Execution Result: 1

