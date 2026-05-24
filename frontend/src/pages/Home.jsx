import React from 'react';
import { Link } from 'react-router-dom';
import { FaCode, FaGamepad, FaChartLine, FaUsers, FaCertificate, FaClock } from 'react-icons/fa';
import Header from '../components/layout/Header';

const Home = () => {
  return (
    <div className="min-h-screen">
      <Header isLanding />

      {/* HERO */}
      <section className="hero-bg py-24 relative">
        <div className="max-w-5xl mx-auto px-6 text-center relative z-10">
          <span className="inline-block mb-6 px-4 py-1.5 text-sm rounded-full border border-[var(--border-subtle)] bg-[var(--input-bg)] backdrop-blur text-[var(--text-primary)]">
            Welcome to Interactive Learning
          </span>

          <h1 className="text-5xl md:text-6xl font-extrabold leading-[1.15] mb-6 text-[var(--text-primary)]">
            Learn Smarter,<br />
            <span className="neon-text">Grow Faster</span>
          </h1>

          <p className="text-lg text-[var(--text-secondary)] max-w-2xl mx-auto mb-10 leading-relaxed">
            Master coding and computer science through interactive challenges, real-time feedback, and personalized learning paths. Join thousands of students advancing their careers.
          </p>

          <Link to="/courses" className="btn-grad text-white px-10 py-4 rounded-xl font-semibold hover:brightness-110 transition shadow-xl text-lg inline-block">
            Explore Courses
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-[var(--text-primary)] mb-4">
              Everything You Need to<br />
              <span className="neon-text">Master Your Skills</span>
            </h2>
            <p className="text-[var(--text-muted)] max-w-2xl mx-auto">
              Comprehensive tools and features designed to accelerate your learning journey
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="glow-card rounded-2xl p-6">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4 bg-[var(--input-bg)]">
                <FaCode className="w-6 h-6 text-blue-400" />
              </div>
              <h3 className="text-lg font-semibold mb-2 text-[var(--text-primary)]">Interactive Coding</h3>
              <p className="text-[var(--text-secondary)] text-sm">Write and test code in real-time with instant feedback and detailed explanations</p>
            </div>

            <div className="glow-card rounded-2xl p-6">
              <div className="w-12 h-12 bg-[var(--input-bg)] rounded-xl flex items-center justify-center mb-4">
                <FaGamepad className="w-6 h-6 text-purple-400" />
              </div>
              <h3 className="text-lg font-semibold mb-2 text-[var(--text-primary)]">Gamified Learning</h3>
              <p className="text-[var(--text-secondary)] text-sm">Earn badges, unlock achievements and compete on leaderboards while learning</p>
            </div>

            <div className="glow-card rounded-2xl p-6">
              <div className="w-12 h-12 bg-[var(--input-bg)] rounded-xl flex items-center justify-center mb-4">
                <FaChartLine className="w-6 h-6 text-green-400" />
              </div>
              <h3 className="text-lg font-semibold mb-2 text-[var(--text-primary)]">Progress Tracking</h3>
              <p className="text-[var(--text-secondary)] text-sm">Visualize your learning journey with detailed analytics and performance metrics</p>
            </div>

            <div className="glow-card rounded-2xl p-6">
              <div className="w-12 h-12 bg-[var(--input-bg)] rounded-xl flex items-center justify-center mb-4">
                <FaUsers className="w-6 h-6 text-orange-400" />
              </div>
              <h3 className="text-lg font-semibold mb-2 text-[var(--text-primary)]">Community Support</h3>
              <p className="text-[var(--text-secondary)] text-sm">Connect with peers, share solutions, and get help from experienced mentors</p>
            </div>

            <div className="glow-card rounded-2xl p-6">
              <div className="w-12 h-12 bg-[var(--input-bg)] rounded-xl flex items-center justify-center mb-4">
                <FaCertificate className="w-6 h-6 text-yellow-400" />
              </div>
              <h3 className="text-lg font-semibold mb-2 text-[var(--text-primary)]">Certifications</h3>
              <p className="text-[var(--text-secondary)] text-sm">Earn recognized certifications upon completing courses and mastering skills</p>
            </div>

            <div className="glow-card rounded-2xl p-6">
              <div className="w-12 h-12 bg-[var(--input-bg)] rounded-xl flex items-center justify-center mb-4">
                <FaClock className="w-6 h-6 text-indigo-400" />
              </div>
              <h3 className="text-lg font-semibold mb-2 text-[var(--text-primary)]">Self-Paced Learning</h3>
              <p className="text-[var(--text-secondary)] text-sm">Learn at your own speed with flexible schedules and lifetime access</p>
            </div>
          </div>
        </div>
      </section>

      {/* Dashboard Preview */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4 text-[var(--text-primary)]">
              Your Learning<br />
              <span className="neon-text">Dashboard</span>
            </h2>
            <p className="text-[var(--text-muted)] max-w-2xl mx-auto">
              Track progress, manage courses, and stay motivated on your learning journey
            </p>
          </div>

          <div className="rounded-2xl p-8 bg-[var(--surface)] border border-[var(--border-subtle)]">
            <div className="rounded-xl p-6 card-strong mb-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold text-[var(--text-primary)]">Active Courses</h3>
                <span className="text-sm text-[var(--text-muted)]">Your current learning paths</span>
              </div>

              <div className="space-y-4">
                {[
                  { title: 'Python Fundamentals', lessons: '18/25', progress: 75, color: 'indigo' },
                  { title: 'Java', lessons: '11/25', progress: 43, color: 'purple' },
                  { title: 'C Programming', lessons: '13/25', progress: 50, color: 'blue' }
                ].map((course, idx) => (
                  <div key={idx} className={`rounded-lg p-4 border-l-4 border-${course.color}-400 bg-[var(--input-bg)]`}>
                    <div className="flex justify-between mb-2">
                      <div>
                        <h4 className="font-semibold text-[var(--text-primary)]">{course.title}</h4>
                        <p className="text-sm text-[var(--text-secondary)]">Lessons: {course.lessons}</p>
                      </div>
                      <span className="text-sm text-[var(--text-primary)]">{course.progress}%</span>
                    </div>
                    <div className="w-full bg-[var(--border-subtle)] h-2 rounded-full">
                      <div className={`bg-${course.color}-400 h-2 rounded-full`} style={{ width: `${course.progress}%` }}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl p-6 card-strong">
              <h3 className="text-xl font-bold mb-4 text-[var(--text-primary)]">This Month</h3>
              <div className="grid grid-cols-3 gap-6 text-center">
                <div>
                  <div className="text-3xl font-bold text-[var(--text-primary)]">28</div>
                  <div className="text-sm text-[var(--text-muted)]">Challenges Solved</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-[var(--text-primary)]">12</div>
                  <div className="text-sm text-[var(--text-muted)]">Lessons Completed</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-[var(--text-primary)]">450</div>
                  <div className="text-sm text-[var(--text-muted)]">Points Earned</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 cta-bg text-[var(--text-primary)] relative overflow-hidden">
        <div className="max-w-4xl mx-auto px-6 text-center relative z-10">
          <h2 className="text-3xl md:text-4xl font-bold mb-6 neon-text">
            Ready to Start Your<br />Learning Journey?
          </h2>

          <p className="text-[var(--text-secondary)] mb-10 text-lg max-w-2xl mx-auto">
            Join thousands of students and professionals learning new skills and advancing their careers
          </p>

          <div className="flex flex-col sm:flex-row justify-center items-center gap-4 px-4">
  <Link 
    to="/signup" 
    className="w-full sm:w-auto btn-grad text-white px-8 sm:px-10 py-3.5 sm:py-4 rounded-xl font-semibold hover:brightness-110 active:scale-95 transition-all duration-200 text-base sm:text-lg shadow-xl text-center"
  >
    Start Learning Now
  </Link>

  <Link 
    to="/courses" 
    className="w-full sm:w-auto border-2 border-[var(--text-primary)] text-[var(--text-primary)] px-8 sm:px-10 py-3.5 sm:py-4 rounded-xl font-semibold hover:bg-[var(--text-primary)]/10 active:scale-95 transition-all duration-200 text-base sm:text-lg shadow-lg text-center backdrop-blur-sm"
  >
    Explore Courses
  </Link>
</div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[var(--bg-footer)] text-[var(--text-muted)] py-12 border-t border-[var(--border-subtle)]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold logo-badge">
                  Y
                </div>
                <span className="text-xl font-bold text-[var(--text-primary)]">Yaksh</span>
              </div>
              <p className="text-sm text-[var(--text-muted)]">
                Interactive learning platform for coding and computer science
              </p>
            </div>

            <div>
              <h4 className="font-semibold text-[var(--text-primary)] mb-3">Product</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/" className="hover:text-[var(--text-primary)]">Features</Link></li>
                <li><Link to="/courses" className="hover:text-[var(--text-primary)]">Courses</Link></li>
                <li><Link to="/" className="hover:text-[var(--text-primary)]">Privacy</Link></li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-[var(--text-primary)] mb-3">Company</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/" className="hover:text-[var(--text-primary)]">About</Link></li>
                <li><Link to="/" className="hover:text-[var(--text-primary)]">Privacy</Link></li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-[var(--text-primary)] mb-3">Contact</h4>
              <p className="text-sm text-[var(--text-muted)]">pythonsupport@fossee.com</p>
            </div>
          </div>

          <div className="border-t border-[var(--border-subtle)] pt-6 flex justify-between text-sm text-[var(--text-muted)] flex-wrap gap-4">
            <p>© 2025 Yaksh. All rights reserved</p>
            <p>Developed by FOSSEE group, IIT Bombay</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;