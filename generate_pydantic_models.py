# import json
# import argparse
# from pathlib import Path
# from typing import Dict, Set
# import re

# def to_camel_case(s):
#     return ''.join(word.capitalize() for word in re.split(r"[\s_\-]+", s))

# def to_snake_case(name):
#     return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

# TYPE_MAP = {
#     "string": "str",
#     "integer": "int",
#     "number": "float",
#     "boolean": "bool",
#     "object": "dict",
#     "array": "List"
# }
# def escape_description(text: str) -> str:
#     return text.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n")

# def get_prop_type(prop, imports: Set[str]) -> str:
#     if "$ref" in prop:
#         return prop["$ref"].split("/")[-1]
#     elif "enum" in prop:
#         literals = ", ".join(f'"{v}"' if isinstance(v, str) else str(v) for v in prop["enum"])
#         imports.add("from typing import Literal")
#         return f"Literal[{literals}]"
#     elif prop.get("type") == "array":
#         items = prop.get("items", {})
#         item_type = get_prop_type(items, imports)
#         imports.add("from typing import List")
#         return f"List[{item_type}]"
#     else:
#         return TYPE_MAP.get(prop.get("type", "Any"), "Any")

# def generate_models(schemas: Dict, imports: Set[str]) -> str:
#     forward_decls = []
#     classes = []
#     base_model = """class OpenAPIModel(BaseModel):
#     @classmethod
#     def from_dict(cls, data: dict):
#         # Use alias mapping (snake_case to original)
#         return cls(**data)

#     def to_dict(self):
#         return self.dict(by_alias=True)"""

#     for class_name, schema in schemas.items():
#         if schema.get("type") and schema["type"] != "object":
#             continue
#         props = schema.get("properties", {})
#         required = set(schema.get("required", []))
#         class_lines = [f"class {class_name}(OpenAPIModel):"]
#         if not props:
#             class_lines.append("    pass")
#         else:
#             for name, prop in props.items():
#                 description = escape_description(prop.get("description", ""))
#                 prop_type = get_prop_type(prop, imports)
#                 if name not in required:
#                     imports.add("from typing import Optional")
#                     class_lines.append(f'    {to_snake_case(name)}: Optional[{prop_type}] = Field(None, description="{description}", alias="{name}")')
#                 else:
#                     class_lines.append(f'    {to_snake_case(name)}: {prop_type} = Field(..., description="{description}", alias="{name}")')
#         classes.append("\n".join(class_lines))

#     import_block = "\n".join(sorted(imports | {"from pydantic import BaseModel, Field"}))
#     return import_block + "\n\n" + base_model + "\n\n" + "\n\n".join(classes)

# def main():
#     parser = argparse.ArgumentParser(description="Generate Pydantic models from OpenAPI schemas")
#     parser.add_argument("--input", required=True, help="Path to OpenAPI JSON file")
#     parser.add_argument("--output", required=True, help="Path to output Python file")

#     args = parser.parse_args()
#     with open(args.input) as f:
#         data = json.load(f)

#     schemas = data.get("components", {}).get("schemas", {})
#     imports = set()
#     model_code = generate_models(schemas, imports)

#     with open(args.output, "w") as out:
#         out.write(model_code)
#     print(f"✅ Models written to {args.output}")

# if __name__ == "__main__":
#     main()


import json
import argparse
import re
from pathlib import Path
from typing import Dict, Set, List


TYPE_MAP = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "object": "dict",
    "array": "List"
}


def to_camel_case(s: str) -> str:
    return ''.join(word.capitalize() for word in re.split(r'[\s_\-]+', s))


def to_snake_case(name: str) -> str:
    name = re.sub(r'(?<=[a-z0-9])([A-Z])', r'_\1', name)  # Add _ before uppercase letters following lowercase/digits
    return name.lower()


def escape_description(text: str) -> str:
    return text.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n")


def get_prop_type(prop, imports: Set[str], dependencies: Set[str]) -> str:
    if "$ref" in prop:
        ref = prop["$ref"].split("/")[-1]
        dependencies.add(ref)
        return ref
    elif "enum" in prop:
        literals = ", ".join(f'"{v}"' if isinstance(v, str) else str(v) for v in prop["enum"])
        imports.add("from typing import Literal")
        return f"Literal[{literals}]"
    elif prop.get("type") == "array":
        items = prop.get("items", {})
        item_type = get_prop_type(items, imports, dependencies)
        imports.add("from typing import List")
        return f"List[{item_type}]"
    else:
        return TYPE_MAP.get(prop.get("type", "Any"), "Any")


def build_dependency_graph(schemas: Dict) -> Dict[str, Set[str]]:
    graph = {}
    for class_name, schema in schemas.items():
        deps = set()
        props = schema.get("properties", {})
        for prop in props.values():
            _ = get_prop_type(prop, set(), deps)
        graph[class_name] = deps
    return graph


def topological_sort(graph: Dict[str, Set[str]]) -> List[str]:
    visited = set()
    temp = set()
    result = []
    cycles = []

    def visit(n):
        if n in visited:
            return
        if n in temp:
            cycles.append(n)
            return
        temp.add(n)
        for m in graph.get(n, []):
            visit(m)
        temp.remove(n)
        visited.add(n)
        result.append(n)

    for node in graph:
        visit(node)

    return result, set(cycles)

def collect_dependencies(root_names, schema_map):
    seen = set()

    def visit(name):
        if name in seen or name not in schema_map:
            return
        seen.add(name)
        schema = schema_map[name]
        refs = set()

        # Check allOf references
        if "allOf" in schema:
            for part in schema["allOf"]:
                if "$ref" in part:
                    refs.add(part["$ref"].split("/")[-1])
                for prop in part.get("properties", {}).values():
                    _ = get_prop_type(prop, set(), refs)
        else:
            for prop in schema.get("properties", {}).values():
                _ = get_prop_type(prop, set(), refs)

        for ref in refs:
            visit(ref)

    for leaf in root_names:
        visit(leaf)

    return seen

def generate_openapi_model_base() -> str:
    return '''
from pydantic import BaseModel

class SerializableModel(BaseModel):
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

    def to_dict(self):
        return self.model_dump(by_alias=True)
'''

def parse_allof(schema, class_name, imports, dependencies):
    """
    Parses an OpenAPI schema with allOf. Returns:
    - List of base classes (from $ref)
    - Properties (combined if there are inline parts)
    """
    base_classes = []
    combined_properties = {}
    required_fields = set()

    for item in schema.get("allOf", []):
        if "$ref" in item:
            ref = item["$ref"].split("/")[-1]
            base_classes.append(ref)
            dependencies.add(ref)
        else:
            combined_properties.update(item.get("properties", {}))
            required_fields.update(item.get("required", []))

    # If there are no properties of our own, rely fully on base_classes
    return base_classes, combined_properties, required_fields

def generate_models(schemas: Dict) -> str:
    imports = set()
    model_definitions = {}
    # scalar_definitions = []
    dependency_graph = build_dependency_graph(schemas)
    sorted_classes, cyclic_classes = topological_sort(dependency_graph)

    for class_name in sorted_classes:
        schema = schemas[class_name]
        class_deps = set()
        if "allOf" in schema:
            base_classes, props, required = parse_allof(schema, class_name, imports, class_deps)
        # elif not schema.get("type") in ["object", "array"]:
        #     description = schema.get("description", "").replace("\"", "\\\"").replace("\n", "\\n")
        #     alias = class_name
        #     scalar_type = TYPE_MAP.get(schema["type"], "Any")
        #     line = f"{alias} = {scalar_type}  # {description}" if description else f"{alias} = {scalar_type}"
        #     # scalar_definitions.append(line)
        #     model_definitions[class_name] = line
        #     continue
        else:
            base_classes = ["SerializableModel"]
            props = schema.get("properties", {})
            required = set(schema.get("required", []))
        bases = ", ".join(base_classes)
        class_lines = [f"class {class_name}({bases}):"]

        if not props:
            class_lines.append("    pass")
        else:
            for name, prop in props.items():
                orig_name = name
                snake_name = to_snake_case(name)
                description = escape_description(prop.get("description", ""))
                prop_type = get_prop_type(prop, imports, class_deps)
                field_args = [f"alias=\"{orig_name}\""]
                if description:
                    field_args.append(f"description=\"{description}\"")
                if name not in required:
                    imports.add("from typing import Optional")
                    class_lines.append(
                        f"    {snake_name}: Optional[{prop_type}] = Field(None, {', '.join(field_args)})"
                    )
                else:
                    class_lines.append(
                        f"    {snake_name}: {prop_type} = Field(..., {', '.join(field_args)})"
                    )
        if class_name in cyclic_classes:
            class_lines.append(f"    model_rebuild()")
            imports.add("from pydantic import Field, model_rebuild")
        else:
            imports.add("from pydantic import Field")
        model_definitions[class_name] = "\n".join(class_lines)

    import_block = "\n".join(sorted(imports | {"from typing import List"}))
    all_models = "\n\n".join(model_definitions[class_name] for class_name in sorted_classes)
    base_class_code = generate_openapi_model_base()
    return f"{import_block}\n\n{base_class_code}\n\n{all_models}"


def main():
    parser = argparse.ArgumentParser(description="Generate Pydantic models from OpenAPI schemas")
    parser.add_argument("--input", required=True, help="Path to OpenAPI JSON file")
    parser.add_argument("--output", required=True, help="Path to output Python file")
    parser.add_argument("--leafs", nargs="+", help="List of class names to include (and their dependencies)")

    args = parser.parse_args()
    with open(args.input) as f:
        data = json.load(f)

    schemas = data.get("components", {}).get("schemas", {})
    if args.leafs:
        included = collect_dependencies(args.leafs, schemas)
        schemas = {k: v for k, v in schemas.items() if k in included}

    model_code = generate_models(schemas)

    with open(args.output, "w") as out:
        out.write(model_code)
    print(f"✅ Models written to {args.output}")


if __name__ == "__main__":
    main()
