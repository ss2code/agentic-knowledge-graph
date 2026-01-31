import json
import os
import webbrowser
from services.graph_service import graphdb, CYAN, GREEN, YELLOW, RED, RESET

class VisualizerAgent:
    def __init__(self, context=None):
        self.context = context
        # Use context output dir if available, else default to 'data'
        self.output_dir = context.output_dir if context else 'data'
        self.output_file = os.path.join(self.output_dir, 'schema_viz.html')

    def run(self):
        print(f"\n{CYAN}--- 📊 Generating Rich Schema Visualization ---{RESET}")
        
        if not graphdb.connect():
             print(f"{RED}Failed to connect to Neo4j.{RESET}")
             return

        # 1. Fetch Schema Data
        print(f"{YELLOW}>> Querying Graph Meta-Data...{RESET}")
        
        # A. Node Counts
        node_query = "MATCH (n) RETURN labels(n)[0] as label, count(n) as count"
        node_res = graphdb.send_query(node_query)
        nodes_counts = {r['label']: r['count'] for r in node_res} if node_res else {}
        
        # B. Relationship Counts
        rel_query = "MATCH (a)-[r]->(b) RETURN labels(a)[0] as source, type(r) as type, labels(b)[0] as target, count(r) as count"
        rel_res = graphdb.send_query(rel_query)
        rels_data = rel_res if rel_res else []
        
        # C. Property Schema (Drill-down info)
        prop_query = """
        CALL db.schema.nodeTypeProperties() 
        YIELD nodeType, propertyName, propertyTypes 
        RETURN nodeType, propertyName, propertyTypes
        """
        try:
            prop_res = graphdb.send_query(prop_query)
        except:
            prop_res = [] # Fallback if apoc/db procedure fails
            
        # Organize Properties by Label
        node_props = {}
        for row in prop_res:
            label = row['nodeType'].replace(":", "").replace("`", "") # Clean ":Label"
            if label not in node_props: node_props[label] = []
            
            prop_str = f"{row['propertyName']} ({row['propertyTypes'][0] if row['propertyTypes'] else 'Any'})"
            if prop_str not in node_props[label]:
                node_props[label].append(prop_str)
            
        # D. Hubs (Most connected nodes)
        print(f"{YELLOW}>> Identifying Hubs...{RESET}")
        hubs = {}
        for label in nodes_counts.keys():
            hub_query = f"""
            MATCH (n:`{label}`)-[r]-()
            WITH n, count(r) as degree
            ORDER BY degree DESC LIMIT 1
            RETURN n, degree
            """
            res = graphdb.send_query(hub_query)
            if res:
                props = res[0]['n']
                # Try to find a readable name
                name = props.get('name', props.get('id', props.get('title', str(props).strip("{}"))))
                hubs[label] = {"name": name, "degree": res[0]['degree']}
            
        # E. Sample Data (5 random nodes per label)
        print(f"{YELLOW}>> Fetching Sample Data...{RESET}")
        samples = {}
        for label in nodes_counts.keys():
            sample_query = f"MATCH (n:`{label}`) RETURN n LIMIT 5"
            res = graphdb.send_query(sample_query)
            if res:
                samples[label] = [r['n'] for r in res]
            
        # F. Anomalies
        anomalies = []
        if not nodes_counts: anomalies.append("Graph is empty.")
        
        connected_labels = set()
        for r in rels_data:
            connected_labels.add(r['source'])
            connected_labels.add(r['target'])
            
        for label in nodes_counts:
            if label not in connected_labels and label != '__Entity__':
                 anomalies.append(f"Disconnected Node Type: {label}")

        # 2. Build HTML
        html_content = self._generate_html(nodes_counts, rels_data, node_props, hubs, samples, anomalies)
        
        # 3. Save
        # Ensure directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        with open(self.output_file, 'w') as f:
            f.write(html_content)
            
        print(f"{GREEN}Visualization saved to: {self.output_file}{RESET}")
        try:
            abs_path = "file://" + os.path.abspath(self.output_file)
            print(f"Opening {abs_path}...")
            # Automatically opening might be annoying in some envs, but user asked for better viz.
            # webbrowser.open(abs_path) 
        except: pass
        
        return anomalies

    def _generate_html(self, nodes, rels, props, hubs, samples, anomalies):
        vis_nodes = []
        vis_edges = []
        id_map = {} 
        
        # Logic to assign ID and Color
        def get_color(lbl):
            if lbl == "CustomerComplaint": return "#ff9999"
            if lbl == "Product": return "#99ff99"
            if "Ingredient" in lbl: return "#ccffcc"
            if "Sentiment" in lbl: return "#ffcc99"
            if "__Entity__" in lbl: return "#e0e0e0"
            return "#97c2fc" # Default blue

        for idx, (label, count) in enumerate(nodes.items()):
            node_id = idx + 1
            id_map[label] = node_id
            
            # Metadata for sidebar
            properties = props.get(label, ["(No explicit properties found)"])
            
            vis_nodes.append({
                "id": node_id,
                "label": f"{label}\\n({count})",
                "title": f"Click for details on {label}",
                "color": get_color(label),
                "shape": "box",
                "font": {"background": "white"},
                "meta": {
                    "count": count,
                    "properties": properties,
                    "hub": hubs.get(label),
                    "samples": samples.get(label, [])
                }
            })
            
        for r in rels:
            if r['source'] in id_map and r['target'] in id_map:
                vis_edges.append({
                    "from": id_map[r['source']],
                    "to": id_map[r['target']],
                    "label": f"{r['type']}\\n({r['count']})",
                    "arrows": "to",
                    "font": {"align": "middle", "background": "none"},
                    "color": {"color": "#848484"}
                })
        
        anom_list = "".join([f"<li class='error'>{a}</li>" for a in anomalies])
        
        # Generate Hubs List for Sidebar
        hubs_html = ""
        for label, hub_data in hubs.items():
            if hub_data:
                 hubs_html += f"<li><strong>{label}:</strong> {hub_data['name']} (Deg: {hub_data['degree']})</li>"

        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Knowledge Graph Schema Explorer</title>
  <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    body {{ margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; height: 100vh; overflow: hidden; }}
    #sidebar {{
        width: 350px;
        background: #f4f4f4;
        border-right: 1px solid #ddd;
        padding: 20px;
        box-shadow: 2px 0 5px rgba(0,0,0,0.1);
        display: flex;
        flex-direction: column;
        overflow-y: auto;
    }}
    #mynetwork {{ flex-grow: 1; background-color: #ffffff; }}
    
    h2 {{ color: #333; margin-top: 0; }}
    h3 {{ color: #555; border-bottom: 2px solid #ddd; padding-bottom: 5px; margin-top: 20px; }}
    
    .stat-card {{ background: white; padding: 10px; border-radius: 5px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    .stat-val {{ font-size: 1.2em; font-weight: bold; color: #007bff; }}
    .stat-label {{ font-size: 0.9em; color: #666; }}
    
    ul {{ list-style-type: none; padding: 0; }}
    li {{ padding: 5px 0; border-bottom: 1px solid #eee; word-break: break-all; }}
    li.error {{ color: #d9534f; font-weight: bold; }}
    
    #details-panel {{ display: none; margin-top: 20px; background: white; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; }}
    .prop-tag {{ display: inline-block; background: #eef; color: #44a; padding: 2px 6px; border-radius: 4px; font-size: 0.85em; margin: 2px; }}
    .sample-json {{ font-family: monospace; font-size: 0.8em; background: #f8f8f8; padding: 5px; border-radius: 3px; max-height: 150px; overflow: auto; white-space: pre-wrap; }}
  </style>
</head>
<body>

<div id="sidebar">
  <h2>🧠 KG Explorer</h2>
  
  <div class="stat-card">
    <div class="stat-val">{len(nodes)}</div>
    <div class="stat-label">Node Types</div>
  </div>
  
  <div class="stat-card">
    <div class="stat-val">{len(set(r['type'] for r in rels))}</div>
    <div class="stat-label">Relationship Types</div>
  </div>

  {f'<div class="stat-card" style="border-left: 4px solid #d9534f;"><h3>⚠️ Anomalies</h3><ul>{anom_list}</ul></div>' if anomalies else ''}

  <h3>🏆 Top Hubs</h3>
  <ul>{hubs_html}</ul>

  <div id="details-panel">
    <h3>Details</h3>
    <div id="detail-content">Select a node to view details.</div>
  </div>
  
  <div style="margin-top: auto; font-size: 0.8em; color: #999;">
    Generated by Agentic KG
  </div>
</div>

<div id="mynetwork"></div>

<script type="text/javascript">
  var nodes = new vis.DataSet({json.dumps(vis_nodes)});
  var edges = new vis.DataSet({json.dumps(vis_edges)});
  var container = document.getElementById('mynetwork');
  
  var data = {{ nodes: nodes, edges: edges }};
  
  var options = {{
    nodes: {{
        borderWidth: 2,
        shadow: true,
        font: {{ size: 14 }}
    }},
    edges: {{
        width: 1.5,
        shadow: false,
        smooth: {{ type: 'cubicBezier', forceDirection: 'horizontal', roundness: 0.4 }}
    }},
    physics: {{
      forceAtlas2Based: {{
          gravitationalConstant: -100,
          centralGravity: 0.005,
          springLength: 230,
          springConstant: 0.18,
          avoidOverlap: 1
      }},
      solver: 'forceAtlas2Based',
      stabilization: {{ iterations: 150 }}
    }},
    interaction: {{ hover: true }}
  }};

  var network = new vis.Network(container, data, options);
  
  network.on("click", function (params) {{
      var panel = document.getElementById("details-panel");
      var content = document.getElementById("detail-content");
      
      if (params.nodes.length > 0) {{
          var nodeId = params.nodes[0];
          var node = nodes.get(nodeId);
          
          var propsHtml = "";
          if (node.meta && node.meta.properties) {{
             propsHtml = node.meta.properties.map(p => `<span class="prop-tag">${{p}}</span>`).join(" ");
          }}
          
          var samplesHtml = "";
          if (node.meta && node.meta.samples && node.meta.samples.length > 0) {{
              samplesHtml = "<strong>Sample Data:</strong><div class='sample-json'>" + 
                            JSON.stringify(node.meta.samples, null, 2) + "</div>";
          }}

          var hubHtml = "";
          if (node.meta && node.meta.hub) {{
              hubHtml = `<br><strong>Top Hub:</strong> ${{node.meta.hub.name}} (Deg: ${{node.meta.hub.degree}})<br>`;
          }}
          
          content.innerHTML = `
            <strong>Type:</strong> ${{-1 !== node.label.indexOf("\\n") ? node.label.split("\\n")[0] : node.label}}<br>
            <strong>Count:</strong> ${{node.meta ? node.meta.count : "?"}}<br>
            ${{hubHtml}}
            <br>
            <strong>Properties:</strong><br>
            ${{propsHtml}}<br><br>
            ${{samplesHtml}}
          `;
          panel.style.display = "block";
      }} else {{
          panel.style.display = "none";
      }}
  }});
</script>

</body>
</html>
"""
