import os
import json
import javalang

# Define annotations that indicate controller classes
CONTROLLER_ANNOTATIONS = {'RestController', 'Controller'}

# Define annotations that indicate request mappings
REQUEST_MAPPING_ANNOTATIONS = {
    'RequestMapping',
    'GetMapping',
    'PostMapping',
    'PutMapping',
    'DeleteMapping',
    'PatchMapping'
}

def extract_endpoints_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        source = file.read()

    try:
        tree = javalang.parse.parse(source)
    except javalang.parser.JavaSyntaxError as e:
        print(f"Syntax error in file {file_path}: {e}")
        return []

    endpoints = []

    # Traverse the AST to find class declarations
    for path, node in tree.filter(javalang.tree.ClassDeclaration):
        class_annotations = {annotation.name for annotation in node.annotations}
        if not CONTROLLER_ANNOTATIONS.intersection(class_annotations):
            continue  # Skip classes that are not controllers

        # Get class-level @RequestMapping path if present
        class_path = ''
        for annotation in node.annotations:
            if annotation.name == 'RequestMapping':
                if annotation.element:
                    for element in annotation.element:
                        if element.name == 'value':
                            class_path = element.value.value.strip('"')
                            break

        # Traverse methods within the controller class
        for method in node.methods:
            method_path = ''
            http_method = 'GET'  # Default HTTP method
            for annotation in method.annotations:
                annotation_name = annotation.name
                if annotation_name in REQUEST_MAPPING_ANNOTATIONS:
                    # Determine HTTP method
                    if annotation_name != 'RequestMapping':
                        http_method = annotation_name.replace('Mapping', '').upper()
                    else:
                        # Check for 'method' attribute in @RequestMapping
                        if annotation.element:
                            for element in annotation.element:
                                if element.name == 'method':
                                    http_method = element.value.member  # e.g., RequestMethod.GET
                    # Extract path
                    if annotation.element:
                        for element in annotation.element:
                            if element.name == 'value':
                                method_path = element.value.value.strip('"')
                                break
                    break  # Only consider the first relevant annotation

            full_path = f"/{class_path.strip('/')}/{method_path.strip('/')}".replace('//', '/')
            endpoints.append({
                'class': node.name,
                'method': method.name,
                'http_method': http_method,
                'path': full_path,
                'file': file_path
            })

    return endpoints

def extract_endpoints_from_directory(directory):
    all_endpoints = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                endpoints = extract_endpoints_from_file(file_path)
                all_endpoints.extend(endpoints)
    return all_endpoints

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Extract API endpoints from Java source files.')
    parser.add_argument('directory', help='Path to the Java project directory')
    parser.add_argument('--output', default='api_endpoints.json', help='Output JSON file name')

    args = parser.parse_args()

    endpoints = extract_endpoints_from_directory(args.directory)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(endpoints, f, indent=2)

    print(f"Extracted {len(endpoints)} endpoints. Results saved to {args.output}")
