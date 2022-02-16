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

G = pgv.AGraph(title="hello", compound=True, directed=True, strict=False, rankdir="TB")
G.add_node("1", label="x")
G.add_node("2", label="x")
G.add_edge("1", "2")
G.subgraph(["1", "2"], rank="same")


G.layout('dot')

G.draw('GHGKG.png')
print("")
