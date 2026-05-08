# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import configparser
from typing import overload


class Config:
    def __init__(
        self, default_section: str, tox_file: str = 'tox.ini'
    ) -> None:
        conf = configparser.RawConfigParser()
        conf.read(tox_file)

        self.conf = conf
        self.default_section = default_section

    def get(
        self,
        option: str,
        section: str | None = None,
        default: str | None = None,
    ) -> str | None:
        section = section or self.default_section

        if not self.conf.has_section(section):
            return default

        if self.conf.has_option(section, option):
            return self.conf.get(section, option).strip()

        return default

    @overload
    def get_multiple(
        self, option: str, section: str | None = None, default: list[str] = ...
    ) -> list[str]:
        ...

    @overload
    def get_multiple(
        self,
        option: str,
        section: str | None = None,
        default: list[str] | None = None,
    ) -> list[str] | None:
        ...

    def get_multiple(
        self,
        option: str,
        section: str | None = None,
        default: list[str] | None = None,
    ) -> list[str] | None:
        section = section or self.default_section

        raw_value = self.get(option, section)
        if not raw_value:
            return default

        values = [v.strip() for v in raw_value.split('\n') if v.strip()]
        result = []
        for vals in values:
            result.extend([v.strip() for v in vals.split(',') if v.strip()])

        return result
