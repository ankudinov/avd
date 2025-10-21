#!/usr/bin/env python3

import sys
sys.path.insert(0,'./python-avd')

import os
import json

from dataclasses import dataclass
from pathlib import Path
from schema_tools.metaschema.meta_schema_model import AristaAvdSchema, AvdSchemaBaseModel
from schema_tools.store import create_store

REPO_ROOT = Path(__file__).parents[2]
PYAVD_DIR = REPO_ROOT.joinpath("python-avd/pyavd")
METASCHEMA_DIR = PYAVD_DIR.joinpath("_schema")
EOS_DESIGNS_SCHEMA_DIR = PYAVD_DIR.joinpath("_eos_designs/schema")

@dataclass(frozen=True)
class SchemaPaths:
    yaml_file: Path
    pickled_schema: Path
    fragments_dir: Path | None = None
    python_class: Path | None = None
    docs_path: Path | None = None

# Remember to also update PICKLED_SCHEMAS in pyavd/_schema/constants.py
SCHEMAS = {
    # "avd_meta_schema": SchemaPaths(
    #     yaml_file=METASCHEMA_DIR.joinpath("avd_meta_schema.json"),
    #     pickled_schema=METASCHEMA_DIR.joinpath("avd_meta_schema.pickle"),
    # ),
    "eos_designs": SchemaPaths(
        yaml_file=EOS_DESIGNS_SCHEMA_DIR.joinpath("eos_designs.schema.yml"),
        pickled_schema=EOS_DESIGNS_SCHEMA_DIR.joinpath("eos_designs.schema.pickle"),
        fragments_dir=EOS_DESIGNS_SCHEMA_DIR.joinpath("schema_fragments"),
        python_class=EOS_DESIGNS_SCHEMA_DIR.joinpath("__init__.py"),
        docs_path=REPO_ROOT.joinpath("ansible_collections/arista/avd/roles/eos_designs/docs"),
    )
}

class MdDoc():

    def __init__(self):
        self.md_doc_string = ""  # init a string for Markdown doc

    def add(self, string_list_to_add: list):
        for a_string in string_list_to_add:
            self.md_doc_string += a_string + os.linesep
        # always add an empty string at the end
        self.md_doc_string += os.linesep

    def get(self):
        return self.md_doc_string

def generate_docs_for_keys(keys_schema: AristaAvdSchema, parent_key: str = "", doc_dir: str = 'typedoc/src'):

    if not os.path.exists(doc_dir):
        os.mkdir(doc_dir)

    top_doc_list = list()

    for key_name, v in keys_schema.items():

        # if parent key is not set - index top level documents
        if not parent_key:
            top_doc_list.append(f"src/{key_name}.md")

        if v.type == 'list':
            key_title = key_name + '[ ]'
        else:
            key_title = key_name

        try:
            required = v.required
        except:
            required = False

        children_md = []
        child_keys_md = []
        if hasattr(v, 'keys'):
            if v.keys:
                children_md.append("children:")
                child_keys_md = [
                    "## Child Keys",
                    ""
                ]
                for subkey in v.keys.keys():
                    children_md.append(f"    - {key_name}/{subkey}.md")
                    child_keys_md.append(f"- [`{subkey}`]({key_name}/{subkey}.md)")

        md = MdDoc()
        md.add([
            f"---",
            f"title: \"{key_title}\""
        ])
        if children_md:
            md.add(children_md)
        md.add([
            f"---",
            f"",
            f"## Key",
            f"",
            f"Key Name | Type | Required",
            f"---------|------|---------",
            f"`{key_name}` | {v.type} | {v.required}",
        ])

        try:
            if v.description:
                md.add([
                    f"## Description",
                    f"",
                    v.description
                ])
        except:
            pass

        md.add([
            f"## Path",
            f"",
            f"> NOTE: We are using the [same format as jq](https://jqlang.org/) to specify the path to the key.",
            f"",
            f"`.{key_name}`"
        ])

        if parent_key:
            md.add([
                f"## Parent Key",
                f"",
                f"`{parent_key}`"
            ])
        if child_keys_md:
            md.add(child_keys_md)

        with open(f'{doc_dir}/{key_name}.md', 'w') as f:
            f.write(md.get())

    if top_doc_list:
        typedoc_config = {
            "searchInComments": True,
            "searchInDocuments": True,
            "$schema": "https://typedoc.org/schema.json",
            "logLevel": "Verbose",
            "readme": "src/index.md",
            "projectDocuments": top_doc_list,
            "out": "site"
        }
        with open("typedoc/typedoc.config.jsonc", "w") as f:
            json.dump(typedoc_config, f, indent=4)

schema_store = create_store(force_rebuild=True)

for schema_name, schema_paths in SCHEMAS.items():
    # if not schema_paths.docs_path:
    #     continue

    schema = AristaAvdSchema(**schema_store[schema_name])
    generate_docs_for_keys(schema.keys)

# inject index.md temporarily
with open(f'typedoc/src/index.md', 'w') as f:
    f.write("# TEST\n\ntest\n")
