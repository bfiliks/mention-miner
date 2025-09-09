from pyvis.network import Network
import networkx as nx

def to_pyvis(G: nx.Graph, out_html: str):
    net = Network(height="700px", width="100%", notebook=False, directed=False)

    # size nodes by weighted degree (strength)
    for n in G.nodes():
        strength = sum(G[n][nbr].get("weight", 1) for nbr in G.neighbors(n))
        net.add_node(n, label=n, value=max(1, strength), title=f"Strength: {strength}")

    for u, v, data in G.edges(data=True):
        net.add_edge(u, v, value=data.get("weight", 1))

    # some reasonable defaults for layout/labels
    net.set_options("""
    const options = {
      nodes: { scaling: { min: 8, max: 40 }, font: { size: 18 } },
      edges: { smooth: { type: "continuous" } },
      physics: { solver: "forceAtlas2Based", forceAtlas2Based: { gravitationalConstant: -50 } }
    }""")
    net.write_html(out_html, notebook=False)
    return out_html
