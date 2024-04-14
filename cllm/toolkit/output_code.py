import argparse
import json
import sys
import subprocess

def install_python_dependencies(dependencies):
    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            pass

def install_dependencies(dependencies, code_type):
    if code_type == 'python':
        install_python_dependencies(dependencies)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--skip-dependencies', action='store_true', help='Skip installing dependencies', default=False)
    args = parser.parse_args()

    input_data = sys.stdin.read()
    data = json.loads(input_data)
    code = data['code']
    dependencies = data.get('dependencies', [])
    code_type = data.get('type', '')
    
    if not args.skip_dependencies:
        install_dependencies(dependencies, code_type)

    print(code)

if __name__ == '__main__':
    main()
