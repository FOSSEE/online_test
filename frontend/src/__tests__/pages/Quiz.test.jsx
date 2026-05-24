import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import Quiz from '../../pages/Quiz';
import * as api from '../../api/api';

vi.mock('../../api/api', () => ({
  startQuiz: vi.fn(),
  submitAnswer: vi.fn(),
  getAnswerResult: vi.fn(),
  quitQuiz: vi.fn(),
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useParams: () => ({ courseId: '1', quizId: '10' }),
    useNavigate: () => mockNavigate,
  };
});

describe('Quiz Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderComponent = () => {
    render(
      <BrowserRouter>
        <Quiz />
      </BrowserRouter>
    );
  };

  it('renders loading state initially', () => {
    api.startQuiz.mockImplementationOnce(() => new Promise(() => {})); // Never resolves
    renderComponent();
    expect(screen.getByText('Loading quiz...')).toBeInTheDocument();
  });

  it('renders error state on API failure', async () => {
    api.startQuiz.mockRejectedValueOnce({ response: { data: { message: 'Quiz not ready' } } });
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Quiz not ready')).toBeInTheDocument();
    });
  });

  it('renders quiz questions on success', async () => {
    api.startQuiz.mockResolvedValueOnce({
      time_left: 600,
      answerpaper: {
        id: 11,
        questions: [
          {
            id: 101,
            description: '<p>What is 2+2?</p>',
            type: 'integer',
            points: 5,
          }
        ]
      }
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Question 1 of 1')).toBeInTheDocument();
    });

    // Validates time formatting
    expect(screen.getByText('10:00')).toBeInTheDocument();
    // Validates input exists
    expect(screen.getByPlaceholderText('Enter integer...')).toBeInTheDocument();
  });

  it('submits answer correctly', async () => {
    api.startQuiz.mockResolvedValueOnce({
      time_left: 600,
      answerpaper: {
        id: 11,
        questions: [
          {
            id: 101,
            description: 'Test Question',
            type: 'string',
            points: 10,
          }
        ]
      }
    });

    api.submitAnswer.mockResolvedValueOnce({ success: true });

    renderComponent();
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Enter string...')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText('Enter string...');
    fireEvent.change(input, { target: { value: 'Test answer' } });

    const submitBtn = screen.getByRole('button', { name: /Submit Answer/i });
    expect(submitBtn).not.toBeDisabled();
    
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(api.submitAnswer).toHaveBeenCalledWith(11, 101, ['Test answer']);
    });
  });
});
