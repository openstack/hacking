#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import ast

from hacking import core


@core.off_by_default
@core.flake8ext
class MockAutospecCheck(object):
    """Check for 'autospec' in mock.patch/mock.patch.object calls

    Okay: mock.patch('target_module_1', autospec=True)
    Okay: mock.patch('target_module_1', autospec=False)
    Okay: mock.patch('target_module_1', autospec=None)
    Okay: mock.patch('target_module_1', defined_mock)
    Okay: mock.patch('target_module_1', new=defined_mock)
    Okay: mock.patch('target_module_1', new_callable=SomeFunc)
    Okay: mock.patch('target_module_1', defined_mock)
    Okay: mock.patch('target_module_1', spec=1000)
    Okay: mock.patch('target_module_1', spec_set=['data'])
    Okay: mock.patch('target_module_1', wraps=some_obj)

    H210: mock.patch('target_module_1')
    Okay: mock.patch('target_module_1')  # noqa
    H210: mock.patch('target_module_1', somearg=23)
    Okay: mock.patch('target_module_1', somearg=23)  # noqa

    Okay: mock.patch.object('target_module_2', 'attribute', autospec=True)
    Okay: mock.patch.object('target_module_2', 'attribute', autospec=False)
    Okay: mock.patch.object('target_module_2', 'attribute', autospec=None)
    Okay: mock.patch.object('target_module_2', 'attribute', new=defined_mock)
    Okay: mock.patch.object('target_module_2', 'attribute', defined_mock)
    Okay: mock.patch.object('target_module_2', 'attribute', new_callable=AFunc)
    Okay: mock.patch.object('target_module_2', 'attribute', spec=3)
    Okay: mock.patch.object('target_module_2', 'attribute', spec_set=[3])
    Okay: mock.patch.object('target_module_2', 'attribute', wraps=some_obj)


    H210: mock.patch.object('target_module_2', 'attribute', somearg=2)
    H210: mock.patch.object('target_module_2', 'attribute')

    """

    name = "mock_check"
    version = "1.00"

    def __init__(self, tree, filename):
        self.filename = filename
        self.tree = tree

    def run(self):
        mcv = MockCheckVisitor(self.filename)
        mcv.visit(self.tree)
        for message in mcv.messages:
            yield message


class MockCheckVisitor(ast.NodeVisitor):
    # Patchers we are looking for and minimum number of 'args' without
    # 'autospec' to not be flagged
    patchers = {'mock.patch': 2, 'mock.patch.object': 3}
    spec_keywords = {"autospec", "new", "new_callable", "spec", "spec_set",
                     "wraps"}

    def __init__(self, filename):
        super(MockCheckVisitor, self).__init__()
        self.messages = []
        self.filename = filename

    def check_missing_autospec(self, call_node):

        def find_autospec_keyword(keyword_node):
            for keyword_obj in keyword_node:
                keyword = keyword_obj.arg
                # If they have defined autospec or new then it is okay
                if keyword in self.spec_keywords:
                    return True
            return False

        if isinstance(call_node, ast.Call):
            func_info = FunctionNameFinder(self.filename)
            func_info.visit(call_node)

            # We are only looking at our patchers
            if func_info.function_name not in self.patchers:
                return

            min_args = self.patchers[func_info.function_name]

            if not find_autospec_keyword(call_node.keywords):
                if len(call_node.args) < min_args:
                    self.messages.append(
                        (call_node.lineno, call_node.col_offset,
                         "H210 Missing 'autospec' or 'spec_set' keyword in "
                         "mock.patch/mock.patch.object", MockCheckVisitor)
                    )

    def visit_Call(self, node):
        self.check_missing_autospec(node)
        self.generic_visit(node)


class FunctionNameFinder(ast.NodeVisitor):
    """Finds the name of the function"""
    def __init__(self, filename):
        super(FunctionNameFinder, self).__init__()
        self._func_name = []
        self.filename = filename

    @property
    def function_name(self):
        return '.'.join(reversed(self._func_name))

    def visit_Name(self, node):
        self._func_name.append(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        try:
            self._func_name.append(node.attr)
            self._func_name.append(node.value.id)
        except AttributeError:
            self.generic_visit(node)

    def visit(self, node):
        # If we get called with an ast.Call node, then work on the 'node.func',
        # as we want the function name.
        if isinstance(node, ast.Call):
            return super(FunctionNameFinder, self).visit(node.func)
        return super(FunctionNameFinder, self).visit(node)
