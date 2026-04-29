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

from unittest import mock

from check_airflow_error_codes import check_for_errors
from ci.prek.common_prek_utils import AIRFLOW_CORE_SOURCES_PATH, temporary_python_file


class TestCheckAirflowErrorCodes:
    def setup_method(self):
        self.exc_def = """
class ErrorCodesTestException(Exception):
    pass

raise ErrorCodesTestException"""

    @mock.patch("check_airflow_error_codes.load_error_mapping")
    def test_raise_with_unmapped_error_code(self, mock_load_error_mapping):
        mock_load_error_mapping.return_value = {"AERRTEST": "ErrorCodesTestException"}

        nonexistent_error_code = "AERRNOTINMAPPINGFILE"
        contents = f"{self.exc_def}('this is a test', error_code='{nonexistent_error_code}')"
        with temporary_python_file(AIRFLOW_CORE_SOURCES_PATH, contents) as f:
            errors = check_for_errors(paths=[f.name])

        assert len(errors) == 1
        error_substr = f"'{nonexistent_error_code}' not found in error mapping file"
        assert error_substr in errors[0]

    @mock.patch("check_airflow_error_codes.load_error_mapping")
    def test_raise_with_mapped_error_code(self, mock_load_error_mapping):
        mock_load_error_mapping.return_value = {"AERRTEST": "ErrorCodesTestException"}
        mapped_error_code = "AERRTEST"

        contents = f"{self.exc_def}('this is a test', error_code='{mapped_error_code}')"
        with temporary_python_file(AIRFLOW_CORE_SOURCES_PATH, contents) as f:
            errors = check_for_errors(paths=[f.name])

        assert len(errors) == 0

    @mock.patch("check_airflow_error_codes.load_error_mapping")
    def test_raise_with_mapped_error_code_elsewhere(self, mock_load_error_mapping):
        mock_load_error_mapping.return_value = {
            "AERRTEST01": "AirflowException",
            "AERRTEST02": "ErrorCodesTestException",
        }
        error_code_mapped_elsewhere = "AERRTEST01"

        contents = f"{self.exc_def}('this is a test', error_code='{error_code_mapped_elsewhere}')"
        with temporary_python_file(AIRFLOW_CORE_SOURCES_PATH, contents) as f:
            errors = check_for_errors(paths=[f.name])

        assert len(errors) == 1
        error_substr = f"error_code '{error_code_mapped_elsewhere}' not mapped to ErrorCodesTestException in error mapping file."
        assert error_substr in errors[0]

    @mock.patch("check_airflow_error_codes.load_error_mapping")
    def test_raise_without_error_code_unspecified(self, mock_load_error_mapping):
        mock_load_error_mapping.return_value = {"AERRTEST": "ErrorCodesTestException"}

        contents = f"{self.exc_def}('this is a test')"
        with temporary_python_file(AIRFLOW_CORE_SOURCES_PATH, contents) as f:
            errors = check_for_errors(paths=[f.name])

        assert len(errors) == 0

    @mock.patch("check_airflow_error_codes.load_error_mapping")
    def test_raise_bare(self, mock_load_error_mapping):
        mock_load_error_mapping.return_value = {"AERRTEST": "ErrorCodesTestException"}

        contents = self.exc_def
        with temporary_python_file(AIRFLOW_CORE_SOURCES_PATH, contents) as f:
            errors = check_for_errors(paths=[f.name])

        assert len(errors) == 0
