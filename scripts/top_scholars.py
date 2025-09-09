import json, pathlib, collections
p = pathlib.Path("data/kirilloff/mentions.json")
m = json.loads(p.read_text(encoding="utf-8"))
ctr = collections.Counter(x["norm_name"] for x in m if x["mention_type"]=="person")
print("Top scholars (by mention count):")
for name, n in ctr.most_common(30):
    print(f"{n:3}  {name}")
