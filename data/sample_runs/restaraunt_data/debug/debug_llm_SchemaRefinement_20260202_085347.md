# LLM Debug Log: SchemaRefinement


## 2026-02-02 08:54:17 | Function: `propose_schema`

**Model**: `gemini-3-pro-preview`

### Prompt
```text

        You are a Neo4j Graph Architect. 
        User Intent: "Root Cause Analysis of Customer Complaints in Restaurants" - Identify the underlying causes of customer complaints by connecting customer reviews, sentiments, experiences, specific ingredients, and product categories within a restaurant's offerings to improve overall customer satisfaction.
        Primary Entities: ['CustomerReview', 'Sentiment', 'CustomerExperience', 'Ingredient', 'ProductCategory']
        
        Data Files available:
        {
  "products.csv": {
    "header": "id,name,category,ingredients",
    "sample_row": "P1,Margherita Pizza,Main,\"Flour, Tomato, Cheese, Basil\""
  },
  "reviews.txt": {
    "header": "The Chianti Classico was okay, but service was slow.",
    "sample_row": "I ordered the House Salad. The Lettuce was soggy. disappointed experience."
  }
}
        
        TASK: Create a Schema / Construction Plan.
        - Map files to Node Labels.
        - Map columns to Properties.
        - Define Relationships between nodes.
        - Important: If a column contains multiple values (e.g. "Flour, Sugar"), suggest a transformation to split it.
        
        CONSTRAINTS:
        1. Output ONLY valid JSON. No conversational text or markdown text outside the code block.
        2. Node Labels MUST be strict PascalCase with NO spaces (e.g., "ProductCategory", not "Product Category").
        3. Relationship Types MUST be SCREAMING_SNAKE_CASE (e.g., "BELONGS_TO").
        
        
        
        OUTPUT JSON format (Dictionary of Rules):
        {
          "Product": {
            "construction_type": "node",
            "source_file": "products.csv",
            "label": "Product",
            "unique_column_name": "id",
            "properties": ["id", "name", "price"]
          },
          "ABOUT_PRODUCT": {
            "construction_type": "relationship",
            "source_file": "products.csv",
            "relationship_type": "ABOUT_PRODUCT",
            "from_node_label": "CustomerReview",
            "from_node_column": "extracted_product_name",
            "to_node_label": "Product",
            "to_node_column": "name",
            "rule": "Use NLP to extract product names from Review text, then match against Product.name"
          },
          "reasoning": "Explanation of design choices"
        }
        }
        
```

### Response
```text
```json
{
  "Product": {
    "construction_type": "node",
    "source_file": "products.csv",
    "label": "Product",
    "unique_column_name": "id",
    "properties": [
      "id",
      "name"
    ]
  },
  "ProductCategory": {
    "construction_type": "node",
    "source_file": "products.csv",
    "label": "ProductCategory",
    "unique_column_name": "category",
    "properties": [
      "category"
    ]
  },
  "Ingredient": {
    "construction_type": "node",
    "source_file": "products.csv",
    "label": "Ingredient",
    "unique_column_name": "ingredients",
    "properties": [
      "name"
    ],
    "transformation": "Split column 'ingredients' by comma delimiter (',') and trim whitespace to create distinct nodes."
  },
  "CustomerReview": {
    "construction_type": "node",
    "source_file": "reviews.txt",
    "label": "CustomerReview",
    "unique_column_name": "hash_id",
    "properties": [
      "review_text"
    ],
    "rule": "Generate a unique hash (MD5/SHA) of the raw text line to serve as the ID."
  },
  "Sentiment": {
    "construction_type": "node",
    "source_file": "reviews.txt",
    "label": "Sentiment",
    "unique_column_name": "derived_sentiment",
    "properties": [
      "type"
    ],
    "rule": "Use NLP Sentiment Analysis on review text to classify as 'Positive', 'Negative', or 'Neutral'."
  },
  "CustomerExperience": {
    "construction_type": "node",
    "source_file": "reviews.txt",
    "label": "CustomerExperience",
    "unique_column_name": "extracted_aspect",
    "properties": [
      "aspect"
    ],
    "rule": "Use NLP Aspect Extraction to identify specific descriptors (e.g., 'soggy', 'slow', 'cold') referenced in the text."
  },
  "BELONGS_TO": {
    "construction_type": "relationship",
    "source_file": "products.csv",
    "relationship_type": "BELONGS_TO",
    "from_node_label": "Product",
    "from_node_column": "id",
    "to_node_label": "ProductCategory",
    "to_node_column": "category"
  },
  "CONTAINS_INGREDIENT": {
    "construction_type": "relationship",
    "source_file": "products.csv",
    "relationship_type": "CONTAINS_INGREDIENT",
    "from_node_label": "Product",
    "from_node_column": "id",
    "to_node_label": "Ingredient",
    "to_node_column": "ingredients",
    "rule": "Create a relationship for every split value found in the ingredients column."
  },
  "DISCUSSES_PRODUCT": {
    "construction_type": "relationship",
    "source_file": "reviews.txt",
    "relationship_type": "DISCUSSES_PRODUCT",
    "from_node_label": "CustomerReview",
    "from_node_column": "review_text",
    "to_node_label": "Product",
    "to_node_column": "name",
    "rule": "Use Named Entity Recognition (NER) or fuzzy string matching to find Product.name within CustomerReview.review_text."
  },
  "HAS_SENTIMENT": {
    "construction_type": "relationship",
    "source_file": "reviews.txt",
    "relationship_type": "HAS_SENTIMENT",
    "from_node_label": "CustomerReview",
    "from_node_column": "hash_id",
    "to_node_label": "Sentiment",
    "to_node_column": "derived_sentiment"
  },
  "REFLECTS_EXPERIENCE": {
    "construction_type": "relationship",
    "source_file": "reviews.txt",
    "relationship_type": "REFLECTS_EXPERIENCE",
    "from_node_label": "CustomerReview",
    "from_node_column": "hash_id",
    "to_node_label": "CustomerExperience",
    "to_node_column": "extracted_aspect"
  },
  "MENTIONS_INGREDIENT": {
    "construction_type": "relationship",
    "source_file": "reviews.txt",
    "relationship_type": "MENTIONS_INGREDIENT",
    "from_node_label": "CustomerReview",
    "from_node_column": "review_text",
    "to_node_label": "Ingredient",
    "to_node_column": "name",
    "rule": "Scan review text for keywords matching Ingredient.name. This helps isolate if a complaint is about a specific component (e.g., 'Lettuce') rather than the whole product."
  },
  "reasoning": "This schema creates a 'Product Knowledge Graph' using the structured CSV data (Products, Categories, Ingredients) and links it to unstructured 'Voice of Customer' data. By splitting ingredients, we allow for granular Root Cause Analysis (e.g., identifying if 'Tomato' causes bad reviews across multiple different Pizza types). NLP extraction is required for the reviews to bridge the gap between unstructured text and structured graph entities."
}
```
```

---

## 2026-02-02 08:54:41 | Function: `critique_schema`

**Model**: `gemini-3-pro-preview`

### Prompt
```text

        You are a strict Graph Schema Reviewer.
        
        CONTEXT:
        1. User Intent: "Root Cause Analysis of Customer Complaints in Restaurants"
        2. Data Files available (Header & Sample):
        {
  "products.csv": {
    "header": "id,name,category,ingredients",
    "sample_row": "P1,Margherita Pizza,Main,\"Flour, Tomato, Cheese, Basil\""
  },
  "reviews.txt": {
    "header": "The Chianti Classico was okay, but service was slow.",
    "sample_row": "I ordered the House Salad. The Lettuce was soggy. disappointed experience."
  }
}
        
        Proposed Schema:
        {
  "Product": {
    "construction_type": "node",
    "source_file": "products.csv",
    "label": "Product",
    "unique_column_name": "id",
    "properties": [
      "id",
      "name"
    ]
  },
  "ProductCategory": {
    "construction_type": "node",
    "source_file": "products.csv",
    "label": "ProductCategory",
    "unique_column_name": "category",
    "properties": [
      "category"
    ]
  },
  "Ingredient": {
    "construction_type": "node",
    "source_file": "products.csv",
    "label": "Ingredient",
    "unique_column_name": "ingredients",
    "properties": [
      "name"
    ],
    "transformation": "Split column 'ingredients' by comma delimiter (',') and trim whitespace to create distinct nodes."
  },
  "CustomerReview": {
    "construction_type": "node",
    "source_file": "reviews.txt",
    "label": "CustomerReview",
    "unique_column_name": "hash_id",
    "properties": [
      "review_text"
    ],
    "rule": "Generate a unique hash (MD5/SHA) of the raw text line to serve as the ID."
  },
  "Sentiment": {
    "construction_type": "node",
    "source_file": "reviews.txt",
    "label": "Sentiment",
    "unique_column_name": "derived_sentiment",
    "properties": [
      "type"
    ],
    "rule": "Use NLP Sentiment Analysis on review text to classify as 'Positive', 'Negative', or 'Neutral'."
  },
  "CustomerExperience": {
    "construction_type": "node",
    "source_file": "reviews.txt",
    "label": "CustomerExperience",
    "unique_column_name": "extracted_aspect",
    "properties": [
      "aspect"
    ],
    "rule": "Use NLP Aspect Extraction to identify specific descriptors (e.g., 'soggy', 'slow', 'cold') referenced in the text."
  },
  "BELONGS_TO": {
    "construction_type": "relationship",
    "source_file": "products.csv",
    "relationship_type": "BELONGS_TO",
    "from_node_label": "Product",
    "from_node_column": "id",
    "to_node_label": "ProductCategory",
    "to_node_column": "category"
  },
  "CONTAINS_INGREDIENT": {
    "construction_type": "relationship",
    "source_file": "products.csv",
    "relationship_type": "CONTAINS_INGREDIENT",
    "from_node_label": "Product",
    "from_node_column": "id",
    "to_node_label": "Ingredient",
    "to_node_column": "ingredients",
    "rule": "Create a relationship for every split value found in the ingredients column."
  },
  "DISCUSSES_PRODUCT": {
    "construction_type": "relationship",
    "source_file": "reviews.txt",
    "relationship_type": "DISCUSSES_PRODUCT",
    "from_node_label": "CustomerReview",
    "from_node_column": "review_text",
    "to_node_label": "Product",
    "to_node_column": "name",
    "rule": "Use Named Entity Recognition (NER) or fuzzy string matching to find Product.name within CustomerReview.review_text."
  },
  "HAS_SENTIMENT": {
    "construction_type": "relationship",
    "source_file": "reviews.txt",
    "relationship_type": "HAS_SENTIMENT",
    "from_node_label": "CustomerReview",
    "from_node_column": "hash_id",
    "to_node_label": "Sentiment",
    "to_node_column": "derived_sentiment"
  },
  "REFLECTS_EXPERIENCE": {
    "construction_type": "relationship",
    "source_file": "reviews.txt",
    "relationship_type": "REFLECTS_EXPERIENCE",
    "from_node_label": "CustomerReview",
    "from_node_column": "hash_id",
    "to_node_label": "CustomerExperience",
    "to_node_column": "extracted_aspect"
  },
  "MENTIONS_INGREDIENT": {
    "construction_type": "relationship",
    "source_file": "reviews.txt",
    "relationship_type": "MENTIONS_INGREDIENT",
    "from_node_label": "CustomerReview",
    "from_node_column": "review_text",
    "to_node_label": "Ingredient",
    "to_node_column": "name",
    "rule": "Scan review text for keywords matching Ingredient.name. This helps isolate if a complaint is about a specific component (e.g., 'Lettuce') rather than the whole product."
  },
  "reasoning": "This schema creates a 'Product Knowledge Graph' using the structured CSV data (Products, Categories, Ingredients) and links it to unstructured 'Voice of Customer' data. By splitting ingredients, we allow for granular Root Cause Analysis (e.g., identifying if 'Tomato' causes bad reviews across multiple different Pizza types). NLP extraction is required for the reviews to bridge the gap between unstructured text and structured graph entities."
}
        
        KNOWLEDGE GRAPH BEST PRACTICES CHECKLIST:
        1. **Standardization**: Are Node Labels PascalCase (e.g., 'Product') and Relationships SCREAMING_SNAKE_CASE (e.g., 'HAS_INGREDIENT')?
        2. **Atomicity**: logical check - if a sample row has "A, B, C", is there a rule to split it?
        3. **Consistency**: Do the mapped properties match the actual file headers provided above?
        4. **Simplicity**: No redundant nodes.
        
        VERIFY:
        1. Does specific `unique_column_name` exist in the file header? (skip for unstructured .txt)
        2. Are relationship mappings accurate? 
           - **EXCEPTION**: If the rule involves "NLP", "LLM", or "Extraction", you MUST allow the `from_node_column` or `to_node_column` to be a "derived" field (like 'extracted_product_name') even if it's not in the file header.
        3. Are all construction types 'node' or 'relationship'?
        4. **CRITICAL**: Do any labels contain spaces? If so, REJECT immediately.
        
        OUTPUT JSON:
        {
           "status": "VALID" or "RETRY",
           "feedback": "If RETRY, explain strictly what is wrong using the checklist. If VALID, say 'Looks good'."
        }
        }
        
```

### Response
```text
{
  "status": "VALID",
  "feedback": "Looks good"
}
```

---
