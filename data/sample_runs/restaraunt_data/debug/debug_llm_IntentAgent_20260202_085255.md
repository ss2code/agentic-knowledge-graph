# LLM Debug Log: IntentAgent


## 2026-02-02 08:53:07 | Function: `refine_intent`

**Model**: `gemini-2.0-flash`

### Prompt
```text

        You are an expert Data Architect.
        Your goal is to extract a clear, actionable business goal for a Knowledge Graph from the user's input,
        WITHOUT assuming any specific domain (e.g., it could be Finance, Biology, Supply Chain, etc.).
        
        Rules:
        1. REJECT vague goals like "analyze data" or "find insights". Ask for specifics.
        2. ACCEPT specific goals where the user mentions connecting concepts (e.g., "Trace X to Y").
        3. OUTPUT FORMAT:
           - If REJECTING: Plain text critique.
           - If ACCEPTING: A JSON object (and ONLY JSON) with:
             {
               "intent": "Short Title",
               "description": "One sentence summary",
               "primary_entities": ["List", "Of", "Node", "Labels"],
               "reasoning": "Why this is a good graph use case"
             }
        
User Input: This is for a restaurant. I want to be able to identify root causes of customer complaints. These might be due to ingredients. I want to be able to identify key matrix around product ideas and product categories where the customer sentiment is good or bad.  Make sure you also include product categories for analysis and include in facts. I want to capture positive and negative reviews, sentiments and also experience. Make sure you include these keywords in the intent so that the correct nodes and relationships are created downstream.
```

### Response
```text
```json
{
  "intent": "Root Cause Analysis of Customer Complaints in Restaurants",
  "description": "Identify the underlying causes of customer complaints by connecting customer reviews, sentiments, experiences, specific ingredients, and product categories within a restaurant's offerings to improve overall customer satisfaction.",
  "primary_entities": ["CustomerReview", "Sentiment", "CustomerExperience", "Ingredient", "ProductCategory"],
  "reasoning": "This is a good graph use case because it involves connecting disparate data points (complaints, sentiments, ingredients, product categories) to identify causal relationships, which is a core strength of knowledge graphs. The goal is specific and actionable."
}
```

```

---
