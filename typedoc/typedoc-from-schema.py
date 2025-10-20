#!/usr/bin/env python3

import sys
sys.path.insert(0,'/workspaces/avd/python-avd')

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

schema_store = create_store(force_rebuild=True)

typedoc_dir = "/workspaces/avd/typedoc/src"
if not os.path.exists(typedoc_dir):
    os.mkdir(typedoc_dir)

top_doc_list = list()

for schema_name, schema_paths in SCHEMAS.items():
    # if not schema_paths.docs_path:
    #     continue

    schema = AristaAvdSchema(**schema_store[schema_name])
    schema_dict=schema.keys
    for key_name, v in schema.keys.items():

        if v.type == 'list':
            key_title = key_name + '[]'
        else:
            key_title = key_name

        top_doc_list.append(f"src/{key_name}.md")

        try:
            required = v.required
        except:
            required = False
        md_doc_list = [
            f"---",
            f"title: {key_title}",
            f"---",
            f"",
            f"## Key",
            f"",
            f"Key Name | Type | Required",
            f"---------|------|---------",
            f"`{key_name}` | {v.type} | {v.required}"
        ]
        md_doc_string = ""
        for a_line in md_doc_list:
            md_doc_string += a_line + os.linesep

        with open(f'{typedoc_dir}/{key_title}.md', 'w') as f:
            f.write(md_doc_string)
        
typedoc_config = {
    "searchInComments": True,
    "searchInDocuments": True,
    "$schema": "https://typedoc.org/schema.json",
    "logLevel": "Verbose",
    "readme": "src/index.md",
    "projectDocuments": top_doc_list,
    "out": "site"
}

with open("/workspaces/avd/typedoc/typedoc.config.jsonc", "w") as f:
    json.dump(typedoc_config, f, indent=4)
