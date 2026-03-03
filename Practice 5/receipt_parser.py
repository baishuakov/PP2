import re
import json

with open("raw.txt", "r", encoding="utf-8") as f:
    data = f.read()

result = {
    "date": None,
    "time": None,
    "payment_method": None,
    "products": [],
    "all_prices": [],
    "calculated_total": 0.0
}

dt_match = re.search(r"(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2}:\d{2})", data)
if dt_match:
    result["date"] = dt_match.group(1)
    result["time"] = dt_match.group(2)

pay_match = re.search(r"([А-Яа-я ]+):\n[\d\s,]+\nИТОГО", data)
if pay_match:
    result["payment_method"] = pay_match.group(1).strip()

product_pattern = r"\d+\.\n(.*?)\n.*?\n([\d\s,]+)\nСтоимость"
items_found = re.findall(product_pattern, data, re.DOTALL)

for item in items_found:
    name = item[0].strip().replace('\n', ' ')
    price_str = item[1].strip().replace(" ", "").replace(",", ".")
    price = float(price_str)

result["calculated_total"] = sum(result["all_prices"])

print(json.dumps(result, indent=4, ensure_ascii=False))