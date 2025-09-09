from pyvis.network import Network
import networkx as nx

def to_pyvis(G: nx.Graph, out_html: str, static: bool = True):
    """
    Build a PyVis graph. If static=True, positions are computed with NetworkX
    and physics is disabled so the layout does not keep moving.
    """
    net = Network(height="700px", width="100%", notebook=False, directed=False)

    if static:
        # Precompute positions and fix nodes
        pos = nx.spring_layout(G, seed=42, k=0.7, iterations=100)
        scale = 800  # convert layout coords (~[-1,1]) to pixels
        for n in G.nodes():
            strength = sum(G[n][nbr].get("weight", 1) for nbr in G.neighbors(n))
            x, y = pos[n]
            net.add_node(
                n,
                label=n,
                value=max(1, strength),
                title=f"Strength: {strength}",
                x=int(x * scale),
                y=int(y * scale),
                physics=False,
                fixed=True,
            )
        for u, v, data in G.edges(data=True):
            net.add_edge(u, v, value=data.get("weight", 1), physics=False)

        # Turn physics off globally
        net.set_options("""
        {
          "physics": { "enabled": false },
          "nodes": { "scaling": { "min": 8, "max": 40 }, "font": { "size": 18 } },
          "edges": { "smooth": { "type": "continuous" } },
          "interaction": { "hover": true, "zoomView": true, "dragView": true }
        }
        """)
    else:
        # (Optional) dynamic layout with stabilization if you ever want motion
        for n in G.nodes():
            strength = sum(G[n][nbr].get("weight", 1) for nbr in G.neighbors(n))
            net.add_node(n, label=n, value=max(1, strength), title=f"Strength: {strength}")
        for u, v, data in G.edges(data=True):
            net.add_edge(u, v, value=data.get("weight", 1))
        net.set_options("""
        {
          "physics": {
            "enabled": true,
            "solver": "forceAtlas2Based",
            "stabilization": { "enabled": true, "iterations": 1200 },
            "forceAtlas2Based": {
              "gravitationalConstant": -50,
              "springLength": 120,
              "springConstant": 0.08,
              "damping": 0.9,
              "avoidOverlap": 0.6
            }
          },
          "nodes": { "scaling": { "min": 8, "max": 40 }, "font": { "size": 18 } },
          "edges": { "smooth": { "type": "continuous" } }
        }
        """)

    net.write_html(out_html, notebook=False)
    return out_html
