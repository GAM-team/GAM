"""Course ID and alias scope helpers.

Pure string utilities for adding/removing course ID prefixes.
This is a leaf module with no intra-project dependencies, created
to break the entity ↔ courses import cycle.
"""


def addCourseIdScope(courseId):
  if not courseId.isdigit() and courseId[:2] not in {'d:', 'p:'}:
    return f'd:{courseId}'
  return courseId

def removeCourseIdScope(courseId):
  if courseId.startswith('d:'):
    return courseId[2:]
  return courseId

def removeCourseAliasScope(alias):
  if alias.startswith('d:'):
    return alias[2:]
  return alias

def addCourseAliasScope(alias):
  """Prepend 'd:' scope to course alias if not already scoped."""
  if alias[:2] not in {'d:', 'p:'}:
    return f'd:{alias}'
  return alias
