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


class Config(object):
    def __init__(self, default_section=None, tox_file='tox.ini'):
        conf = configparser.RawConfigParser()
        conf.read(tox_file)

        self.conf = conf
        self.default_section = default_section

    def get(self, option, section=None, default=None):
        section = section or self.default_section

        if not self.conf.has_section(section):
            return default

        if self.conf.has_option(section, option):
            return self.conf.get(section, option).strip()

        return default

    def get_multiple(self, option, section=None, default=None):
        section = section or self.default_section

        values = self.get(option, section)
        if not values:
            return default

        values = [v.strip() for v in values.split('\n') if v.strip()]
        result = []
        for vals in values:
            result.extend([v.strip() for v in vals.split(',') if v.strip()])

        return result
