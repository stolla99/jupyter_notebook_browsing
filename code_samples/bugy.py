b = [1, 2]
for a in b:
     if a > 5:
        if True:
            x = 0
            print('val')
            continue
            x = 5
        else:
            break
        x = 780
f = 5

import pygraphviz as pgv

G = pgv.AGraph(title="hello", compound=True, directed=True, strict=False)
G.add_node("node1")
G.add_node("node2")
G.add_node("node3")
G.add_node("node4")
G.add_node("node5")
G.add_edge("node1", "node2")
G.add_edge("node3", "node4")
G.subgraph(["node1", "node3", "node5"], name="cluster", label="Cluster")
G.subgraph(["node2", "node4"], name="cluster1", label="Cluster")

G.layout('dot')

G.draw('GHGKG.png')
print("")
