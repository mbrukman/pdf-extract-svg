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
ifeq (VERBOSE,1)
	VERB =
endif

PORT = 8080

# Note: for security, this web server will only be accessible from the same
# machine that is running the server. If you want to access the server from
# another machine, remove the `--bind 127.0.0.1` flag from the command below.
run:
	$(VERB) echo "Listening on http://localhost:$(PORT) ..."
	$(VERB) python -m http.server $(PORT) --bind 127.0.0.1
