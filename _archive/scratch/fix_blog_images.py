import json
import os

def fix_blog_images():
    path = 'DAW_bundle/site/bibliotheca/page-defs/blog.json'
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    def traverse(node):
        if isinstance(node, dict):
            if node.get('type') == 'divi/image' and 'image' in node:
                image_attr = node['image']
                inner_content = image_attr.get('innerContent', {})
                desktop = inner_content.get('desktop', {})
                val = desktop.get('value', {})
                if 'src' in val:
                    node['src'] = val['src']
                    if 'alt' in val:
                        node['alt'] = val['alt']
                    del node['image']
                    print(f"Fixed image module: {node['src']}")
            
            for key, val in node.items():
                traverse(val)
        elif isinstance(node, list):
            for item in node:
                traverse(item)

    traverse(data)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print("Successfully wrote fixed blog.json")

if __name__ == '__main__':
    fix_blog_images()
