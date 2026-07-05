import pytest
from gam.util.entity import (
    addCourseIdScope,
    removeCourseIdScope,
    addCourseAliasScope,
    removeCourseAliasScope,
)

class TestCourseScopes:
    def test_add_course_id_scope_plain(self):
        """Should add 'd:' if just digits and no prefix."""
        assert addCourseIdScope("12345") == "12345"
        
    def test_add_course_id_scope_already_prefixed(self):
        """Should not modify if already prefixed."""
        assert addCourseIdScope("d:12345") == "d:12345"
        assert addCourseIdScope("p:12345") == "p:12345"
        
    def test_add_course_id_scope_non_digits(self):
        """Should add 'd:' if it's not purely digits and has no prefix."""
        assert addCourseIdScope("abcde") == "d:abcde"

    def test_remove_course_id_scope_with_d(self):
        """Should remove 'd:' prefix."""
        assert removeCourseIdScope("d:12345") == "12345"

    def test_remove_course_id_scope_with_p(self):
        """Should not remove 'p:' prefix."""
        assert removeCourseIdScope("p:12345") == "p:12345"

    def test_remove_course_id_scope_no_prefix(self):
        """Should return unchanged if no prefix."""
        assert removeCourseIdScope("12345") == "12345"
        
    def test_add_course_alias_scope_no_prefix(self):
        """Should add 'd:' prefix if no prefix present."""
        assert addCourseAliasScope("my-alias") == "d:my-alias"

    def test_add_course_alias_scope_prefixed(self):
        """Should return unchanged if prefixed."""
        assert addCourseAliasScope("d:my-alias") == "d:my-alias"
        assert addCourseAliasScope("p:my-alias") == "p:my-alias"

    def test_remove_course_alias_scope_with_d(self):
        """Should remove 'd:' prefix."""
        assert removeCourseAliasScope("d:my-alias") == "my-alias"
        
    def test_remove_course_alias_scope_with_p(self):
        """Should not remove 'p:' prefix."""
        assert removeCourseAliasScope("p:my-alias") == "p:my-alias"
