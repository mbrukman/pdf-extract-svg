# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

VERB = @
ifeq ($(VERBOSE),1)
	VERB =
endif

PYTHON_VERSION ?= $(shell python -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')")

mypy-test:
	$(VERB) python -m mypy --python-version=$(PYTHON_VERSION) --check-untyped-defs --ignore-missing-imports `find . -name 'third_party' -prune -o -name '*.py' -print`

pytype-test:
	$(VERB) python -m pytype --python-version=$(PYTHON_VERSION) -k `find . -name 'third_party' -prune -o -name '*.py' -print`
