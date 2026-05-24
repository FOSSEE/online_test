import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import Submission from '../../pages/Submission';
import * as api from '../../api/api';
import * as authStore from '../../store/authStore';

vi.mock('../../api/api', () => ({
  getQuizSubmissionStatus: vi.fn(),
  quitQuiz: vi.fn(),
  getModeratorStatus: vi.fn(),
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useParams: () => ({ answerpaperId: '100' }),
    useNavigate: () => mockNavigate,
    Link: ({ children, to }) => <a href={to}>{children}</a>,
  };
});

describe('Submission Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(authStore, 'useAuthStore').mockReturnValue({
      user: { id: 1, is_moderator: false },
    });
    api.getModeratorStatus.mockResolvedValue({ is_moderator_active: false });
  });

  const renderComponent = () => {
    render(
      <BrowserRouter>
        <Submission />
      </BrowserRouter>
    );
  };

  it('renders loading state initially', () => {
    api.getQuizSubmissionStatus.mockImplementationOnce(() => new Promise(() => {}));
    renderComponent();
    expect(screen.getByText('Loading submission status...')).toBeInTheDocument();
  });

  it('renders error state on API failure', async () => {
    api.getQuizSubmissionStatus.mockRejectedValueOnce(new Error('Network Error'));
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Failed to load submission status')).toBeInTheDocument();
    });
  });

  it('renders submission status correctly', async () => {
    api.getQuizSubmissionStatus.mockResolvedValueOnce({
      status: 'in_progress',
      attempted_count: 1,
      not_attempted_count: 4,
      questions: [
        { id: 1, title: 'Question 1', attempted: true },
        { id: 2, title: 'Question 2', attempted: false }
      ]
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Submission Status')).toBeInTheDocument();
    });

    expect(screen.getByText('1')).toBeInTheDocument(); // attempted count
    expect(screen.getByText('4')).toBeInTheDocument(); // not attempted count
    
    // Check if ATTMEPTED and NOT ATTEMPTED badges render
    expect(screen.getByText('ATTEMPTED')).toBeInTheDocument();
    expect(screen.getByText('NOT ATTEMPTED')).toBeInTheDocument();
    
    // Check for quit confirmation UI
    expect(screen.getByText('Are you sure you wish to quit exam?')).toBeInTheDocument();
  });

  it('displays correct UI when quiz is fully submitted (completed)', async () => {
    api.getQuizSubmissionStatus.mockResolvedValueOnce({
      status: 'completed',
      attempted_count: 5,
      not_attempted_count: 0,
      percent: 80,
      questions: [
        { id: 1, title: 'Question 1', attempted: true }
      ]
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Quiz Submitted Successfully')).toBeInTheDocument();
      expect(screen.getByText('Score: 80%')).toBeInTheDocument();
    });
  });

  it('handles quit quiz logic', async () => {
    api.getQuizSubmissionStatus.mockResolvedValue({
      status: 'in_progress',
      questions: []
    });
    api.quitQuiz.mockResolvedValueOnce({ success: true });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Yes, Quit/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Yes, Quit/i }));

    await waitFor(() => {
      expect(api.quitQuiz).toHaveBeenCalledWith('100');
    });
  });
});
