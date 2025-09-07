import timeit
from xml.dom.minidom import parseString, Document


def copy1(doc):
    root = doc.documentElement.cloneNode(deep=True)
    copy = Document()
    copy.appendChild(root)
    return copy


def copy2(doc):
    return parseString(doc.toxml())


with open("ur10.urdf") as f:
    xml = f.read()
doc = parseString(xml)


print(timeit.timeit("copy1(doc)", globals=globals(), number=100))
print(timeit.timeit("copy2(doc)", globals=globals(), number=100))
