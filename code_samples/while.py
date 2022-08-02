import subprocess
import sys

html_doc = "<TABLE ID=\"table\" WIDTH=\"\" BORDER=\"0\" CELLBORDER=\"1\" CELLSPACING=\"0\"><TR><TD>left</TD><TD " \
           "PORT=\"f1\">mid dle</TD><TD PORT=\"f2\">right</TD></TR></TABLE>" \
           "<TABLE ID=\"table\" WIDTH=\"232\" " \
           "BORDER=\"0\" CELLBORDER=\"1\" CELLSPACING=\"0\"><TR><TD>left</TD><TD " \
           "PORT=\"f1\">mid dle</TD><TD PORT=\"f2\">right</TD></TR></TABLE>"

p = subprocess.Popen(['python', '../data_tracing/render_html.py', html_doc], stdout=subprocess.PIPE)
y = int(p.stdout.readline().decode('utf-8'))
p.kill()
del p
print(y)
