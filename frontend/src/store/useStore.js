import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useStore = create(
  persist(
    (set) => ({
      user: {
        name: 'Alex',
        username: 'mohitr8998',
        email: 'mohitr8998@gmail.com',
        avatar: 'https://ui-avatars.com/api/?name=Mohit+Rana&background=7b2ff7&color=fff&size=128',
      },

      courses: [
        {
          id: 1,
          title: 'Python Fundamentals',
          instructor: 'Prof. Sarah Chen',
          progress: 72,
          lessons: { completed: 18, total: 25 },
          level: 'Advanced',
          rating: 4.8,
          students: 5200,
          duration: '40 hours',
          color: 'indigo'
        },
        {
          id: 2,
          title: 'Java Programming Masterclass',
          instructor: 'Dr. Michael Wong',
          progress: 45,
          lessons: { completed: 11, total: 25 },
          level: 'Intermediate',
          rating: 4.9,
          students: 6400,
          duration: '52 hours',
          color: 'pink'
        },
        {
          id: 3,
          title: 'Web Development with React',
          instructor: 'Prof. Emma Johnson',
          progress: 28,
          lessons: { completed: 7, total: 25 },
          level: 'Intermediate',
          rating: 4.6,
          students: 3800,
          duration: '35 hours',
          color: 'blue'
        },
      ],

      stats: {
        coursesEnrolled: 5,
        inProgress: 2,
        challengesSolved: 127,
        challengesThisWeek: 12,
        currentStreak: 14,
        learningHours: '45h 30m',
        thisMonth: {
          challengesSolved: 28,
          lessonsCompleted: 12,
          pointsEarned: 450
        }
      },

      activities: [
        {
          id: 1,
          type: 'lesson',
          title: 'Completed lesson',
          description: 'Python for Data...',
          time: '2h ago',
          icon: 'check',
          color: 'green'
        },
        {
          id: 2,
          type: 'badge',
          title: 'Earned badge',
          badge: 'Problem Solver',
          time: '5h ago',
          icon: 'award',
          color: 'amber'
        },
        {
          id: 3,
          type: 'streak',
          title: '7-day streak!',
          description: 'Keep it up',
          time: '1d ago',
          icon: 'flame',
          color: 'orange'
        },
        {
          id: 4,
          type: 'reply',
          title: 'New forum reply',
          description: 'Your post on "Array Methods"',
          time: '2d ago',
          icon: 'message',
          color: 'purple'
        }
      ],

      badges: {
        unlocked: [
          {
            id: 1,
            name: 'First Challenge',
            description: 'Complete your first coding challenge',
            date: 'Jan 15, 2025',
            color: 'cyan'
          },
          {
            id: 2,
            name: '7-Day Streak',
            description: 'Learn for 7 consecutive days',
            date: 'Jan 22, 2025',
            color: 'orange'
          },
          {
            id: 3,
            name: 'Perfect Score',
            description: 'Get 100% on a challenge',
            date: 'Jan 20, 2025',
            color: 'purple'
          },
          {
            id: 4,
            name: 'Speed Demon',
            description: 'Solve 3 challenges in one day',
            date: 'Jan 25, 2025',
            color: 'blue'
          }
        ],
        inProgress: [
          {
            id: 5,
            name: 'Course Master',
            description: 'Complete an entire course',
            progress: 60,
            steps: { completed: 3, total: 5 }
          },
          {
            id: 6,
            name: 'Mentor',
            description: 'Help 5 other students',
            progress: 40,
            steps: { completed: 2, total: 5 }
          },
          {
            id: 7,
            name: 'Century Club',
            description: 'Solve 100 challenges',
            progress: 87,
            steps: { completed: 87, total: 100 }
          }
        ]
      },

      sidebarCollapsed: false,
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

      theme: 'dark',
      toggleTheme: () => set((state) => ({ theme: state.theme === 'dark' ? 'light' : 'dark' })),
    }),
    {
      name: 'yaksh-storage', // unique name
      partialize: (state) => ({ theme: state.theme, sidebarCollapsed: state.sidebarCollapsed }), // only persist theme and sidebar state
    }
  )
);