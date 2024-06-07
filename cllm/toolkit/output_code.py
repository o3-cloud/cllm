import argparse
import json
import sys
import subprocess

def install_python_dependencies(dependencies):
    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            print(f"Failed to install {dep}", file=sys.stderr)

def install_dependencies(dependencies, code_type):
    if code_type == 'python':
        install_python_dependencies(dependencies)

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--skip-dependencies', action='store_true', help='Skip installing dependencies')
    return parser.parse_args()

def read_input_data():
    input_data = sys.stdin.read()
    return json.loads(input_data)

def main():
    args = parse_arguments()
    data = read_input_data()
    
    code = data.get('code', '')
    dependencies = data.get('dependencies', [])
    code_type = data.get('type', '')

    if not args.skip_dependencies:
        install_dependencies(dependencies, code_type)

    print(code)

if __name__ == '__main__':
    main()
