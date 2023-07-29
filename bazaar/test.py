import re

string = "hello"
val = re.sub(re.compile("(.+)l(.+)"), r"\2l\1", string)
print(val)