from html.parser import HTMLParser

class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.div_stack = []

    def handle_starttag(self, tag, attrs):
        if tag == "div":
            classes = [v for k, v in attrs if k == "class"]
            c = classes[0] if classes else "NO_CLASS"
            self.div_stack.append((c, self.getpos()[0]))
            print("  " * len(self.div_stack) + f"<{c} at line {self.getpos()[0]}>")

    def handle_endtag(self, tag):
        if tag == "div":
            if self.div_stack:
                c, line = self.div_stack.pop()
                print("  " * (len(self.div_stack)+1) + f"</{c} from line {line}>")

parser = MyHTMLParser()
with open("templates/configure.html", "r") as f:
    parser.feed(f.read())
parser.close()
