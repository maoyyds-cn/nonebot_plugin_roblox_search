import os

base_dir = "."

for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.endswith('.py'):
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'rotunnel.com' in content:
                new_content = content.replace('rotunnel.com', 'rotunnel.com')
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"替换完成: {file_path}")

print("所有文件替换完成")
