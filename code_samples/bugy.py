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

from pygraphviz import AGraph
g = AGraph()
g.add_node("a00", label="<f0> text | {<f1> f1 | <f2> text}", shape="record")
g.add_node("a01", label="<f0> f0 | {<f1> text | <f2> text}", shape="record")
g.add_edge('a00', 'a01', tailport='f1', headport='f0')


g.layout('dot')

g.draw('GHGKG.png')
print("")
