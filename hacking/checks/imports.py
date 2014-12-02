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

import imp
import inspect
import os
import re
import sys
import traceback

from hacking import core

RE_RELATIVE_IMPORT = re.compile('^from\s*[.]')

modules_cache = dict((mod, True) for mod in tuple(sys.modules.keys())
                     + sys.builtin_module_names)


@core.flake8ext
def hacking_import_rules(logical_line, physical_line, filename, noqa):
    r"""Check for imports.

    OpenStack HACKING guide recommends one import per line:
    Do not import more than one module per line

    Examples:
    Okay: from nova.compute import api
    H301: from nova.compute import api, utils


    Imports should usually be on separate lines.

    OpenStack HACKING guide recommends importing only modules:
    Do not import objects, only modules

    Examples:
    Okay: from os import path
    Okay: from os import path as p
    Okay: from os import (path as p)
    Okay: import os.path
    Okay: from nova.compute import rpcapi
    Okay: from os.path import dirname as dirname2  # noqa
    Okay: from six.moves.urllib import parse
    H302: from os.path import dirname as dirname2
    H302: from os.path import (dirname as dirname2)
    H303: from os.path import *
    H304: from .compute import rpcapi
    """
    # TODO(jogo): make the following doctests pass:
    #            H301: import os, sys
    # NOTE(afazekas): An old style relative import example will not be able to
    # pass the doctest, since the relativity depends on the file's locality
    # TODO(mordred: We need to split this into 4 different checks so that they
    # can be disabled by command line switches properly

    if noqa:
        return

    def is_module_for_sure(mod, search_path=sys.path):
        mod = mod.replace('(', '')  # Ignore parentheses
        for finder in sys.meta_path:
            if finder.find_module(mod) is not None:
                return True
        try:
            mod_name = mod
            while '.' in mod_name:
                pack_name, _sep, mod_name = mod_name.partition('.')
                f, p, d = imp.find_module(pack_name, search_path)
                search_path = [p]
            imp.find_module(mod_name, search_path)
        except ImportError:
            try:
                # NOTE(vish): handle namespace modules
                if '.' in mod:
                    pack_name, mod_name = mod.rsplit('.', 1)
                    __import__(pack_name, fromlist=[mod_name])
                else:
                    __import__(mod)
            except ImportError:
                # NOTE(imelnikov): import error here means the thing is
                # not importable in current environment, either because
                # of missing dependency, typo in code being checked, or
                # any other reason. Anyway, we have no means to know if
                # it is module or not, so we return True to avoid
                # false positives.
                return True
            except Exception:
                # NOTE(jogo) don't stack trace if unexpected import error,
                # log and continue.
                traceback.print_exc()
                return False
            else:
                # NOTE(imelnikov): we imported the thing; if it was module,
                # it must be there:
                if mod in sys.modules:
                    return True
                else:
                    # NOTE(dhellmann): If the thing isn't there under
                    # its own name, look to see if it is a module
                    # redirection import in one of the oslo libraries
                    # where we are moving things out of the namespace
                    # package.
                    pack_name, _sep, mod_name = mod.rpartition('.')
                    if pack_name in sys.modules:
                        the_mod = getattr(sys.modules[pack_name], mod_name,
                                          None)
                        return inspect.ismodule(the_mod)
                    return False
        return True

    def is_module(mod):
        """Checks for non module imports."""
        if mod in modules_cache:
            return modules_cache[mod]
        res = is_module_for_sure(mod)
        modules_cache[mod] = res
        return res

    current_path = os.path.dirname(filename)
    current_mod = os.path.basename(filename)
    if current_mod[-3:] == ".py":
        current_mod = current_mod[:-3]

    split_line = logical_line.split()
    split_line_len = len(split_line)
    if (split_line_len > 1 and split_line[0] in ('import', 'from') and
            not core.is_import_exception(split_line[1])):
        pos = logical_line.find(',')
        if pos != -1:
            if split_line[0] == 'from':
                yield pos, "H301: one import per line"
            return  # ',' is not supported by the H302 checker yet
        pos = logical_line.find('*')
        if pos != -1:
            yield pos, "H303: No wildcard (*) import."
            return

        if split_line_len in (2, 4, 6) and split_line[1] != "__future__":
            if 'from' == split_line[0] and split_line_len > 3:
                mod = '.'.join((split_line[1], split_line[3]))
                if core.is_import_exception(mod):
                    return
                if RE_RELATIVE_IMPORT.search(logical_line):
                    yield logical_line.find('.'), (
                        "H304: No relative imports. '%s' is a relative import"
                        % logical_line)
                    return

                if not is_module(mod):
                    yield 0, ("H302: import only modules."
                              "'%s' does not import a module" % logical_line)
                return

        # NOTE(afazekas): import searches first in the package
        # The import keyword just imports modules
        # The guestfs module now imports guestfs
        mod = split_line[1]
        if (current_mod != mod and not is_module(mod) and
                is_module_for_sure(mod, [current_path])):
            yield 0, ("H304: No relative imports."
                      " '%s' is a relative import" % logical_line)


module_cache = dict()


def _find_module(module, path=None):
    mod_base = module
    parent_path = None
    while '.' in mod_base:
        first, _, mod_base = mod_base.partition('.')
        parent_path = path
        _, path, _ = imp.find_module(first, path)
        path = [path]
    try:
        _, path, _ = imp.find_module(mod_base, path)
    except ImportError:
        # NOTE(bnemec): There are two reasons we might get here: 1) A
        # non-module import and 2) an import of a namespace module that is
        # in the same namespace as the current project, which caused us to
        # recurse into the project namespace but fail to find the third-party
        # module.  For 1), we won't be able to import it as a module, so we
        # return the parent module's path, but for 2) the import below should
        # succeed, so we re-raise the ImportError because the module was
        # legitimately not found in this path.
        try:
            __import__(module)
        except ImportError:
            # Non-module import, return the parent path if we have it
            if parent_path:
                return parent_path
            raise
        raise
    return path


# List of all Python 2 stdlib modules - anything not in this list will be
# allowed in either the stdlib or third-party groups to allow for Python 3
# stdlib additions.
# The list was generated via the following script, which is a variation on
# the one found here:
# http://stackoverflow.com/questions/6463918/how-can-i-get-a-list-of-all-the-python-standard-library-modules
"""
from distutils import sysconfig
import os
import sys

std_lib = sysconfig.get_python_lib(standard_lib=True)
prefix_len = len(std_lib) + 1
modules = ''
line = '['
mod_list = []
for top, dirs, files in os.walk(std_lib):
    for name in files:
        if 'site-packages' not in top:
            if name == '__init__.py':
                full_name = top[prefix_len:].replace('/', '.')
                mod_list.append(full_name)
            elif name.endswith('.py'):
                full_name = top.replace('/', '.') + '.'
                full_name += name[:-3]
                full_name = full_name[prefix_len:]
                mod_list.append(full_name)
            elif name.endswith('.so') and top.endswith('lib-dynload'):
                full_name = name[:-3]
                if full_name.endswith('module'):
                    full_name = full_name[:-6]
                mod_list.append(full_name)
for name in sys.builtin_module_names:
    mod_list.append(name)
mod_list.sort()
for mod in mod_list:
    if len(line + mod) + 8 > 79:
        modules += '\n' + line
        line = '    '
    line += "'%s', " % mod
print modules + ']'
"""
py2_stdlib = [
    'BaseHTTPServer', 'Bastion', 'CGIHTTPServer', 'ConfigParser', 'Cookie',
    'DocXMLRPCServer', 'HTMLParser', 'MimeWriter', 'Queue',
    'SimpleHTTPServer', 'SimpleXMLRPCServer', 'SocketServer', 'StringIO',
    'UserDict', 'UserList', 'UserString', '_LWPCookieJar',
    '_MozillaCookieJar', '__builtin__', '__future__', '__main__',
    '__phello__.foo', '_abcoll', '_ast', '_bisect', '_bsddb', '_codecs',
    '_codecs_cn', '_codecs_hk', '_codecs_iso2022', '_codecs_jp',
    '_codecs_kr', '_codecs_tw', '_collections', '_crypt', '_csv',
    '_ctypes', '_curses', '_curses_panel', '_elementtree', '_functools',
    '_hashlib', '_heapq', '_hotshot', '_io', '_json', '_locale',
    '_lsprof', '_multibytecodec', '_multiprocessing', '_osx_support',
    '_pyio', '_random', '_socket', '_sqlite3', '_sre', '_ssl',
    '_strptime', '_struct', '_symtable', '_sysconfigdata',
    '_threading_local', '_warnings', '_weakref', '_weakrefset', 'abc',
    'aifc', 'antigravity', 'anydbm', 'argparse', 'array', 'ast',
    'asynchat', 'asyncore', 'atexit', 'audiodev', 'audioop', 'base64',
    'bdb', 'binascii', 'binhex', 'bisect', 'bsddb', 'bsddb.db',
    'bsddb.dbobj', 'bsddb.dbrecio', 'bsddb.dbshelve', 'bsddb.dbtables',
    'bsddb.dbutils', 'bz2', 'cPickle', 'cProfile', 'cStringIO',
    'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd', 'code', 'codecs',
    'codeop', 'collections', 'colorsys', 'commands', 'compileall',
    'compiler', 'compiler.ast', 'compiler.consts', 'compiler.future',
    'compiler.misc', 'compiler.pyassem', 'compiler.pycodegen',
    'compiler.symbols', 'compiler.syntax', 'compiler.transformer',
    'compiler.visitor', 'contextlib', 'cookielib', 'copy', 'copy_reg',
    'crypt', 'csv', 'ctypes', 'ctypes._endian', 'ctypes.macholib',
    'ctypes.macholib.dyld', 'ctypes.macholib.dylib',
    'ctypes.macholib.framework', 'ctypes.util', 'ctypes.wintypes',
    'curses', 'curses.ascii', 'curses.has_key', 'curses.panel',
    'curses.textpad', 'curses.wrapper', 'datetime', 'dbhash', 'dbm',
    'decimal', 'difflib', 'dircache', 'dis', 'distutils',
    'distutils.archive_util', 'distutils.bcppcompiler',
    'distutils.ccompiler', 'distutils.cmd', 'distutils.command',
    'distutils.command.bdist', 'distutils.command.bdist_dumb',
    'distutils.command.bdist_msi', 'distutils.command.bdist_rpm',
    'distutils.command.bdist_wininst', 'distutils.command.build',
    'distutils.command.build_clib', 'distutils.command.build_ext',
    'distutils.command.build_py', 'distutils.command.build_scripts',
    'distutils.command.check', 'distutils.command.clean',
    'distutils.command.config', 'distutils.command.install',
    'distutils.command.install_data',
    'distutils.command.install_egg_info',
    'distutils.command.install_headers', 'distutils.command.install_lib',
    'distutils.command.install_scripts', 'distutils.command.register',
    'distutils.command.sdist', 'distutils.command.upload',
    'distutils.config', 'distutils.core', 'distutils.cygwinccompiler',
    'distutils.debug', 'distutils.dep_util', 'distutils.dir_util',
    'distutils.dist', 'distutils.emxccompiler', 'distutils.errors',
    'distutils.extension', 'distutils.fancy_getopt',
    'distutils.file_util', 'distutils.filelist', 'distutils.log',
    'distutils.msvc9compiler', 'distutils.msvccompiler',
    'distutils.spawn', 'distutils.sysconfig', 'distutils.text_file',
    'distutils.unixccompiler', 'distutils.util', 'distutils.version',
    'distutils.versionpredicate', 'dl', 'doctest', 'dumbdbm',
    'dummy_thread', 'dummy_threading', 'email', 'email._parseaddr',
    'email.base64mime', 'email.charset', 'email.encoders', 'email.errors',
    'email.feedparser', 'email.generator', 'email.header',
    'email.iterators', 'email.message', 'email.mime',
    'email.mime.application', 'email.mime.audio', 'email.mime.base',
    'email.mime.image', 'email.mime.message', 'email.mime.multipart',
    'email.mime.nonmultipart', 'email.mime.text', 'email.parser',
    'email.quoprimime', 'email.utils', 'encodings', 'encodings.aliases',
    'encodings.ascii', 'encodings.base64_codec', 'encodings.big5',
    'encodings.big5hkscs', 'encodings.bz2_codec', 'encodings.charmap',
    'encodings.cp037', 'encodings.cp1006', 'encodings.cp1026',
    'encodings.cp1140', 'encodings.cp1250', 'encodings.cp1251',
    'encodings.cp1252', 'encodings.cp1253', 'encodings.cp1254',
    'encodings.cp1255', 'encodings.cp1256', 'encodings.cp1257',
    'encodings.cp1258', 'encodings.cp424', 'encodings.cp437',
    'encodings.cp500', 'encodings.cp720', 'encodings.cp737',
    'encodings.cp775', 'encodings.cp850', 'encodings.cp852',
    'encodings.cp855', 'encodings.cp856', 'encodings.cp857',
    'encodings.cp858', 'encodings.cp860', 'encodings.cp861',
    'encodings.cp862', 'encodings.cp863', 'encodings.cp864',
    'encodings.cp865', 'encodings.cp866', 'encodings.cp869',
    'encodings.cp874', 'encodings.cp875', 'encodings.cp932',
    'encodings.cp949', 'encodings.cp950', 'encodings.euc_jis_2004',
    'encodings.euc_jisx0213', 'encodings.euc_jp', 'encodings.euc_kr',
    'encodings.gb18030', 'encodings.gb2312', 'encodings.gbk',
    'encodings.hex_codec', 'encodings.hp_roman8', 'encodings.hz',
    'encodings.idna', 'encodings.iso2022_jp', 'encodings.iso2022_jp_1',
    'encodings.iso2022_jp_2', 'encodings.iso2022_jp_2004',
    'encodings.iso2022_jp_3', 'encodings.iso2022_jp_ext',
    'encodings.iso2022_kr', 'encodings.iso8859_1', 'encodings.iso8859_10',
    'encodings.iso8859_11', 'encodings.iso8859_13',
    'encodings.iso8859_14', 'encodings.iso8859_15',
    'encodings.iso8859_16', 'encodings.iso8859_2', 'encodings.iso8859_3',
    'encodings.iso8859_4', 'encodings.iso8859_5', 'encodings.iso8859_6',
    'encodings.iso8859_7', 'encodings.iso8859_8', 'encodings.iso8859_9',
    'encodings.johab', 'encodings.koi8_r', 'encodings.koi8_u',
    'encodings.latin_1', 'encodings.mac_arabic', 'encodings.mac_centeuro',
    'encodings.mac_croatian', 'encodings.mac_cyrillic',
    'encodings.mac_farsi', 'encodings.mac_greek', 'encodings.mac_iceland',
    'encodings.mac_latin2', 'encodings.mac_roman',
    'encodings.mac_romanian', 'encodings.mac_turkish', 'encodings.mbcs',
    'encodings.palmos', 'encodings.ptcp154', 'encodings.punycode',
    'encodings.quopri_codec', 'encodings.raw_unicode_escape',
    'encodings.rot_13', 'encodings.shift_jis', 'encodings.shift_jis_2004',
    'encodings.shift_jisx0213', 'encodings.string_escape',
    'encodings.tis_620', 'encodings.undefined',
    'encodings.unicode_escape', 'encodings.unicode_internal',
    'encodings.utf_16', 'encodings.utf_16_be', 'encodings.utf_16_le',
    'encodings.utf_32', 'encodings.utf_32_be', 'encodings.utf_32_le',
    'encodings.utf_7', 'encodings.utf_8', 'encodings.utf_8_sig',
    'encodings.uu_codec', 'encodings.zlib_codec', 'errno', 'exceptions',
    'fcntl', 'filecmp', 'fileinput', 'fnmatch', 'formatter', 'fpformat',
    'fractions', 'ftplib', 'functools', 'future_builtins', 'gc', 'gdbm',
    'genericpath', 'getopt', 'getpass', 'gettext', 'glob', 'grp', 'gzip',
    'hashlib', 'heapq', 'hmac', 'hotshot', 'hotshot.log', 'hotshot.stats',
    'hotshot.stones', 'htmlentitydefs', 'htmllib', 'httplib', 'idlelib',
    'idlelib.AutoComplete', 'idlelib.AutoCompleteWindow',
    'idlelib.AutoExpand', 'idlelib.Bindings', 'idlelib.CallTipWindow',
    'idlelib.CallTips', 'idlelib.ClassBrowser', 'idlelib.CodeContext',
    'idlelib.ColorDelegator', 'idlelib.Debugger', 'idlelib.Delegator',
    'idlelib.EditorWindow', 'idlelib.FileList', 'idlelib.FormatParagraph',
    'idlelib.GrepDialog', 'idlelib.HyperParser', 'idlelib.IOBinding',
    'idlelib.IdleHistory', 'idlelib.MultiCall', 'idlelib.MultiStatusBar',
    'idlelib.ObjectBrowser', 'idlelib.OutputWindow', 'idlelib.ParenMatch',
    'idlelib.PathBrowser', 'idlelib.Percolator', 'idlelib.PyParse',
    'idlelib.PyShell', 'idlelib.RemoteDebugger',
    'idlelib.RemoteObjectBrowser', 'idlelib.ReplaceDialog',
    'idlelib.RstripExtension', 'idlelib.ScriptBinding',
    'idlelib.ScrolledList', 'idlelib.SearchDialog',
    'idlelib.SearchDialogBase', 'idlelib.SearchEngine',
    'idlelib.StackViewer', 'idlelib.ToolTip', 'idlelib.TreeWidget',
    'idlelib.UndoDelegator', 'idlelib.WidgetRedirector',
    'idlelib.WindowList', 'idlelib.ZoomHeight', 'idlelib.aboutDialog',
    'idlelib.configDialog', 'idlelib.configHandler',
    'idlelib.configHelpSourceEdit', 'idlelib.configSectionNameDialog',
    'idlelib.dynOptionMenuWidget', 'idlelib.idle', 'idlelib.idlever',
    'idlelib.keybindingDialog', 'idlelib.macosxSupport', 'idlelib.rpc',
    'idlelib.run', 'idlelib.tabbedpages', 'idlelib.textView', 'ihooks',
    'imageop', 'imaplib', 'imghdr', 'imp', 'importlib', 'imputil',
    'inspect', 'io', 'itertools', 'json', 'json.decoder', 'json.encoder',
    'json.scanner', 'json.tool', 'keyword', 'lib2to3', 'lib2to3.__main__',
    'lib2to3.btm_matcher', 'lib2to3.btm_utils', 'lib2to3.fixer_base',
    'lib2to3.fixer_util', 'lib2to3.fixes', 'lib2to3.fixes.fix_apply',
    'lib2to3.fixes.fix_basestring', 'lib2to3.fixes.fix_buffer',
    'lib2to3.fixes.fix_callable', 'lib2to3.fixes.fix_dict',
    'lib2to3.fixes.fix_except', 'lib2to3.fixes.fix_exec',
    'lib2to3.fixes.fix_execfile', 'lib2to3.fixes.fix_exitfunc',
    'lib2to3.fixes.fix_filter', 'lib2to3.fixes.fix_funcattrs',
    'lib2to3.fixes.fix_future', 'lib2to3.fixes.fix_getcwdu',
    'lib2to3.fixes.fix_has_key', 'lib2to3.fixes.fix_idioms',
    'lib2to3.fixes.fix_import', 'lib2to3.fixes.fix_imports',
    'lib2to3.fixes.fix_imports2', 'lib2to3.fixes.fix_input',
    'lib2to3.fixes.fix_intern', 'lib2to3.fixes.fix_isinstance',
    'lib2to3.fixes.fix_itertools', 'lib2to3.fixes.fix_itertools_imports',
    'lib2to3.fixes.fix_long', 'lib2to3.fixes.fix_map',
    'lib2to3.fixes.fix_metaclass', 'lib2to3.fixes.fix_methodattrs',
    'lib2to3.fixes.fix_ne', 'lib2to3.fixes.fix_next',
    'lib2to3.fixes.fix_nonzero', 'lib2to3.fixes.fix_numliterals',
    'lib2to3.fixes.fix_operator', 'lib2to3.fixes.fix_paren',
    'lib2to3.fixes.fix_print', 'lib2to3.fixes.fix_raise',
    'lib2to3.fixes.fix_raw_input', 'lib2to3.fixes.fix_reduce',
    'lib2to3.fixes.fix_renames', 'lib2to3.fixes.fix_repr',
    'lib2to3.fixes.fix_set_literal', 'lib2to3.fixes.fix_standarderror',
    'lib2to3.fixes.fix_sys_exc', 'lib2to3.fixes.fix_throw',
    'lib2to3.fixes.fix_tuple_params', 'lib2to3.fixes.fix_types',
    'lib2to3.fixes.fix_unicode', 'lib2to3.fixes.fix_urllib',
    'lib2to3.fixes.fix_ws_comma', 'lib2to3.fixes.fix_xrange',
    'lib2to3.fixes.fix_xreadlines', 'lib2to3.fixes.fix_zip',
    'lib2to3.main', 'lib2to3.patcomp', 'lib2to3.pgen2',
    'lib2to3.pgen2.conv', 'lib2to3.pgen2.driver', 'lib2to3.pgen2.grammar',
    'lib2to3.pgen2.literals', 'lib2to3.pgen2.parse', 'lib2to3.pgen2.pgen',
    'lib2to3.pgen2.token', 'lib2to3.pgen2.tokenize', 'lib2to3.pygram',
    'lib2to3.pytree', 'lib2to3.refactor', 'linecache', 'linuxaudiodev',
    'locale', 'logging', 'logging.config', 'logging.handlers', 'macpath',
    'macurl2path', 'mailbox', 'mailcap', 'markupbase', 'marshal', 'math',
    'md5', 'mhlib', 'mimetools', 'mimetypes', 'mimify', 'mmap',
    'modulefinder', 'multifile', 'multiprocessing',
    'multiprocessing.connection', 'multiprocessing.dummy',
    'multiprocessing.dummy.connection', 'multiprocessing.forking',
    'multiprocessing.heap', 'multiprocessing.managers',
    'multiprocessing.pool', 'multiprocessing.process',
    'multiprocessing.queues', 'multiprocessing.reduction',
    'multiprocessing.sharedctypes', 'multiprocessing.synchronize',
    'multiprocessing.util', 'mutex', 'netrc', 'new', 'nis', 'nntplib',
    'ntpath', 'nturl2path', 'numbers', 'opcode', 'operator', 'optparse',
    'os', 'os2emxpath', 'ossaudiodev', 'parser', 'pdb', 'pickle',
    'pickletools', 'pipes', 'pkgutil', 'plat-linux2.CDROM',
    'plat-linux2.DLFCN', 'plat-linux2.IN', 'plat-linux2.TYPES',
    'platform', 'plistlib', 'popen2', 'poplib', 'posix', 'posixfile',
    'posixpath', 'pprint', 'profile', 'pstats', 'pty', 'pwd',
    'py_compile', 'pyclbr', 'pydoc', 'pydoc_data', 'pydoc_data.topics',
    'pyexpat', 'quopri', 'random', 're', 'readline', 'repr', 'resource',
    'rexec', 'rfc822', 'rlcompleter', 'robotparser', 'runpy', 'sched',
    'select', 'sets', 'sgmllib', 'sha', 'shelve', 'shlex', 'shutil',
    'signal', 'site', 'smtpd', 'smtplib', 'sndhdr', 'socket', 'spwd',
    'sqlite3', 'sqlite3.dbapi2', 'sqlite3.dump', 'sre', 'sre_compile',
    'sre_constants', 'sre_parse', 'ssl', 'stat', 'statvfs', 'string',
    'stringold', 'stringprep', 'strop', 'struct', 'subprocess', 'sunau',
    'sunaudio', 'symbol', 'symtable', 'sys', 'sysconfig', 'syslog',
    'tabnanny', 'tarfile', 'telnetlib', 'tempfile', 'termios', 'test',
    'test.test_support', 'textwrap', 'this', 'thread', 'threading',
    'time', 'timeit', 'timing', 'toaiff', 'token', 'tokenize', 'trace',
    'traceback', 'tty', 'types', 'unicodedata', 'unittest',
    'unittest.__main__', 'unittest.case', 'unittest.loader',
    'unittest.main', 'unittest.result', 'unittest.runner',
    'unittest.signals', 'unittest.suite', 'unittest.test',
    'unittest.test.dummy', 'unittest.test.support',
    'unittest.test.test_assertions', 'unittest.test.test_break',
    'unittest.test.test_case', 'unittest.test.test_discovery',
    'unittest.test.test_functiontestcase', 'unittest.test.test_loader',
    'unittest.test.test_program', 'unittest.test.test_result',
    'unittest.test.test_runner', 'unittest.test.test_setups',
    'unittest.test.test_skipping', 'unittest.test.test_suite',
    'unittest.util', 'urllib', 'urllib2', 'urlparse', 'user', 'uu',
    'uuid', 'warnings', 'wave', 'weakref', 'webbrowser', 'whichdb',
    'wsgiref', 'wsgiref.handlers', 'wsgiref.headers',
    'wsgiref.simple_server', 'wsgiref.util', 'wsgiref.validate', 'xdrlib',
    'xml', 'xml.dom', 'xml.dom.NodeFilter', 'xml.dom.domreg',
    'xml.dom.expatbuilder', 'xml.dom.minicompat', 'xml.dom.minidom',
    'xml.dom.pulldom', 'xml.dom.xmlbuilder', 'xml.etree',
    'xml.etree.ElementInclude', 'xml.etree.ElementPath',
    'xml.etree.ElementTree', 'xml.etree.cElementTree', 'xml.parsers',
    'xml.parsers.expat', 'xml.sax', 'xml.sax._exceptions',
    'xml.sax.expatreader', 'xml.sax.handler', 'xml.sax.saxutils',
    'xml.sax.xmlreader', 'xmllib', 'xmlrpclib', 'xxsubtype', 'zipfile', ]
# Dynamic modules that can't be auto-discovered by the script above
manual_stdlib = ['os.path', ]
py2_stdlib.extend(manual_stdlib)


def _get_import_type(module):
    if module in module_cache:
        return module_cache[module]

    def cache_type(module_type):
        module_cache[module] = module_type
        return module_type

    # Check static stdlib list
    if module in py2_stdlib:
        return cache_type('stdlib')

    # Check if the module is local
    try:
        _find_module(module, ['.'])
        # If the previous line succeeded then it must be a project module
        return cache_type('project')
    except ImportError:
        pass

    # Otherwise treat it as third-party - this means we may treat some stdlib
    # modules as third-party, but that's okay because we are allowing
    # third-party libs in the stdlib section.
    return cache_type('third-party')


@core.flake8ext
def hacking_import_groups(logical_line, blank_before, previous_logical,
                          indent_level, previous_indent_level, physical_line,
                          noqa):
    r"""Check that imports are grouped correctly.

    OpenStack HACKING guide recommendation for imports:
    imports grouped such that Python standard library imports are together,
    third party library imports are together, and project imports are
    together

    This check allows mixing of third-party and stdlib modules so we don't
    fail on new Python 3 stdlib modules that used to be third-party.

    Okay: import os\nimport sys\n\nimport six\n\nimport hacking
    Okay: import six\nimport znon_existent_package
    Okay: import os\nimport threading
    Okay: import mock\nimport os
    H305: import hacking\nimport os
    H305: import hacking\nimport nonexistent
    H305: import hacking\nimport mock
    """
    if (noqa or blank_before > 0 or
            indent_level != previous_indent_level):
        return

    normalized_line = core.import_normalize(logical_line.strip()).split()
    normalized_previous = core.import_normalize(previous_logical.
                                                strip()).split()

    def compatible(previous, current):
        if previous == current:
            return True
        if ((previous in ['stdlib', 'third-party']) and
                (current in ['stdlib', 'third-party'])):
            return True
        return False

    if normalized_line and normalized_line[0] == 'import':
        current_type = _get_import_type(normalized_line[1])
        if normalized_previous and normalized_previous[0] == 'import':
            previous_type = _get_import_type(normalized_previous[1])
            if not compatible(previous_type, current_type):
                yield(0, 'H305: imports not grouped correctly '
                      '(%s: %s, %s: %s)' %
                      (normalized_previous[1], previous_type,
                       normalized_line[1], current_type))


@core.flake8ext
def hacking_import_alphabetical(logical_line, blank_before, previous_logical,
                                indent_level, previous_indent_level):
    r"""Check for imports in alphabetical order.

    OpenStack HACKING guide recommendation for imports:
    imports in human alphabetical order

    Okay: import os\nimport sys\n\nimport nova\nfrom nova import test
    Okay: import os\nimport sys
    H306: import sys\nimport os
    Okay: import sys\n\n# foo\nimport six
    """
    # handle import x
    # use .lower since capitalization shouldn't dictate order
    if blank_before < 1 and indent_level == previous_indent_level:
        split_line = core.import_normalize(logical_line.
                                           strip()).lower().split()
        split_previous = core.import_normalize(previous_logical.
                                               strip()).lower().split()
        length = [2, 4]
        if (len(split_line) in length and len(split_previous) in length and
                split_line[0] == "import" and split_previous[0] == "import"):
            if split_line[1] < split_previous[1]:
                yield (0, "H306: imports not in alphabetical order (%s, %s)"
                       % (split_previous[1], split_line[1]))


class ImportGroupData(object):
    """A class to hold persistent state data for import group checks.

    To verify import grouping, it is necessary to know the current group
    for the current file.  This can not always be known solely from the
    current and previous line, so this class can be used to keep track.
    """

    # NOTE(bnemec): *args is needed because the test code tries to run this
    # as a flake8 check and passes an argument to it.
    def __init__(self, *args):
        self.current_group = None
        self.current_filename = None
        self.current_import = None


together_data = ImportGroupData()


@core.flake8ext
def hacking_import_groups_together(logical_line, blank_lines, indent_level,
                                   previous_indent_level, line_number,
                                   physical_line, filename, noqa):
    r"""Check that like imports are grouped together.

    OpenStack HACKING guide recommendation for imports:
    Imports should be grouped together by type.

    This check allows mixing of third-party libs into the stdlib group in
    order to accomodate new Python 3 stdlib modules.

    Okay: import os\nimport sys
    Okay: try:\n    import foo\nexcept ImportError:\n    pass\n\nimport six
    Okay: import mock\n\nimport six
    Okay: import abc\nimport mock\n\nimport six
    Okay: import eventlet\neventlet.monkey_patch()\n\nimport copy
    H307: import os\n\nimport sys
    H307: import mock\nimport os\n\nimport sys
    """
    if line_number == 1 or filename != together_data.current_filename:
        together_data.current_group = None
    together_data.current_filename = filename

    if noqa:
        return

    def update_current_group(current):
        if together_data.current_group is None:
            if current in ['stdlib', 'third-party']:
                # Assume stdlib until we know otherwise
                together_data.current_group = 'stdlib'
                return
        if (together_data.current_group == 'stdlib' and
                current == 'third-party' and blank_lines < 1):
            # Keep the current group stdlib, since there may be third-party
            # libs in that group
            return
        together_data.current_group = current

    normalized_line = core.import_normalize(logical_line.strip()).split()
    if normalized_line:
        if normalized_line[0] == 'import':
            current_type = _get_import_type(normalized_line[1])
            previous_import = together_data.current_import
            together_data.current_import = normalized_line[1]
            matched = current_type == together_data.current_group
            update_current_group(current_type)
            if (matched and indent_level == previous_indent_level and
                    blank_lines >= 1):
                yield(0, 'H307: like imports should be grouped together (%s '
                      'and %s from %s are separated by whitespace)' %
                      (previous_import,
                       together_data.current_import,
                       current_type))
        else:
            # Reset on non-import code
            together_data.current_group = None
