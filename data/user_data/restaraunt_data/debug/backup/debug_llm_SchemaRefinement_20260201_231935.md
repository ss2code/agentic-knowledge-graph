# LLM Debug Log: SchemaRefinement


## 2026-02-01 23:14:57 | Function: `propose_schema`

**Model**: `gemini-3-pro-preview`

### Prompt
```text

        You are a Neo4j Graph Architect. 
        User Intent: "Root Cause Analysis of Customer Complaints Related to Products and Categories" - Identify the root causes of customer complaints related to specific ingredients, products, and product categories by analyzing customer reviews, sentiments, and experiences, and connecting them to product information.
        Primary Entities: ['CustomerComplaint', 'Ingredient', 'Product', 'ProductCategory', 'CustomerReview', 'Sentiment', 'CustomerExperience']
        
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
    "transformation": "Split column 'ingredients' by delimiter ',' to create individual Ingredient nodes."
  },
  "CustomerReview": {
    "construction_type": "node",
    "source_file": "reviews.txt",
    "label": "CustomerReview",
    "unique_column_name": "generated_uuid",
    "properties": [
      "review_text"
    ],
    "transformation": "Treat each row/line as a distinct review body. Generate a unique UUID for each row."
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
    "rule": "Iterate through the split array of ingredients and create a relationship for each distinct ingredient found."
  },
  "ABOUT_PRODUCT": {
    "construction_type": "relationship",
    "source_file": "reviews.txt",
    "relationship_type": "ABOUT_PRODUCT",
    "from_node_label": "CustomerReview",
    "from_node_column": "review_text",
    "to_node_label": "Product",
    "to_node_column": "name",
    "rule": "Use NLP (Named Entity Recognition) to extract Product Names from 'review_text' and fuzzy match against Product.name."
  },
  "MENTIONS_INGREDIENT": {
    "construction_type": "relationship",
    "source_file": "reviews.txt",
    "relationship_type": "MENTIONS_INGREDIENT",
    "from_node_label": "CustomerReview",
    "from_node_column": "review_text",
    "to_node_label": "Ingredient",
    "to_node_column": "name",
    "rule": "Use NLP to extract Ingredient terms from 'review_text' and match against Ingredient.name to identify root causes (e.g., 'soggy lettuce')."
  },
  "HAS_SENTIMENT": {
    "construction_type": "node_property_extraction",
    "source_file": "reviews.txt",
    "target_node_label": "CustomerReview",
    "target_property": "sentiment_score",
    "rule": "Apply Sentiment Analysis on 'review_text' to store a polarity score (-1.0 to 1.0) on the CustomerReview node to quantify the complaint severity."
  },
  "reasoning": "The schema bridges structured product data with unstructured review text. 'Product' and 'ProductCategory' form the backbone hierarchy. 'Ingredient' nodes are extracted via list splitting from the CSV to allow granular root cause tracking (e.g., if multiple pizzas with 'Cheese' get bad reviews). The 'CustomerReview' nodes act as the entry point for analysis. NLP-driven relationships ('ABOUT_PRODUCT', 'MENTIONS_INGREDIENT') are defined to link the unstructured complaints dynamically to the specific graph entities they reference."
}
```

---

## 2026-02-01 23:15:23 | Function: `critique_schema`

**Model**: `gemini-3-pro-preview`

### Prompt
```text

        You are a strict Graph Schema Reviewer.
        
        CONTEXT:
        1. User Intent: "Root Cause Analysis of Customer Complaints Related to Products and Categories"
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
    "transformation": "Split column 'ingredients' by delimiter ',' to create individual Ingredient nodes."
  },
  "CustomerReview": {
    "construction_type": "node",
    "source_file": "reviews.txt",
    "label": "CustomerReview",
    "unique_column_name": "generated_uuid",
    "properties": [
      "review_text"
    ],
    "transformation": "Treat each row/line as a distinct review body. Generate a unique UUID for each row."
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
    "rule": "Iterate through the split array of ingredients and create a relationship for each distinct ingredient found."
  },
  "ABOUT_PRODUCT": {
    "construction_type": "relationship",
    "source_file": "reviews.txt",
    "relationship_type": "ABOUT_PRODUCT",
    "from_node_label": "CustomerReview",
    "from_node_column": "review_text",
    "to_node_label": "Product",
    "to_node_column": "name",
    "rule": "Use NLP (Named Entity Recognition) to extract Product Names from 'review_text' and fuzzy match against Product.name."
  },
  "MENTIONS_INGREDIENT": {
    "construction_type": "relationship",
    "source_file": "reviews.txt",
    "relationship_type": "MENTIONS_INGREDIENT",
    "from_node_label": "CustomerReview",
    "from_node_column": "review_text",
    "to_node_label": "Ingredient",
    "to_node_column": "name",
    "rule": "Use NLP to extract Ingredient terms from 'review_text' and match against Ingredient.name to identify root causes (e.g., 'soggy lettuce')."
  },
  "HAS_SENTIMENT": {
    "construction_type": "node_property_extraction",
    "source_file": "reviews.txt",
    "target_node_label": "CustomerReview",
    "target_property": "sentiment_score",
    "rule": "Apply Sentiment Analysis on 'review_text' to store a polarity score (-1.0 to 1.0) on the CustomerReview node to quantify the complaint severity."
  },
  "reasoning": "The schema bridges structured product data with unstructured review text. 'Product' and 'ProductCategory' form the backbone hierarchy. 'Ingredient' nodes are extracted via list splitting from the CSV to allow granular root cause tracking (e.g., if multiple pizzas with 'Cheese' get bad reviews). The 'CustomerReview' nodes act as the entry point for analysis. NLP-driven relationships ('ABOUT_PRODUCT', 'MENTIONS_INGREDIENT') are defined to link the unstructured complaints dynamically to the specific graph entities they reference."
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
```json
{
  "status": "RETRY",
  "feedback": "The schema contains a construction_type 'node_property_extraction' for the entry 'HAS_SENTIMENT'. According to Verification Checklist item #3, all construction types must strictly be 'node' or 'relationship'. Please incorporate the 'sentiment_score' property and its calculation rule directly into the 'CustomerReview' node definition."
}
```
```

---

## 2026-02-01 23:16:06 | Function: `propose_schema`

**Model**: `gemini-3-pro-preview`

### Prompt
```text

        You are a Neo4j Graph Architect. 
        User Intent: "Root Cause Analysis of Customer Complaints Related to Products and Categories" - Identify the root causes of customer complaints related to specific ingredients, products, and product categories by analyzing customer reviews, sentiments, and experiences, and connecting them to product information.
        Primary Entities: ['CustomerComplaint', 'Ingredient', 'Product', 'ProductCategory', 'CustomerReview', 'Sentiment', 'CustomerExperience']
        
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
        
        PREVIOUS FEEDBACK TO ADDRESS: The schema contains a construction_type 'node_property_extraction' for the entry 'HAS_SENTIMENT'. According to Verification Checklist item #3, all construction types must strictly be 'node' or 'relationship'. Please incorporate the 'sentiment_score' property and its calculation rule directly into the 'CustomerReview' node definition.
        
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
    "rule": "Split the 'ingredients' column by comma separator, trim whitespace, and create a unique node for each distinct ingredient."
  },
  "CustomerReview": {
    "construction_type": "node",
    "source_file": "reviews.txt",
    "label": "CustomerReview",
    "unique_column_name": "review_id",
    "properties": [
      "review_id",
      "body",
      "sentiment_score"
    ],
    "rule": "Generate a unique hash/UUID for 'review_id'. Store the full text row as 'body'. Calculate 'sentiment_score' (float -1.0 to 1.0) using NLP and store it directly as a property."
  },
  "Sentiment": {
    "construction_type": "node",
    "source_file": "reviews.txt",
    "label": "Sentiment",
    "unique_column_name": "sentiment_label",
    "properties": [
      "label"
    ],
    "rule": "Derive categorical sentiment (Positive, Neutral, Negative) from the review text using NLP."
  },
  "CustomerExperience": {
    "construction_type": "node",
    "source_file": "reviews.txt",
    "label": "CustomerExperience",
    "unique_column_name": "experience_phrase",
    "properties": [
      "phrase",
      "complaint_type"
    ],
    "rule": "Extract key phrases describing the root cause or experience (e.g., 'soggy lettuce', 'slow service') using NLP keyword extraction."
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
    "rule": "Iterate through the split values of the 'ingredients' column to link the Product to each specific Ingredient node."
  },
  "MENTIONS_PRODUCT": {
    "construction_type": "relationship",
    "source_file": "reviews.txt",
    "relationship_type": "MENTIONS_PRODUCT",
    "from_node_label": "CustomerReview",
    "from_node_column": "review_id",
    "to_node_label": "Product",
    "to_node_column": "name",
    "rule": "Use NLP Named Entity Recognition (NER) to find Product names in review text and link to the Product node."
  },
  "HAS_SENTIMENT": {
    "construction_type": "relationship",
    "source_file": "reviews.txt",
    "relationship_type": "HAS_SENTIMENT",
    "from_node_label": "CustomerReview",
    "from_node_column": "review_id",
    "to_node_label": "Sentiment",
    "to_node_column": "sentiment_label",
    "rule": "Link the review to the derived categorical Sentiment node."
  },
  "REPORTED_EXPERIENCE": {
    "construction_type": "relationship",
    "source_file": "reviews.txt",
    "relationship_type": "REPORTED_EXPERIENCE",
    "from_node_label": "CustomerReview",
    "from_node_column": "review_id",
    "to_node_label": "CustomerExperience",
    "to_node_column": "experience_phrase",
    "rule": "Link the review to the extracted experience/complaint phrase."
  },
  "RELATED_TO_INGREDIENT": {
    "construction_type": "relationship",
    "source_file": "reviews.txt",
    "relationship_type": "RELATED_TO_INGREDIENT",
    "from_node_label": "CustomerExperience",
    "from_node_column": "experience_phrase",
    "to_node_label": "Ingredient",
    "to_node_column": "name",
    "rule": "Use NLP dependency parsing to link specific complaints (e.g., 'soggy') to the ingredient mentioned in the context (e.g., 'Lettuce')."
  },
  "reasoning": "The schema normalizes product data by splitting 'ingredients' into distinct nodes to allow for granular root cause analysis (e.g., identifying if 'Cheese' is a recurring issue across multiple pizzas). The 'CustomerReview' node directly captures the 'sentiment_score' property as requested, while a separate 'Sentiment' node allows for categorical grouping (Positive/Negative). NLP-driven relationships connect unstructured reviews to structured product and ingredient data to fulfill the RCA intent."
}
```
```

---

## 2026-02-01 23:16:26 | Function: `critique_schema`

**Model**: `gemini-3-pro-preview`

### Prompt
```text

        You are a strict Graph Schema Reviewer.
        
        CONTEXT:
        1. User Intent: "Root Cause Analysis of Customer Complaints Related to Products and Categories"
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
    "rule": "Split the 'ingredients' column by comma separator, trim whitespace, and create a unique node for each distinct ingredient."
  },
  "CustomerReview": {
    "construction_type": "node",
    "source_file": "reviews.txt",
    "label": "CustomerReview",
    "unique_column_name": "review_id",
    "properties": [
      "review_id",
      "body",
      "sentiment_score"
    ],
    "rule": "Generate a unique hash/UUID for 'review_id'. Store the full text row as 'body'. Calculate 'sentiment_score' (float -1.0 to 1.0) using NLP and store it directly as a property."
  },
  "Sentiment": {
    "construction_type": "node",
    "source_file": "reviews.txt",
    "label": "Sentiment",
    "unique_column_name": "sentiment_label",
    "properties": [
      "label"
    ],
    "rule": "Derive categorical sentiment (Positive, Neutral, Negative) from the review text using NLP."
  },
  "CustomerExperience": {
    "construction_type": "node",
    "source_file": "reviews.txt",
    "label": "CustomerExperience",
    "unique_column_name": "experience_phrase",
    "properties": [
      "phrase",
      "complaint_type"
    ],
    "rule": "Extract key phrases describing the root cause or experience (e.g., 'soggy lettuce', 'slow service') using NLP keyword extraction."
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
    "rule": "Iterate through the split values of the 'ingredients' column to link the Product to each specific Ingredient node."
  },
  "MENTIONS_PRODUCT": {
    "construction_type": "relationship",
    "source_file": "reviews.txt",
    "relationship_type": "MENTIONS_PRODUCT",
    "from_node_label": "CustomerReview",
    "from_node_column": "review_id",
    "to_node_label": "Product",
    "to_node_column": "name",
    "rule": "Use NLP Named Entity Recognition (NER) to find Product names in review text and link to the Product node."
  },
  "HAS_SENTIMENT": {
    "construction_type": "relationship",
    "source_file": "reviews.txt",
    "relationship_type": "HAS_SENTIMENT",
    "from_node_label": "CustomerReview",
    "from_node_column": "review_id",
    "to_node_label": "Sentiment",
    "to_node_column": "sentiment_label",
    "rule": "Link the review to the derived categorical Sentiment node."
  },
  "REPORTED_EXPERIENCE": {
    "construction_type": "relationship",
    "source_file": "reviews.txt",
    "relationship_type": "REPORTED_EXPERIENCE",
    "from_node_label": "CustomerReview",
    "from_node_column": "review_id",
    "to_node_label": "CustomerExperience",
    "to_node_column": "experience_phrase",
    "rule": "Link the review to the extracted experience/complaint phrase."
  },
  "RELATED_TO_INGREDIENT": {
    "construction_type": "relationship",
    "source_file": "reviews.txt",
    "relationship_type": "RELATED_TO_INGREDIENT",
    "from_node_label": "CustomerExperience",
    "from_node_column": "experience_phrase",
    "to_node_label": "Ingredient",
    "to_node_column": "name",
    "rule": "Use NLP dependency parsing to link specific complaints (e.g., 'soggy') to the ingredient mentioned in the context (e.g., 'Lettuce')."
  },
  "reasoning": "The schema normalizes product data by splitting 'ingredients' into distinct nodes to allow for granular root cause analysis (e.g., identifying if 'Cheese' is a recurring issue across multiple pizzas). The 'CustomerReview' node directly captures the 'sentiment_score' property as requested, while a separate 'Sentiment' node allows for categorical grouping (Positive/Negative). NLP-driven relationships connect unstructured reviews to structured product and ingredient data to fulfill the RCA intent."
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
```json
{
  "status": "VALID",
  "feedback": "Looks good"
}
```
```

---
