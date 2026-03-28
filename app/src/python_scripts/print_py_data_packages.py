"""
print.py — Data package processing script

Bu betik veri paketlerini (JSON, CSV, YAML gibi) okuyup işlemek için
örnek bir Python3 yapısı sunar.

Kendi veri paketlerinizi bu yapıya göre genişletebilirsiniz.
"""

import json
import csv
import yaml
from pathlib import Path
from typing import Any, Dict

def load_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def load_yaml(path: str) -> Dict[str, Any]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_csv(path: str) -> list:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def print_package_info(data: Any, source: str):
    print(f"--- Veri Paketi: {source} ---")
    print(json.dumps(data, indent=2, ensure_ascii=False))

def main():
    # Örnek dosya yolları (kendine göre düzenleyebilirsin)
    json_file = "data/sample.json"
    yaml_file = "data/sample.yaml"
    csv_file = "data/sample.csv"

    if Path(json_file).exists():
        data = load_json(json_file)
        print_package_info(data, json_file)

    if Path(yaml_file).exists():
        data = load_yaml(yaml_file)
        print_package_info(data, yaml_file)

    if Path(csv_file).exists():
        data = load_csv(csv_file)
        print_package_info(data, csv_file)

if __name__ == "__main__":
    main()
