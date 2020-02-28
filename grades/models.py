from django.db import models
from django.contrib.auth.models import User


class GradingSystem(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(default='About the grading system!')
    creator = models.ForeignKey(User, null=True, blank=True,
                                on_delete=models.CASCADE)

    def get_grade(self, marks):
        ranges = self.graderange_set.all()
        lower_limits = ranges.values_list('lower_limit', flat=True)
        upper_limits = ranges.values_list('upper_limit', flat=True)
        lower_limit = self._get_lower_limit(marks, lower_limits)
        upper_limit = self._get_upper_limit(marks, upper_limits)
        grade_range = ranges.filter(lower_limit=lower_limit,
                                    upper_limit=upper_limit).first()
        if grade_range:
            return grade_range.grade

    def _get_upper_limit(self, marks, upper_limits):
        greater_than = [upper_limit for upper_limit in upper_limits
                        if upper_limit > marks]
        if greater_than:
            return min(greater_than, key=lambda x: x-marks)

    def _get_lower_limit(self, marks, lower_limits):
        less_than = []
        for lower_limit in lower_limits:
            if lower_limit == marks:
                return lower_limit
            if lower_limit < marks:
                less_than.append(lower_limit)
        if less_than:
            return max(less_than, key=lambda x: x-marks)

    def __str__(self):
        return self.name.title()


class GradeRange(models.Model):
    system = models.ForeignKey(GradingSystem, on_delete=models.CASCADE)
    lower_limit = models.FloatField()
    upper_limit = models.FloatField()
    grade = models.CharField(max_length=10)
    description = models.CharField(max_length=127, null=True, blank=True)

    def __str__(self):
        return self.system.name.title()
