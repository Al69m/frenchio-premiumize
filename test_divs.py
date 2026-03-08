from html.parser import HTMLParser

class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.div_stack = []
        self.line_offset = 1

    def handle_starttag(self, tag, attrs):
        if tag == "div":
            classes = [v for k, v in attrs if k == "class"]
            self.div_stack.append(classes[0] if classes else "NO_CLASS")

    def handle_endtag(self, tag):
        if tag == "div":
            if self.div_stack:
                self.div_stack.pop()
            else:
                print(f"ERROR: Extra </div> at line {self.getpos()[0]}")

    def close(self):
        super().close()
        for i, div in enumerate(self.div_stack):
            print(f"Unclosed <div class='{div}'>")

parser = MyHTMLParser()
with open("templates/configure.html", "r") as f:
    parser.feed(f.read())
parser.close()
print("Done checking divs.")
