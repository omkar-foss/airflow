#!/usr/bin/env python3
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

import ast
import sys
from pathlib import Path

import yaml
from common_prek_utils import AIRFLOW_CORE_ROOT_PATH

ERROR_MAPPING_PATH = AIRFLOW_CORE_ROOT_PATH / "docs" / "error_mapping.yml"


def load_error_mapping() -> dict[str, str]:
    """Load the error mapping yaml file and return error codes as a set."""

    if not ERROR_MAPPING_PATH.exists():
        print(f"WARNING: {ERROR_MAPPING_PATH} not found")
        return {}

    with open(ERROR_MAPPING_PATH) as f:
        mapping = yaml.safe_load(f)

    if not mapping:
        print(f"Unable to load error mapping file {ERROR_MAPPING_PATH}.")
        return {}

    try:
        error_codes_list = mapping["error_guide"]["error_codes"]
        error_codes: dict[str, str] = {}
        for ec in error_codes_list:
            error_codes[ec["error_code"]] = ec["exception_type"]
        return error_codes
    except KeyError:
        print(f"Invalid yaml structure in error mapping file {ERROR_MAPPING_PATH}.")
        return {}


def check_raise_statement(
    error_codes: dict[str, str],
    node: ast.Raise,
    filename: str,
    line_no: int,
) -> list[str]:

    errors = []

    if not error_codes:
        errors.append("Unable to load list of valid error codes.")
        return errors

    if node.exc is None:
        return errors

    exc = node.exc

    if not isinstance(exc, ast.Call):
        return errors

    func = exc.func
    func_name = None
    if isinstance(func, ast.Name):
        func_name = func.id
    elif isinstance(func, ast.Attribute):
        func_name = func.attr

    has_error_code = any(kw.arg == "error_code" for kw in exc.keywords if kw.arg)
    if not has_error_code:
        return errors

    kw_error_code = next(kw for kw in exc.keywords if kw.arg == "error_code")
    if not isinstance(kw_error_code.value, ast.Constant):
        errors.append(f"{filename}:{line_no}: error_code must be a constant value")
        return errors

    error_code = kw_error_code.value.value
    error_code_str = error_code.decode() if isinstance(error_code, bytes) else str(error_code)
    exc_class = error_codes.get(error_code_str)
    if exc_class is None:
        errors.append(
            f"{filename}:{line_no}: error_code '{error_code_str}' not found in error mapping file,"
            f" please define it in {ERROR_MAPPING_PATH}."
        )
    elif exc_class != func_name:
        errors.append(
            f"{filename}:{line_no}: error_code '{error_code_str}' not mapped to {func_name} in error mapping file."
        )

    return errors


def validate_file(error_codes: dict[str, str], filepath: Path) -> list[str]:
    """Initiates the validation process and returns a list of errors."""

    errors = []
    try:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
        filename = str(filepath)
        tree = ast.parse(source, filename=filename)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Raise):
                continue
            errors.extend(
                check_raise_statement(
                    error_codes,
                    node,
                    filename,
                    node.lineno,
                )
            )
    except SyntaxError as e:
        errors.append(f"{filepath}:{e.lineno}: SyntaxError: {e.msg}")
    except Exception as e:
        errors.append(f"{filepath}: Error parsing: {e}")

    return errors


def check_for_errors(paths: list[str]):
    error_codes: dict[str, str] = load_error_mapping()
    if not error_codes:
        print("No error codes loaded from error mapping file. Exiting.")
        sys.exit(1)

    errors = []
    files = [Path(f) for f in paths]
    for filepath in files:
        errors.extend(validate_file(error_codes, filepath))

    return errors


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: check_airflow_error_codes.py <file1.py> [file2.py ...]")
        sys.exit(1)

    errors = check_for_errors(sys.argv[1:])
    if errors:
        for error in errors:
            print(error)
        sys.exit(1)
    sys.exit(0)
