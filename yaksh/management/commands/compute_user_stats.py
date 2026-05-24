from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from yaksh.models import UserStats, AnswerPaper, BadgeProgress, Badge
from django.db.models import Count


class Command(BaseCommand):
    help = 'Compute and update statistics for all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Compute stats for a specific user',
        )

    def handle(self, *args, **kwargs):
        username = kwargs.get('username')

        if username:
            try:
                user = User.objects.get(username=username)
                users = [user]
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User "{username}" not found')
                )
                return
        else:
            users = User.objects.all()

        processed_count = 0

        for user in users:
            try:
                self._compute_user_stats(user)
                processed_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Processed: {user.username}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error processing {user.username}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nStats computation complete! Processed {processed_count} users.'
            )
        )

    def _compute_user_stats(self, user):
        """Compute statistics for a single user"""
        # Get or create user stats
        user_stats, created = UserStats.objects.get_or_create(user=user)

        # Count completed quizzes/challenges
        completed_papers = AnswerPaper.objects.filter(
            user=user,
            status='completed'
        ).count()
        
        user_stats.total_challenges_solved = completed_papers

        # Calculate learning hours (estimate based on quiz time)
        total_time = 0
        for paper in AnswerPaper.objects.filter(user=user, status='completed'):
            if paper.start_time and paper.end_time:
                time_diff = paper.end_time - paper.start_time
                total_time += time_diff.total_seconds() / 3600  # Convert to hours
        
        user_stats.total_learning_hours = total_time

        # Save stats
        user_stats.save()

        # Initialize badge progress for all active badges
        active_badges = Badge.objects.filter(active=True)
        for badge in active_badges:
            badge_progress, created = BadgeProgress.objects.get_or_create(
                user=user,
                badge=badge
            )
            badge_progress.update_progress()

        self.stdout.write(f'  - Challenges: {completed_papers}')
        self.stdout.write(f'  - Learning hours: {total_time:.1f}h')

