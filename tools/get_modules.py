import os


def get_modules():
    current_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    target_dir = current_dir.replace('tools', 'module')
    all_files = os.listdir(target_dir)
    files = list()
    for file in all_files:
        if file.startswith('__') or file.startswith('.'):
            continue
        file = file[:-3]
        files.append(file)

    return (target_dir, files)
