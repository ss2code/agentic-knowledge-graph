import pandas as pd
import random
import os

os.makedirs('data', exist_ok=True)

# 1. Generate Structured Data (The "Skeleton")
products_list = [
    {"id": "P1", "name": "Margherita Pizza", "category": "Main", "ingredients": "Flour, Tomato, Cheese, Basil"},
    {"id": "P2", "name": "Pepperoni Pizza", "category": "Main", "ingredients": "Flour, Tomato, Cheese, Pepperoni"},
    {"id": "P3", "name": "House Salad", "category": "Starter", "ingredients": "Lettuce, Tomato, Cucumber, Olive Oil"},
    {"id": "P4", "name": "Tiramisu", "category": "Dessert", "ingredients": "Ladyfingers, Coffee, Mascarpone, Cocoa"},
    {"id": "P5", "name": "Chianti Classico", "category": "Drink", "ingredients": "Sangiovese Grapes"},
    {"id": "P6", "name": "Chardonnay", "category": "Drink", "ingredients": "Chardonnay Grapes"},
    {"id": "P7", "name": "Spaghetti Carbonara", "category": "Main", "ingredients": "Pasta, Eggs, Cheese, Guanciale"},
    {"id": "P8", "name": "Bruschetta", "category": "Starter", "ingredients": "Bread, Tomato, Garlic, Basil"},
    {"id": "P9", "name": "Gelato", "category": "Dessert", "ingredients": "Milk, Sugar, Vanilla"},
    {"id": "P10", "name": "Espresso", "category": "Drink", "ingredients": "Coffee Beans"}
]
pd.DataFrame(products_list).to_csv('data/products.csv', index=False)

# 2. Generate Unstructured Data (The "Flesh")
# We simulate specific supply chain issues (e.g., "Rotten Tomato") affecting multiple products
issues = ["soggy", "rotten", "bland", "too salty", "cold", "undercooked", "sour", "stale"]
sentiments = ["disappointed", "terrible", "awful", "sad", "angry"]

reviews = []
for _ in range(50):
    prod = random.choice(products_list)
    # 30% chance of a specific ingredient failure
    if random.random() < 0.3:
        ing = random.choice(prod["ingredients"].split(", ")).strip()
        issue = random.choice(issues)
        review = f"I ordered the {prod['name']}. The {ing} was {issue}. {random.choice(sentiments)} experience."
    else:
        review = f"The {prod['name']} was okay, but service was slow."
    reviews.append(review)

with open('data/reviews.txt', 'w') as f:
    f.write("\n".join(reviews))

print("Data generation complete.")
