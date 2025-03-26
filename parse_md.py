import os
import re
import csv

markdown_dir = "dishes"
csv_dir = "csv"

if not os.path.exists(csv_dir):
    os.makedirs(csv_dir)

csv_files = {
    'dishes': ['name'],
    'categories': ['dish_name', 'category_type'],
    'items': ['dish_name', 'name'],
    'calc_items': ['dish_name', 'description'],
    'steps': ['dish_name', 'id', 'description', 'order'],
    'extra_details': ['dish_name', 'description']
}

for csv_name, headers in csv_files.items():
    with open(os.path.join(csv_dir, f"{csv_name}.csv"), 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)

for filename in os.listdir(markdown_dir):
    if filename.endswith('.md'):
        file_path = os.path.join(markdown_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        dish_name = re.search(r'# (.+?)的做法', content).group(1).strip()

        # 提取類別內容
        items_section = re.search(r'## 必備原料和工具\n([\s\S]+?)\n##', content).group(1)
        items = [line.strip('- ').strip() for line in items_section.split('\n') if line.strip().startswith('-')]

        calc_section = re.search(r'## 計算\n([\s\S]+?)\n##', content).group(1)
        calc_items = [line.strip('- ').strip() for line in calc_section.split('\n') if line.strip().startswith('-')]

        steps_section = re.search(r'## 操作\n([\s\S]+?)(?:\n##|$)', content).group(1)
        steps = [line.strip('- ').strip() for line in steps_section.split('\n') if line.strip().startswith('-')]
        steps_with_order = [(f"{dish_name}_{i+1}", step, i+1) for i, step in enumerate(steps)]

        extra_section_match = re.search(r'## 附加內容\n([\s\S]+)', content)
        extra_details = [extra_section_match.group(1).strip()] if extra_section_match else []

        # 寫入 CSV
        with open(os.path.join(csv_dir, 'dishes.csv'), 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([dish_name])

        with open(os.path.join(csv_dir, 'categories.csv'), 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for cat_type in ['RequiredItems', 'Calculation', 'Steps', 'ExtraInfo']:
                writer.writerow([dish_name, cat_type])

        with open(os.path.join(csv_dir, 'items.csv'), 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for item in items:
                writer.writerow([dish_name, item])

        with open(os.path.join(csv_dir, 'calc_items.csv'), 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for calc in calc_items:
                writer.writerow([dish_name, calc])

        with open(os.path.join(csv_dir, 'steps.csv'), 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for step_id, desc, order in steps_with_order:
                writer.writerow([dish_name, step_id, desc, order])

        with open(os.path.join(csv_dir, 'extra_details.csv'), 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for detail in extra_details:
                writer.writerow([dish_name, detail])

print("CSV 生成完成！")
