from django.core.management.base import BaseCommand
from yaksh.models import Badge


class Command(BaseCommand):
    help = 'Initialize the database with predefined badges'

    def handle(self, *args, **kwargs):
        badges_data = [
            {
                'name': 'First Challenge',
                'description': 'Complete your first coding challenge',
                'icon': 'check',
                'color': 'cyan',
                'badge_type': 'challenge',
                'criteria_type': 'challenges_solved',
                'criteria_value': 1
            },
            {
                'name': '7-Day Streak',
                'description': 'Learn for 7 consecutive days',
                'icon': 'fire',
                'color': 'orange',
                'badge_type': 'streak',
                'criteria_type': 'streak_days',
                'criteria_value': 7
            },
            {
                'name': '30-Day Streak',
                'description': 'Learn for 30 consecutive days',
                'icon': 'fire',
                'color': 'orange',
                'badge_type': 'streak',
                'criteria_type': 'streak_days',
                'criteria_value': 30
            },
            {
                'name': 'Perfect Score',
                'description': 'Get 100% on a challenge',
                'icon': 'trophy',
                'color': 'purple',
                'badge_type': 'achievement',
                'criteria_type': 'perfect_score',
                'criteria_value': 1
            },
            {
                'name': 'Speed Demon',
                'description': 'Solve 3 challenges in one day',
                'icon': 'bolt',
                'color': 'blue',
                'badge_type': 'challenge',
                'criteria_type': 'challenges_solved',
                'criteria_value': 3
            },
            {
                'name': 'Century Club',
                'description': 'Solve 100 challenges',
                'icon': 'trophy',
                'color': 'amber',
                'badge_type': 'challenge',
                'criteria_type': 'challenges_solved',
                'criteria_value': 100
            },
            {
                'name': 'Course Master',
                'description': 'Complete an entire course',
                'icon': 'star',
                'color': 'green',
                'badge_type': 'course',
                'criteria_type': 'courses_completed',
                'criteria_value': 1
            },
            {
                'name': 'Mentor',
                'description': 'Complete 5 courses',
                'icon': 'star',
                'color': 'purple',
                'badge_type': 'course',
                'criteria_type': 'courses_completed',
                'criteria_value': 5
            },
            {
                'name': 'Challenge Rookie',
                'description': 'Solve 10 challenges',
                'icon': 'check',
                'color': 'green',
                'badge_type': 'challenge',
                'criteria_type': 'challenges_solved',
                'criteria_value': 10
            },
            {
                'name': 'Challenge Expert',
                'description': 'Solve 50 challenges',
                'icon': 'trophy',
                'color': 'blue',
                'badge_type': 'challenge',
                'criteria_type': 'challenges_solved',
                'criteria_value': 50
            }
        ]

        created_count = 0
        updated_count = 0

        for badge_data in badges_data:
            badge, created = Badge.objects.update_or_create(
                name=badge_data['name'],
                defaults=badge_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created badge: {badge.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated badge: {badge.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nBadge initialization complete!'
                f'\nCreated: {created_count} badges'
                f'\nUpdated: {updated_count} badges'
            )
        )

