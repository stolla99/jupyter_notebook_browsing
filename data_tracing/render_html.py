"""
Script is called from subprocess in e.g. process_kernels.py to render and get information of
an HTML element.
"""
import asyncio
import sys
from requests_html import HTML

script = """
function f1() {
    var list = document.getElementsByTagName("table");
    var mapped = [];
    for (let item of list) {
        mapped.push(item.offsetWidth)
    }
    var max = 0;
    for (var i = 0; i < mapped.length; i++) {
  		if (mapped[i] > max) {
        	max = mapped[i];
        }
	}
    console.log(max);
    return max
}
"""


def start_html(arg):
    """
    Starts a chromium instance and returns the width of the arg parameter

    arg HTML code with all tables of one CFG Cell reg exp=[<TABLE ... > ... </TABLE>]+
    """
    html = HTML(html=arg)
    val = html.render(script=script, reload=False)
    return val


if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    x = start_html(sys.argv[1])
    print(x)
    quit(1)
