#!/usr/bin/env python3
"""Fix missing imports across GAM — incremental, validated approach.

For each module with missing names:
1. Determine the canonical source module for each missing name
2. Add the import
3. Actually try to import the module to verify no circular dependency
4. If it fails, revert and mark as needing manual resolution
"""
import ast
import sys
import dis
import types
import builtins
import importlib
import subprocess
from pathlib import Path
from collections import defaultdict

SRC = Path('src')
GAM = SRC / 'gam'
builtin_names = set(dir(builtins))

# ── Canonical source for every missing name ──────────────────────────────
SOURCES = {
    # stdlib / third-party  (value is just the import statement)
    'arrow': ('import arrow', None),
    'google': ('import google', None),
    'httplib2': ('import httplib2', None),
    'json': ('import json', None),
    'random': ('import random', None),

    # gam.util.access
    'accessErrorExit': (None, 'gam.util.access'),
    'accessErrorExitNonDirectory': (None, 'gam.util.access'),
    'checkEntityDNEorAccessErrorExit': (None, 'gam.util.access'),
    'entityOrEntityUnknownWarning': (None, 'gam.util.access'),
    'entityUnknownWarning': (None, 'gam.util.access'),

    # gam.util.api
    'ClientAPIAccessDeniedExit': (None, 'gam.util.api'),

    # gam.util.api_call
    'callGAPIpages': (None, 'gam.util.api_call'),

    # gam.util.args
    'getCharacter': (None, 'gam.util.args'),
    'getString': (None, 'gam.util.args'),
    'normalizeEmailAddressOrUID': (None, 'gam.util.args'),
    'todaysTime': (None, 'gam.util.args'),
    'unescapeCRsNLs': (None, 'gam.util.args'),
    'ISOformatTimeStamp': (None, 'gam.util.args'),

    # gam.util.batch
    'RI_J': (None, 'gam.util.batch'),

    # gam.util.csv_pf
    'RowFilterMatch': (None, 'gam.util.csv_pf'),
    'cleanJSON': (None, 'gam.util.csv_pf'),
    'flattenJSON': (None, 'gam.util.csv_pf'),
    'showJSON': (None, 'gam.util.csv_pf'),

    # gam.util.display
    'entityActionNotPerformedWarning': (None, 'gam.util.display'),
    'entityPerformActionNumItems': (None, 'gam.util.display'),
    'printEntity': (None, 'gam.util.display'),
    'printEntityKVList': (None, 'gam.util.display'),
    'printGettingEntityItemForWhom': (None, 'gam.util.display'),
    'printLine': (None, 'gam.util.display'),
    'userYouTubeServiceNotEnabledWarning': (None, 'gam.util.display'),

    # gam.util.entity
    'checkUserSuspended': (None, 'gam.util.entity'),
    'convertGroupCloudIDToEmail': (None, 'gam.util.entity'),
    'convertOrgUnitIDtoPath': (None, 'gam.util.entity'),
    'convertUserIDtoEmail': (None, 'gam.util.entity'),
    'getEntityArgument': (None, 'gam.util.entity'),
    '_getCoursesOwnerInfo': (None, 'gam.cmd.courses.courses'),
    'doPrintLicenses': (None, 'gam.cmd.licenses'),

    # gam.util.errors
    'formatChoiceList': (None, 'gam.util.errors'),
    'unknownArgumentExit': (None, 'gam.util.errors'),
    'usageErrorExit': (None, 'gam.util.errors'),

    # gam.util.fileio
    'cleanFilename': (None, 'gam.util.fileio'),
    'UNKNOWN': (None, 'gam.util.fileio'),

    # gam.util.gdoc
    'getGDocData': (None, 'gam.util.gdoc'),
    'getStorageFileData': (None, 'gam.util.gdoc'),

    # gam.util.output
    '_stripControlCharsFromName': (None, 'gam.util.output'),
    'formatKeyValueList': (None, 'gam.util.output'),
    'formatLocalTimestamp': (None, 'gam.util.output'),
    'setSysExitRC': (None, 'gam.util.output'),

    # gam.util.svcacct
    'buildGAPIServiceObject': (None, 'gam.util.svcacct'),

    # gam.constants
    'NO_ENTITIES_FOUND_RC': (None, 'gam.constants'),
    'MIMETYPE_GA_SPREADSHEET': (None, 'gam.constants'),

    # gam.cmd.courses.courses
    '_convertCourseUserIdToEmailName': (None, 'gam.cmd.courses.courses'),
    '_courseItemPassesFilter': (None, 'gam.cmd.courses.courses'),
    '_getCourseAliasesMembers': (None, 'gam.cmd.courses.courses'),
    '_getCourseItemFilter': (None, 'gam.cmd.courses.courses'),
    '_getCourseOwnerSA': (None, 'gam.cmd.courses.courses'),
    '_getCourseSelectionParameters': (None, 'gam.cmd.courses.courses'),
    '_getCourseStates': (None, 'gam.cmd.courses.courses'),
    '_getCoursesInfo': (None, 'gam.cmd.courses.courses'),
    '_getCoursesOwnerInfo': (None, 'gam.cmd.courses.courses'),
    '_gettingCourseEntityQuery': (None, 'gam.cmd.courses.courses'),
    '_initCourseItemFilter': (None, 'gam.cmd.courses.courses'),
    '_initCourseSelectionParameters': (None, 'gam.cmd.courses.courses'),
    '_initCourseShowProperties': (None, 'gam.cmd.courses.courses'),
    '_printCourseItemCount': (None, 'gam.cmd.courses.courses'),
    '_setApplyCourseItemFilter': (None, 'gam.cmd.courses.courses'),
    'COURSE_ANNOUNCEMENTS_FIELDS_CHOICE_MAP': (None, 'gam.cmd.courses.courses'),
    'COURSE_ANNOUNCEMENTS_INDEXED_TITLES': (None, 'gam.cmd.courses.courses'),
    'COURSE_ANNOUNCEMENTS_ORDERBY_CHOICE_MAP': (None, 'gam.cmd.courses.courses'),
    'COURSE_ANNOUNCEMENTS_SORT_TITLES': (None, 'gam.cmd.courses.courses'),
    'COURSE_ANNOUNCEMENTS_TIME_OBJECTS': (None, 'gam.cmd.courses.courses'),
    'COURSE_CUS_FILTER_FIELDS_MAP': (None, 'gam.cmd.courses.courses'),
    'COURSE_CU_FILTER_FIELDS_MAP': (None, 'gam.cmd.courses.courses'),
    'COURSE_U_FILTER_FIELDS_MAP': (None, 'gam.cmd.courses.courses'),
    'COURSE_MEMBER_ARGUMENTS': (None, 'gam.cmd.courses.courses'),

    # gam.cmd.courses.content
    'COURSE_PARTICIPANTS_SORT_TITLES': (None, 'gam.cmd.courses.content'),

    # gam.cmd.cros.print
    'CROS_END_ARGUMENTS': (None, 'gam.cmd.cros.print'),
    'CROS_START_ARGUMENTS': (None, 'gam.cmd.cros.print'),

    # gam.cmd.drive.core
    '_getDriveFileParentInfo': (None, 'gam.cmd.drive.core'),
    '_getSharedDriveNameFromId': (None, 'gam.cmd.drive.core'),
    '_mapDrive2QueryToDrive3': (None, 'gam.cmd.drive.core'),
    '_validateUserGetFileIDs': (None, 'gam.cmd.drive.core'),
    'escapeDriveFileName': (None, 'gam.cmd.drive.core'),
    'getDriveFileCopyAttribute': (None, 'gam.cmd.drive.core'),
    'getDriveFileEntity': (None, 'gam.cmd.drive.core'),
    'getDriveFileParentAttribute': (None, 'gam.cmd.drive.core'),
    'getEscapedDriveFileName': (None, 'gam.cmd.drive.core'),
    'initDriveFileAttributes': (None, 'gam.cmd.drive.core'),
    'initDriveFileEntity': (None, 'gam.cmd.drive.core'),

    # gam.cmd.drive.filepaths
    'DRIVEFILE_BASIC_PERMISSION_FIELDS': (None, 'gam.cmd.drive.filepaths'),
    'DRIVEFILE_ORDERBY_CHOICE_MAP': (None, 'gam.cmd.drive.filepaths'),
    'DRIVE_PERMISSIONS_SUBFIELDS_CHOICE_MAP': (None, 'gam.cmd.drive.filepaths'),
    'addFilePathsToRow': (None, 'gam.cmd.drive.filepaths'),
    'initFilePathInfo': (None, 'gam.cmd.drive.filepaths'),

    # gam.cmd.drive.filetree
    'DRIVEFILE_ACL_ROLES_MAP': (None, 'gam.cmd.drive.filetree'),
    'DriveListParameters': (None, 'gam.cmd.drive.filetree'),
    'MimeTypeCheck': (None, 'gam.cmd.drive.filetree'),
    'PermissionMatch': (None, 'gam.cmd.drive.filetree'),
    'buildFileTree': (None, 'gam.cmd.drive.filetree'),

    # gam.cmd.drive.files
    'STAT_FILE_COPIED_MOVED': (None, 'gam.cmd.drive.files'),
    'STAT_FILE_DUPLICATE': (None, 'gam.cmd.drive.files'),
    'STAT_FILE_FAILED': (None, 'gam.cmd.drive.files'),
    'STAT_FILE_IN_SKIPIDS': (None, 'gam.cmd.drive.files'),
    'STAT_FILE_NOT_COPYABLE_MOVABLE': (None, 'gam.cmd.drive.files'),
    'STAT_FILE_PERMISSIONS_FAILED': (None, 'gam.cmd.drive.files'),
    'STAT_FILE_PROTECTEDRANGES_FAILED': (None, 'gam.cmd.drive.files'),
    'STAT_FILE_SHORTCUT_CREATED': (None, 'gam.cmd.drive.files'),
    'STAT_FILE_SHORTCUT_EXISTS': (None, 'gam.cmd.drive.files'),
    'STAT_FILE_TOTAL': (None, 'gam.cmd.drive.files'),
    'STAT_FOLDER_COPIED_MOVED': (None, 'gam.cmd.drive.files'),
    'STAT_FOLDER_DUPLICATE': (None, 'gam.cmd.drive.files'),
    'STAT_FOLDER_FAILED': (None, 'gam.cmd.drive.files'),
    'STAT_FOLDER_MERGED': (None, 'gam.cmd.drive.files'),
    'STAT_FOLDER_NOT_WRITABLE': (None, 'gam.cmd.drive.files'),
    'STAT_FOLDER_PERMISSIONS_FAILED': (None, 'gam.cmd.drive.files'),
    'STAT_FOLDER_SHORTCUT_CREATED': (None, 'gam.cmd.drive.files'),
    'STAT_FOLDER_SHORTCUT_EXISTS': (None, 'gam.cmd.drive.files'),
    'STAT_FOLDER_TOTAL': (None, 'gam.cmd.drive.files'),
    'STAT_USER_NOT_ORGANIZER': (None, 'gam.cmd.drive.files'),
    '_incrStatistic': (None, 'gam.cmd.drive.files'),
    '_initStatistics': (None, 'gam.cmd.drive.files'),
    'processFilenameReplacements': (None, 'gam.cmd.drive.files'),

    # gam.cmd.drive.transfer.fileops
    'HTTP_ERROR_PATTERN': (None, 'gam.cmd.drive.transfer.fileops'),
    'MICROSOFT_FORMATS_LIST': (None, 'gam.cmd.drive.transfer.fileops'),
    'MIMETYPE_EXTENSION_MAP': (None, 'gam.cmd.drive.transfer.fileops'),
    'TRANSFER_DRIVEFILE_ACL_ROLES_MAP': (None, 'gam.cmd.drive.transfer.fileops'),

    # gam.cmd.drive.copymove.copymove_util
    '_checkForExistingShortcut': (None, 'gam.cmd.drive.copymove.copymove_util'),
    'COPY_NONINHERITED_PERMISSIONS_ALWAYS': (None, 'gam.cmd.drive.copymove.copymove_util'),
    'COPY_NONINHERITED_PERMISSIONS_SYNC_ALL_FOLDERS': (None, 'gam.cmd.drive.copymove.copymove_util'),
    '_copyPermissions': (None, 'gam.cmd.drive.copymove.copymove_util'),
    '_updateSheetProtectedRangesACLchange': (None, 'gam.cmd.drive.copymove.copymove_util'),
    'DEST_PARENT_SHAREDDRIVE_ROOT': (None, 'gam.cmd.drive.copymove.copymove_util'),
    'getCopyMoveOptions': (None, 'gam.cmd.drive.copymove.copymove_util'),
    'initCopyMoveOptions': (None, 'gam.cmd.drive.copymove.copymove_util'),

    # gam.cmd.drive.transfer.ownership
    'getPermissionIdForEmail': (None, 'gam.cmd.drive.transfer.ownership'),

    # gam.cmd.licenses
    'doPrintLicenses': (None, 'gam.cmd.licenses'),

    # gam.cmd.reseller
    'ANALYTIC_ENTITY_MAP': (None, 'gam.cmd.reseller'),

    # gam.cmd.users.display
    'USER_NAME_PROPERTY_PRINT_ORDER': (None, 'gam.cmd.users.display'),

    # gam.cmd.oauth
    'Credentials': (None, 'gam.cmd.oauth'),
}


def get_global_loads(code_obj):
    names = set()
    for instr in dis.get_instructions(code_obj):
        if instr.opname in ('LOAD_GLOBAL', 'LOAD_GLOBAL_AND_NULL', 'LOAD_GLOBAL_MORPH'):
            names.add(instr.argval)
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            names.update(get_global_loads(const))
    return names


def find_missing_per_module():
    """Find all missing globals per module."""
    sys.path.insert(0, str(SRC))
    missing = defaultdict(set)
    for fp in sorted(GAM.rglob('*.py')):
        if '__pycache__' in str(fp) or fp.name == '__init__.py':
            continue
        rel = fp.relative_to(SRC)
        mod_name = '.'.join(rel.parts)[:-3]
        try:
            mod = importlib.import_module(mod_name)
        except:
            continue
        mod_globals = set(dir(mod))
        for attr_name in dir(mod):
            obj = getattr(mod, attr_name)
            if not isinstance(obj, types.FunctionType) or obj.__module__ != mod.__name__:
                continue
            for ref in get_global_loads(obj.__code__):
                if ref not in mod_globals and ref not in builtin_names:
                    missing[mod_name].add(ref)
    return missing


def validate_import(filepath):
    """Actually try importing the module in a subprocess to detect cycles."""
    rel = filepath.relative_to(SRC)
    mod_name = '.'.join(rel.parts)[:-3]
    result = subprocess.run(
        [sys.executable, '-c', f'import sys; sys.path.insert(0,"src"); import {mod_name}'],
        capture_output=True, text=True, timeout=10
    )
    return result.returncode == 0, result.stderr


def build_import_line(source_mod, names):
    sorted_names = sorted(names)
    line = f"from {source_mod} import {', '.join(sorted_names)}"
    if len(line) > 100:
        items = ',\n    '.join(sorted_names)
        line = f"from {source_mod} import (\n    {items},\n)"
    return line


def add_imports_to_file(filepath, imports_by_source, stdlib_imports):
    """Add imports to file, returns the new content (doesn't write)."""
    source = filepath.read_text(encoding='utf-8')

    # Check what's already imported
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    existing_names = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                existing_names.add(alias.asname or alias.name)

    new_lines = []

    # Stdlib imports
    for name in sorted(stdlib_imports):
        if name not in existing_names:
            new_lines.append(f'import {name}')

    # From imports
    for source_mod in sorted(imports_by_source):
        names_to_add = imports_by_source[source_mod] - existing_names
        if names_to_add:
            new_lines.append(build_import_line(source_mod, names_to_add))

    if not new_lines:
        return None

    # Find last top-level import line
    last_import_line = 0
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            last_import_line = node.end_lineno

    lines = source.split('\n')
    insert_text = '\n'.join(new_lines)
    lines.insert(last_import_line, insert_text)

    return '\n'.join(lines)


def main():
    missing = find_missing_per_module()

    # Plan: group by file
    plan = defaultdict(lambda: {'from': defaultdict(set), 'stdlib': set()})
    unmapped = defaultdict(set)

    for consumer_mod, names in sorted(missing.items()):
        for name in sorted(names):
            if name not in SOURCES:
                unmapped[consumer_mod].add(name)
                continue
            stmt, source_mod = SOURCES[name]
            if stmt:  # stdlib
                plan[consumer_mod]['stdlib'].add(name)
            else:
                if source_mod == consumer_mod:
                    continue
                plan[consumer_mod]['from'][source_mod].add(name)

    # Apply file by file, validate each one
    fixed = 0
    failed = []

    for consumer_mod in sorted(plan):
        fp = SRC / consumer_mod.replace('.', '/')
        if fp.is_dir():
            fp = fp / '__init__.py'
        else:
            fp = fp.with_suffix('.py')
        if not fp.exists():
            continue

        original = fp.read_text(encoding='utf-8')
        info = plan[consumer_mod]

        new_content = add_imports_to_file(fp, info['from'], info['stdlib'])
        if new_content is None:
            continue

        # Write and validate
        fp.write_text(new_content, encoding='utf-8')
        ok, err = validate_import(fp)

        if ok:
            fixed += 1
            rel = str(fp.relative_to(SRC))
            total_new = len(info['stdlib']) + sum(len(v) for v in info['from'].values())
            print(f'  ✓ {rel}: +{total_new} imports')
            for s in sorted(info['stdlib']):
                print(f'      import {s}')
            for src, names in sorted(info['from'].items()):
                print(f'      from {src} import {", ".join(sorted(names))}')
        else:
            # Revert!
            fp.write_text(original, encoding='utf-8')
            # Try individual imports to find which ones are safe
            safe_from = defaultdict(set)
            safe_stdlib = set()
            cycle_names = []

            # Test stdlib individually
            for name in sorted(info['stdlib']):
                test_info = {'from': defaultdict(set), 'stdlib': {name}}
                test_content = add_imports_to_file(fp, test_info['from'], test_info['stdlib'])
                if test_content:
                    fp.write_text(test_content, encoding='utf-8')
                    ok2, _ = validate_import(fp)
                    fp.write_text(original, encoding='utf-8')
                    if ok2:
                        safe_stdlib.add(name)
                    else:
                        cycle_names.append(name)

            # Test from-imports by source module
            for src, names in sorted(info['from'].items()):
                test_info = {'from': {src: names}, 'stdlib': set()}
                test_content = add_imports_to_file(fp, test_info['from'], test_info['stdlib'])
                if test_content:
                    fp.write_text(test_content, encoding='utf-8')
                    ok2, err2 = validate_import(fp)
                    fp.write_text(original, encoding='utf-8')
                    if ok2:
                        safe_from[src] = names
                    else:
                        cycle_names.extend(sorted(names))

            # Apply safe subset
            if safe_from or safe_stdlib:
                new_content2 = add_imports_to_file(fp, safe_from, safe_stdlib)
                if new_content2:
                    fp.write_text(new_content2, encoding='utf-8')
                    ok3, _ = validate_import(fp)
                    if ok3:
                        fixed += 1
                        rel = str(fp.relative_to(SRC))
                        total_safe = len(safe_stdlib) + sum(len(v) for v in safe_from.values())
                        print(f'  ✓ {rel}: +{total_safe} imports (partial, {len(cycle_names)} cycled)')
                        for s in sorted(safe_stdlib):
                            print(f'      import {s}')
                        for src, names in sorted(safe_from.items()):
                            print(f'      from {src} import {", ".join(sorted(names))}')
                    else:
                        fp.write_text(original, encoding='utf-8')

            if cycle_names:
                rel = str(fp.relative_to(SRC))
                failed.append((rel, cycle_names))
                print(f'  ✗ {rel}: CYCLE for {cycle_names}')

    print(f'\nFixed {fixed} files')

    if failed:
        print(f'\n{len(failed)} files had cycle issues:')
        for rel, names in failed:
            print(f'  {rel}: {names}')

    if unmapped:
        total = sum(len(v) for v in unmapped.values())
        print(f'\n{total} UNMAPPED names (need definitions or manual resolution):')
        for mod in sorted(unmapped):
            print(f'  {mod}: {sorted(unmapped[mod])}')


if __name__ == '__main__':
    main()
