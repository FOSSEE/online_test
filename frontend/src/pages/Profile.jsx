import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  FaLinkedin,
  FaGithub,
  FaUser,
  FaEnvelope,
  FaPhone,
  FaMapMarkerAlt,
  FaGraduationCap,
  FaCamera,
  FaGlobe,
  FaClock,
  FaCheckCircle,
  FaTimesCircle,
  FaSave,
  FaTimes,
  FaEdit,
  FaTrash,
  FaChartLine
} from 'react-icons/fa';
import Header from '../components/layout/Header';
import StudentSidebar from '../components/layout/Sidebar';
import TeacherSidebar from '../components/layout/TeacherSidebar';
import { useAuthStore } from '../store/authStore';
import { getUserProfile, patchUserProfile, getModeratorStatus } from '../api/api';

const Profile = () => {
  const { user, isAuthenticated } = useAuthStore();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isModeratorActive, setIsModeratorActive] = useState(null);
  const [isSummaryOpen, setIsSummaryOpen] = useState(false);

  const [profileData, setProfileData] = useState(null);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    display_name: '',
    bio: '',
    email: '',
    phone: '',
    city: '',
    country: 'India',
    linkedin: '',
    github: '',
    roll_number: '',
    institute: '',
    department: '',
    position: '',
    timezone: 'Asia/Kolkata'
  });

  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  const [loading, setLoading] = useState(true);

  // Determine if user is currently in teacher mode (not just has teacher privileges)
  const isTeacher = user?.is_moderator && isModeratorActive;

  // Fetch active moderator status on mount
  useEffect(() => {
    const fetchModeratorStatus = async () => {
      if (user?.is_moderator && isAuthenticated) {
        try {
          const status = await getModeratorStatus();
          setIsModeratorActive(status.is_moderator_active);
        } catch (error) {
          console.error('Failed to fetch moderator status:', error);
          setIsModeratorActive(false);
        }
      } else {
        setIsModeratorActive(false);
      }
    };
    fetchModeratorStatus();
  }, [user, isAuthenticated]);

  // Fetch profile data on mount
  useEffect(() => {
    const loadProfile = async () => {
      try {
        setLoading(true);
        const response = await getUserProfile();
        const userData = response.user;
        setProfileData(userData);

        // Populate form
        setFormData({
          first_name: userData.first_name || '',
          last_name: userData.last_name || '',
          display_name: userData.display_name || '',
          bio: userData.bio || '',
          email: userData.email || '',
          phone: userData.phone || '',
          city: userData.city || '',
          country: userData.country || 'India',
          linkedin: userData.linkedin || '',
          github: userData.github || '',
          roll_number: userData.roll_number || '',
          institute: userData.institute || '',
          department: userData.department || '',
          position: userData.position || '',
          timezone: userData.timezone || 'Asia/Kolkata'
        });
      } catch (error) {
        console.error('Failed to load profile:', error);
        showMessage('error', 'Failed to load profile data');
      } finally {
        setLoading(false);
      }
    };

    if (isAuthenticated) {
      loadProfile();
    }
  }, [isAuthenticated]);

  const showMessage = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage({ type: '', text: '' }), 4000);
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setIsSaving(true);

    try {
      // Only send changed fields
      const changedFields = {};
      Object.keys(formData).forEach(key => {
        if (formData[key] !== profileData?.[key]) {
          changedFields[key] = formData[key];
        }
      });

      if (Object.keys(changedFields).length === 0) {
        showMessage('info', 'No changes to save');
        setIsSaving(false);
        return;
      }

      const response = await patchUserProfile(changedFields);

      if (response.message) {
        setProfileData(response.user);
        showMessage('success', 'Profile updated successfully!');
        setIsEditing(false);
      }
    } catch (error) {
      console.error('Failed to update profile:', error);
      showMessage('error', error.response?.data?.error || 'Failed to update profile');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    // Reset form to original data
    if (profileData) {
      setFormData({
        first_name: profileData.first_name || '',
        last_name: profileData.last_name || '',
        display_name: profileData.display_name || '',
        bio: profileData.bio || '',
        email: profileData.email || '',
        phone: profileData.phone || '',
        city: profileData.city || '',
        country: profileData.country || 'India',
        linkedin: profileData.linkedin || '',
        github: profileData.github || '',
        roll_number: profileData.roll_number || '',
        institute: profileData.institute || '',
        department: profileData.department || '',
        position: profileData.position || '',
        timezone: profileData.timezone || 'Asia/Kolkata'
      });
    }
    setIsEditing(false);
  };





  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--bg-primary)] text-[var(--text-primary)]">
        <div className="text-center">
          <div className="text-2xl font-bold text-[var(--text-secondary)] mb-4">Please log in to view your profile</div>
          <Link to="/signin" className="text-indigo-500 hover:text-indigo-400 font-semibold transition-colors">
            Go to Login
          </Link>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex min-h-screen relative grid-texture">
        {isTeacher ? (
          <TeacherSidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
        ) : (
          <StudentSidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
        )}
        <main className="flex-1 lg:ml-64">
          <Header
            onMenuClick={() => setIsSidebarOpen(!isSidebarOpen)}
            isSidebarOpen={isSidebarOpen}
          />
          <div className="p-8 flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto mb-4"></div>
              <p className="text-[var(--text-muted)] font-medium">Loading profile...</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen relative grid-texture">
      {/* Sidebar - Conditional based on role */}
      {isTeacher ? (
        <TeacherSidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
      ) : (
        <StudentSidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
      )}

      {/* Main Content */}
      <main className="flex-1">
        <Header isAuth />
        <div className="p-4 sm:p-6 lg:p-8">
          {/* Page Header */}
          <div className="mb-6 lg:mb-8">

            <h1 className="text-2xl sm:text-3xl font-bold mb-2">Profile Settings</h1>
            <p className="text-sm muted">Manage your account information and preferences</p>

          </div>
          {/* Status Message */}
          {message.text && (
            <div className={`mb-6 p-4 rounded-xl border-2 text-sm sm:text-base ${message.type === 'success' ? 'bg-green-500/10 border-green-500/30 text-green-300' :
              message.type === 'error' ? 'bg-red-500/10 border-red-500/30 text-red-300' :
                'bg-blue-500/10 border-blue-500/30 text-blue-300'
              }`}>
              <div className="flex items-center gap-2">
                {message.type === 'success' ? <FaCheckCircle /> : <FaTimesCircle />}
                <span>{message.text}</span>
              </div>
            </div>
          )}

          <div className="flex flex-col xl:flex-row gap-6">
            <div className="flex-1 card-strong p-4 sm:p-6 relative rounded-2xl border-2 border-[var(--border-strong)]">

              {/* Header */}
              <div className="flex flex-row items-center gap-2 mb-4 sm:mb-6 pb-4 border-b-2 border-[var(--border-subtle)] pr-12 sm:pr-32">
                <div className="flex items-center justify-center w-10 h-10 sm:w-12 sm:h-12 rounded-xl flex-shrink-0">
                  <img
                    src={`https://ui-avatars.com/api/?name=${formData.first_name}+${formData.last_name}&background=6366f1&color=fff&size=128&bold=true`}
                    alt="Profile"
                    className="w-full h-full rounded-xl shadow-[var(--shadow-soft)] border border-indigo-500/20 object-cover"
                  />
                  {isEditing && (
                    <button
                      type="button"
                      className="absolute -bottom-2 -right-2 bg-indigo-600 hover:bg-indigo-500 text-white p-1.5 sm:p-2 rounded-lg border border-indigo-400/30 shadow-lg transition-transform hover:scale-105 active:scale-95"
                      onClick={() => alert('Avatar upload coming soon!')}
                    >
                      <FaCamera className="w-3 h-3 sm:w-3.5 sm:h-3.5" />
                    </button>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <h2 className="text-lg sm:text-xl font-bold truncate">
                    {formData.display_name || `${formData.first_name} ${formData.last_name}`}
                  </h2>
                  <p className="text-xs sm:text-sm muted">
                    @{user?.username} • {formData.position || (isTeacher ? 'Teacher' : 'Student')}

                  </p>
                </div>
              </div>

              {!isEditing && (
                <div className="absolute right-4 top-4 sm:right-6 sm:top-6 flex items-center gap-2 z-10">
                  <button
                    type="button"
                    onClick={() => setIsSummaryOpen(true)}
                    className="xl:hidden bg-green-600 text-white px-3 sm:px-4 py-2 rounded-lg font-semibold hover:bg-purple-700 active:scale-95 transition text-xs sm:text-sm whitespace-nowrap"
                  >
                    <FaChartLine className="inline w-4 h-4 sm:mr-2" />
                    <span className="hidden sm:inline">Stats</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsEditing(true)}
                    className="flex items-center gap-2 px-3 sm:px-4 py-2 bg-blue-600/10 hover:bg-blue-600/20 border border-blue-500/30 text-blue-400 rounded-xl text-sm font-semibold transition-colors"
                  >
                    <FaEdit className="inline w-4 h-4 sm:mr-2" />
                    <span className="hidden sm:inline">Edit Profile</span>
                  </button>
                </div>
              )}

              {/* Form */}
              <form onSubmit={handleSave} className="space-y-4 sm:space-y-5">
                <div className="grid lg:grid-cols-2 gap-5 sm:gap-8">
                  {/* Left Column - Personal Details */}
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-base sm:text-lg font-bold mb-1">Personal Details</h3>
                      <p className="text-xs sm:text-sm muted mb-4">Basic information about yourself</p>
                    </div>

                    {/* First & Last Name */}
                    <div className="grid grid-cols-2 gap-3 sm:gap-4">
                      <div>
                        <label className="block text-xs sm:text-sm font-semibold mb-2 text-[var(--text-secondary)]">
                          First Name *
                        </label>
                        <input
                          type="text"
                          name="first_name"
                          value={formData.first_name}
                          onChange={(e) => handleChange('first_name', e.target.value)}
                          disabled={!isEditing}
                          required
                          placeholder="First name"
                          className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                        />
                      </div>
                      <div>
                        <label className="block text-xs sm:text-sm font-semibold mb-2 text-[var(--text-secondary)]">
                          Last Name *
                        </label>
                        <input
                          type="text"
                          name="last_name"
                          value={formData.last_name}
                          onChange={(e) => handleChange('last_name', e.target.value)}
                          disabled={!isEditing}
                          required
                          placeholder="Last name"
                          className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                        />
                      </div>
                    </div>

                    {/* Display Name */}
                    <div>
                      <label className="block text-xs sm:text-sm font-semibold mb-2 text-[var(--text-secondary)]">
                        Display Name
                      </label>
                      <input
                        type="text"
                        name="display_name"
                        value={formData.display_name}
                        onChange={(e) => handleChange('display_name', e.target.value)}
                        disabled={!isEditing}
                        placeholder="How you want to be called"
                        className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                      />
                    </div>

                    {/* Bio */}
                    <div>
                      <label className="block text-xs sm:text-sm font-semibold mb-2 text-[var(--text-secondary)]">
                        Bio
                      </label>
                      <textarea
                        name="bio"
                        value={formData.bio}
                        onChange={(e) => handleChange('bio', e.target.value)}
                        disabled={!isEditing}
                        rows="5"
                        placeholder="Tell us about yourself..."
                        className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 resize-y text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                      />
                    </div>

                    {/* Contact Info Group */}
                    <div className="pt-4 mt-4 border-t border-[var(--border-subtle)] space-y-4">
                      <div>
                        <h3 className="text-base sm:text-lg font-bold mb-1">Contact & Location</h3>
                        <p className="text-xs sm:text-sm muted mb-4">How to reach you</p>
                      </div>

                      <div className="grid grid-cols-2 gap-3 sm:gap-4">
                        {/* Email */}
                        <div className="col-span-2">
                          <label className="block text-xs sm:text-sm font-semibold mb-2 text-[var(--text-secondary)]">
                            Email *
                          </label>
                          <input
                            type="email"
                            name="email"
                            value={formData.email}
                            onChange={(e) => handleChange('email', e.target.value)}
                            disabled={!isEditing}
                            required
                            placeholder="your.email@example.com"
                            className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                          />
                        </div>

                        {/* Phone */}
                        <div>
                          <label className="block text-xs sm:text-sm font-semibold mb-2 text-[var(--text-secondary)]">
                            Phone
                          </label>
                          <input
                            type="tel"
                            name="phone"
                            value={formData.phone}
                            onChange={(e) => handleChange('phone', e.target.value)}
                            disabled={!isEditing}
                            placeholder="+91 XXXXX XXXXX"
                            className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                          />
                        </div>

                        {/* Timezone */}
                        <div>
                          <label className="block text-xs sm:text-sm font-semibold mb-2 text-[var(--text-secondary)]">
                            Timezone
                          </label>
                          <select
                            name="timezone"
                            value={formData.timezone}
                            onChange={(e) => handleChange('timezone', e.target.value)}
                            disabled={!isEditing}
                            className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                          >
                            <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
                            <option value="Asia/Dubai">Asia/Dubai (GST)</option>
                            <option value="Europe/London">Europe/London (GMT)</option>
                            <option value="America/New_York">America/New_York (EST)</option>
                            <option value="America/Los_Angeles">America/Los_Angeles (PST)</option>
                            <option value="UTC">UTC</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Right Column - Academic & Social */}
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-base sm:text-lg font-bold mb-1">Academic & Department</h3>
                      <p className="text-xs sm:text-sm muted mb-4">Your current educational status</p>
                    </div>

                    {/* Roll Number & Position */}
                    <div className="grid grid-cols-2 gap-3 sm:gap-4">
                      <div>
                        <label className="block text-xs sm:text-sm font-semibold mb-2 text-[var(--text-secondary)]">
                          Roll Number
                        </label>
                        <input
                          type="text"
                          name="roll_number"
                          value={formData.roll_number}
                          onChange={(e) => handleChange('roll_number', e.target.value)}
                          disabled={!isEditing}
                          placeholder="Roll no."
                          className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                        />
                      </div>
                      <div>
                        <label className="block text-xs sm:text-sm font-semibold mb-2 text-[var(--text-secondary)]">
                          Position
                        </label>
                        <input
                          type="text"
                          name="position"
                          value={formData.position}
                          onChange={(e) => handleChange('position', e.target.value)}
                          disabled={!isEditing}
                          placeholder="e.g., Student"
                          className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                        />
                      </div>
                    </div>

                    {/* Institute */}
                    <div>
                      <label className="block text-xs sm:text-sm font-semibold mb-2 text-[var(--text-secondary)]">
                        Institute
                      </label>
                      <input
                        type="text"
                        name="institute"
                        value={formData.institute}
                        onChange={(e) => handleChange('institute', e.target.value)}
                        disabled={!isEditing}
                        placeholder="Enter institute name"
                        className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                      />
                    </div>

                    {/* Department */}
                    <div>
                      <label className="block text-xs sm:text-sm font-semibold mb-2 text-[var(--text-secondary)]">
                        Department
                      </label>
                      <input
                        type="text"
                        name="department"
                        value={formData.department}
                        onChange={(e) => handleChange('department', e.target.value)}
                        disabled={!isEditing}
                        placeholder="e.g., Computer Science"
                        className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-3 sm:gap-4">
                      <div>
                        <label className="block text-xs sm:text-sm font-semibold mb-2 text-[var(--text-secondary)]">
                          City
                        </label>
                        <input
                          type="text"
                          name="city"
                          value={formData.city}
                          onChange={(e) => handleChange('city', e.target.value)}
                          disabled={!isEditing}
                          placeholder="Your city"
                          className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                        />
                      </div>
                      <div>
                        <label className="block text-xs sm:text-sm font-semibold mb-2 text-[var(--text-secondary)]">
                          Country
                        </label>
                        <select
                          name="country"
                          value={formData.country}
                          onChange={(e) => handleChange('country', e.target.value)}
                          disabled={!isEditing}
                          className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                        >
                          <option value="India">India</option>
                          <option value="United States">United States</option>
                          <option value="United Kingdom">United Kingdom</option>
                          <option value="Canada">Canada</option>
                          <option value="Australia">Australia</option>
                        </select>
                      </div>
                    </div>

                    {/* Social Links Group */}
                    <div className="pt-4 mt-4 border-t border-[var(--border-subtle)] space-y-4">
                      <div>
                        <h3 className="text-base sm:text-lg font-bold mb-1">Social Profiles</h3>
                        <p className="text-xs sm:text-sm muted mb-4">Connect your social accounts</p>
                      </div>

                      {/* LinkedIn */}
                      <div>
                        <label className="block text-xs sm:text-sm font-semibold mb-2 text-[var(--text-secondary)]">
                          LinkedIn URL
                        </label>
                        <div className="relative">
                          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <FaLinkedin className="text-blue-500" />
                          </div>
                          <input
                            type="url"
                            name="linkedin"
                            value={formData.linkedin}
                            onChange={(e) => handleChange('linkedin', e.target.value)}
                            disabled={!isEditing}
                            placeholder="https://www.linkedin.com/in/..."
                            className="w-full pl-10 pr-3 sm:pr-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                          />
                        </div>
                      </div>

                      {/* GitHub */}
                      <div>
                        <label className="block text-xs sm:text-sm font-semibold mb-2 text-[var(--text-secondary)]">
                          GitHub URL
                        </label>
                        <div className="relative">
                          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <FaGithub className="text-[var(--text-primary)]" />
                          </div>
                          <input
                            type="url"
                            name="github"
                            value={formData.github}
                            onChange={(e) => handleChange('github', e.target.value)}
                            disabled={!isEditing}
                            placeholder="https://github.com/..."
                            className="w-full pl-10 pr-3 sm:pr-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Form Actions */}
                {isEditing && (
                  <div className="flex flex-col sm:flex-row justify-end gap-3 mt-6 sm:mt-8 pt-6 sm:pt-8 border-t-2 border-[var(--border-subtle)]">
                    <button
                      type="button"
                      onClick={handleCancel}
                      disabled={isSaving}
                      className="px-6 py-2.5 rounded-xl font-bold bg-[var(--input-bg)] hover:bg-red-500/10 border-2 border-[var(--border-strong)] hover:border-red-500/30 text-[var(--text-primary)] hover:text-red-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      <FaTimes className="w-4 h-4" />
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isSaving}
                      className="px-8 py-2.5 rounded-xl font-bold bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      {isSaving ? (
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      ) : (
                        <FaSave className="w-4 h-4" />
                      )}
                      <span>Save Changes</span>
                    </button>
                  </div>
                )}
              </form>
            </div>

            {/* Profile Summary Sidebar */}
            <div className="hidden xl:block xl:w-80 2xl:w-96 flex-shrink-0">
              <div className="card-strong p-5 sm:p-6 rounded-2xl border-2 border-[var(--border-strong)] sticky top-6">
                {/* Sidebar Header */}
                <div className="flex items-center gap-3 mb-6 pb-4 border-b-2 border-[var(--border-subtle)]">
                  <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border-2 border-indigo-500/30 flex items-center justify-center">
                    <FaChartLine className="w-5 h-5 text-indigo-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-[var(--text-primary)]">Profile Summary</h3>
                    <p className="text-xs muted">Your account overview</p>
                  </div>
                </div>

                {/* Account Info */}
                <div className="space-y-4">
                  <div className="bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl p-4">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-[var(--text-secondary)] font-medium">Username</span>
                      <span className="font-bold text-[var(--text-primary)] px-2.5 py-1 rounded-md bg-[var(--surface)] border-2 border-[var(--border-strong)]">
                        @{user?.username}
                      </span>
                    </div>
                  </div>

                  <div className="bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl p-4">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-[var(--text-secondary)] font-medium">Role</span>
                      <span className="font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">
                        {isTeacher ? 'Teacher' : 'Student'}
                      </span>
                    </div>
                  </div>

                  <div className="bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl p-4">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-[var(--text-secondary)] font-medium">Location</span>
                      <div className="flex items-center gap-1.5 font-bold text-[var(--text-primary)]">
                        <FaMapMarkerAlt className="w-3.5 h-3.5 text-red-400" />
                        <span>{formData.city ? `${formData.city}, ${formData.country}` : 'Not set'}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Social Links Summary */}
                {(formData.linkedin || formData.github) && (
                  <div className="pt-6 border-t border-[var(--border-subtle)] mt-6">
                    <h4 className="text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-4">Connected Profiles</h4>
                    <div className="space-y-3">
                      {formData.linkedin && (
                        <a
                          href={formData.linkedin}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-3 p-3 bg-[var(--input-bg)] hover:bg-blue-500/5 border-2 border-[var(--border-strong)] hover:border-blue-500/30 rounded-xl transition-all duration-300 group"
                        >
                          <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
                            <FaLinkedin className="w-4 h-4 text-blue-500" />
                          </div>
                          <span className="text-sm font-semibold text-[var(--text-primary)] group-hover:text-blue-400 transition-colors">LinkedIn Profile</span>
                        </a>
                      )}
                      {formData.github && (
                        <a
                          href={formData.github}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-3 p-3 bg-[var(--input-bg)] hover:bg-gray-500/5 border-2 border-[var(--border-strong)] hover:border-gray-500/30 rounded-xl transition-all duration-300 group"
                        >
                          <div className="w-8 h-8 rounded-lg bg-gray-500/10 flex items-center justify-center">
                            <FaGithub className="w-4 h-4 text-[var(--text-primary)]" />
                          </div>
                          <span className="text-sm font-semibold text-[var(--text-primary)] transition-colors">GitHub Profile</span>
                        </a>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Mobile/Tablet Summary Modal */}
          {isSummaryOpen && (
            <div className="fixed inset-0 z-50 xl:hidden">
              {/* Backdrop */}
              <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
                onClick={() => setIsSummaryOpen(false)}
              />

              {/* Modal */}
              <div className="absolute inset-x-4 top-1/2 -translate-y-1/2 sm:inset-x-auto sm:left-1/2 sm:-translate-x-1/2 sm:w-full sm:max-w-md">
                <div className="card-strong bg-[var(--surface)] border-2 border-[var(--border-strong)] rounded-2xl p-6 max-h-[80vh] overflow-y-auto">
                  {/* Header */}
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h3 className="text-xl font-bold flex items-center gap-2 text-[var(--text-primary)]">
                        <FaChartLine className="w-5 h-5 text-indigo-400" />
                        Profile Summary
                      </h3>
                      <p className="text-sm muted mt-1">Your account overview</p>
                    </div>
                    <button
                      onClick={() => setIsSummaryOpen(false)}
                      className="p-2 hover:bg-[var(--surface-2)] border border-transparent hover:border-[var(--border-strong)] rounded-lg transition-colors"
                    >
                      <FaTimes className="w-5 h-5 text-[var(--text-muted)]" />
                    </button>
                  </div>

                  {/* Account Info */}
                  <div className="space-y-4">
                    <div className="bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl p-4">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-[var(--text-secondary)] font-medium">Username</span>
                        <span className="font-bold text-[var(--text-primary)] px-2.5 py-1 rounded-md bg-[var(--surface)] border-2 border-[var(--border-strong)]">
                          @{user?.username}
                        </span>
                      </div>
                    </div>

                    <div className="bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl p-4">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-[var(--text-secondary)] font-medium">Role</span>
                        <span className="font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">
                          {isTeacher ? 'Teacher' : 'Student'}
                        </span>
                      </div>
                    </div>

                    <div className="bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl p-4">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-[var(--text-secondary)] font-medium">Location</span>
                        <div className="flex items-center gap-1.5 font-bold text-[var(--text-primary)]">
                          <FaMapMarkerAlt className="w-3.5 h-3.5 text-red-400" />
                          <span>{formData.city ? `${formData.city}, ${formData.country}` : 'Not set'}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Social Links Summary */}
                  {(formData.linkedin || formData.github) && (
                    <div className="pt-6 border-t border-[var(--border-subtle)] mt-6">
                      <h4 className="text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-4">Connected Profiles</h4>
                      <div className="space-y-3">
                        {formData.linkedin && (
                          <a
                            href={formData.linkedin}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-3 p-3 bg-[var(--input-bg)] hover:bg-blue-500/5 border-2 border-[var(--border-strong)] hover:border-blue-500/30 rounded-xl transition-all duration-300 group"
                          >
                            <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
                              <FaLinkedin className="w-4 h-4 text-blue-500" />
                            </div>
                            <span className="text-sm font-semibold text-[var(--text-primary)] group-hover:text-blue-400 transition-colors">LinkedIn Profile</span>
                          </a>
                        )}
                        {formData.github && (
                          <a
                            href={formData.github}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-3 p-3 bg-[var(--input-bg)] hover:bg-gray-500/5 border-2 border-[var(--border-strong)] hover:border-gray-500/30 rounded-xl transition-all duration-300 group"
                          >
                            <div className="w-8 h-8 rounded-lg bg-gray-500/10 flex items-center justify-center">
                              <FaGithub className="w-4 h-4 text-[var(--text-primary)]" />
                            </div>
                            <span className="text-sm font-semibold text-[var(--text-primary)] transition-colors">GitHub Profile</span>
                          </a>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Profile;