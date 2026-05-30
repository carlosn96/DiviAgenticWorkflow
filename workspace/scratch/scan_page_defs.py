import glob
import json
import os

def scan_page_defs():
    files = glob.glob('DAW_bundle/site/bibliotheca/page-defs/*.json')
    for f in files:
        print(f"Scanning {f}...")
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
        except Exception as e:
            print(f"  Error loading JSON: {e}")
            continue

        anomalies = []
        def traverse(node, path=""):
            if isinstance(node, dict):
                if node.get('type') == 'divi/image' and 'image' in node:
                    anomalies.append(f"{path}/image module has nested 'image' key")
                if node.get('type') == 'divi/button' and 'button' in node:
                    anomalies.append(f"{path}/button module has nested 'button' key")
                for key, val in node.items():
                    traverse(val, f"{path}/{key}")
            elif isinstance(node, list):
                for idx, item in enumerate(node):
                    traverse(item, f"{path}[{idx}]")

        traverse(data)
        if anomalies:
            print(f"  Found anomalies in {f}:")
            for a in anomalies:
                print(f"    - {a}")
        else:
            print(f"  No anomalies in {f}")

if __name__ == '__main__':
    scan_page_defs()
