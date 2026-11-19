import html
import json
import re
import sys


FENCE = re.compile(r" {0,3}(`{3,}|~{3,})([^\n]*)$")
INLINE = re.compile(
    r"(?<!\\)\$`(?P<math>[^`\n]+)`\$|(?<!`)(?P<ticks>`+)(?!`).+?(?<!`)(?P=ticks)(?!`)"
)
MARKDOWN = str.maketrans({char: f"&#{ord(char)};" for char in r"\`_*[]~$|"})


def inline_math(match):
    if match["math"] is None:
        return match[0]
    formula = html.escape(r"\(" + match["math"] + r"\)", quote=False)
    return '<span class="math">' + formula.translate(MARKDOWN) + "</span>"


def render_math(content):
    output = []
    fence = None
    equation = None
    for line in content.splitlines(keepends=True):
        marker = FENCE.fullmatch(line.rstrip("\r\n"))
        if fence is not None:
            if marker and marker[1].startswith(fence) and not marker[2].strip():
                if equation is None:
                    output.append(line)
                else:
                    formula = html.escape("".join(equation).rstrip("\r\n"), quote=False)
                    output.append('<div class="math">\n\\[\n' + formula + '\n\\]\n</div>\n')
                fence = None
                equation = None
            elif equation is None:
                output.append(line)
            else:
                equation.append(line)
        elif marker:
            fence = marker[1]
            if marker[2].strip() == "math":
                equation = []
            else:
                output.append(line)
        elif line.startswith(("    ", "\t")):
            output.append(line)
        else:
            output.append(INLINE.sub(inline_math, line))
    if equation is not None:
        raise ValueError("Unclosed math fence")
    return "".join(output)


def process(items):
    for item in items:
        if chapter := item.get("Chapter"):
            chapter["content"] = render_math(chapter["content"])
            process(chapter["sub_items"])


if __name__ == "__main__":
    if sys.argv[1:2] == ["supports"]:
        sys.exit(0 if sys.argv[2:] == ["html"] else 1)
    _, book = json.load(sys.stdin.buffer)
    process(book["items"])
    sys.stdout.buffer.write(json.dumps(book, ensure_ascii=False).encode("utf-8"))
