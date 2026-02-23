import json

with open("Sample-data.json") as file:
    data = json.load(file)

print("Interface Status")
print("=" * 80)
print(f"{'DN':<50} {'Description':<20} {'Speed':<7} {'MTU':<6}")
print("-" * 80)

for item in data["imdata"]:
    a = item["l1PhysIf"]["attributes"]
    print(f"{a['dn']:<50} {a.get('descr', ''):<20} {a.get('speed', 'inherit'):<7} {a['mtu']:<6}")