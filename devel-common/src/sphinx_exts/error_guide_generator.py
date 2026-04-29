# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from __future__ import annotations

import os
from pathlib import Path

import yaml

AIRFLOW_ROOT_PATH = Path(os.path.abspath(__file__)).parents[3]
GENERATED_PATH = AIRFLOW_ROOT_PATH / "airflow-core" / "docs" / "contributor" / "error_codes"
GENERATED_PATH.mkdir(parents=True, exist_ok=True)


def generate_error_docs(app):
    """Generates .rst files for each error code in the YAML mapping."""

    mapping_yaml_path = AIRFLOW_ROOT_PATH / "airflow-core" / "docs" / "error_mapping.yml"

    if not mapping_yaml_path.exists():
        from sphinx.util import logging

        logger = logging.getLogger(__name__)
        logger.error("Error mapping file missing at %s", mapping_yaml_path.absolute())
        return

    with open(mapping_yaml_path) as f:
        data = yaml.safe_load(f)

    guide_root = data.get("error_guide", {})
    guide_desc = guide_root.get("description", "")
    error_list = guide_root.get("error_codes", [])

    # license header
    license_header = """
 .. Licensed to the Apache Software Foundation (ASF) under one
    or more contributor license agreements.  See the NOTICE file
    distributed with this work for additional information
    regarding copyright ownership.  The ASF licenses this file
    to you under the Apache License, Version 2.0 (the
    "License"); you may not use this file except in compliance
    with the License.  You may obtain a copy of the License at

 ..   http://www.apache.org/licenses/LICENSE-2.0

 .. Unless required by applicable law or agreed to in writing,
    software distributed under the License is distributed on an
    "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
    KIND, either express or implied.  See the License for the
    specific language governing permissions and limitations
    under the License.
"""

    # index page
    index_rst_title = "Error Codes Guide"

    index_rst_lines = [
        license_header,
        "",
        index_rst_title,
        "=" * len(index_rst_title),
        "",
        guide_desc,
        "",
        ".. toctree::",
        "   :maxdepth: 1",
        "   :caption: Error Codes",
        "",
    ]

    for entry in error_list:
        code = entry["error_code"]

        # add it to toctree
        index_rst_lines.append(f"   {code}")

        # error page iter
        title = f"{code}: {entry['user_facing_error_message']}"
        underline = "=" * len(title)

        error_code_rst_lines = [
            title,
            underline,
            "",
            f"**Exception:** ``{entry['exception_type']}``",
            "",
            "Description",
            "-----------",
            entry["description"],
            "",
            "First Steps",
            "-----------",
            entry["first_steps"],
            "",
            "Documentation to refer",
            "-----------------------",
            entry["documentation"],
            "",
        ]

        rst_content = "\n".join(error_code_rst_lines) + "\n"

        (GENERATED_PATH / f"{code}.rst").write_text(
            rst_content,
            encoding="utf-8",
        )

    index_rst_lines.append("")

    # reinit index
    (GENERATED_PATH / "index.rst").write_text(
        "\n".join(index_rst_lines),
        encoding="utf-8",
    )


def setup(app):
    app.connect("builder-inited", generate_error_docs)
