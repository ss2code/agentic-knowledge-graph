from services.graph_service import graphdb

def setup_golden_data():
    """
    Populates the DB with the Golden Dataset (Restaurant Complaints).
    """
    print("Initializing Golden Data...")
    graphdb.connect()
    graphdb.nuke_database()
    
    cypher = """
    CREATE (p1:Product {name: 'Tomato Soup', type: 'Soup'})
    CREATE (p2:Product {name: 'Caesar Salad', type: 'Salad'})
    
    CREATE (i1:Ingredient {name: 'tomato'})
    CREATE (i2:Ingredient {name: 'salt'})
    CREATE (i3:Ingredient {name: 'lettuce'})
    
    CREATE (p1)-[:CONTAINS]->(i1)
    CREATE (p1)-[:CONTAINS]->(i2)
    CREATE (p2)-[:CONTAINS]->(i3)
    
    CREATE (c1:Complaint {description: 'Too salty', date: '2023-01-01', category: 'Food Quality'})
    CREATE (c2:Complaint {description: 'Found a fly', date: '2023-01-02', category: 'Food Quality'})
    CREATE (c3:Complaint {description: 'Cold soup', date: '2023-01-03', category: 'Food Quality'})
    CREATE (c4:Complaint {description: 'Rude server', date: '2023-01-04', category: 'Service'})
    
    CREATE (c1)-[:ABOUT]->(p1)
    CREATE (c2)-[:ABOUT]->(p2)
    CREATE (c3)-[:ABOUT]->(p1)
    """
    
    graphdb.send_query(cypher)
    print("Golden Data Created.")

if __name__ == "__main__":
    setup_golden_data()
