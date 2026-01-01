import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import GameSubmission from './GameSubmission';

describe('GameSubmission', () => {
  const mockOnToggleDone = jest.fn();
  const mockOnSubmit = jest.fn();
  const mockOnContinue = jest.fn();

  beforeEach(() => {
    mockOnToggleDone.mockClear();
    mockOnSubmit.mockClear();
    mockOnContinue.mockClear();
  });

  test('does not render when canSubmit is false', () => {
    const { container } = render(
      <GameSubmission
        canSubmit={false}
        isDone={false}
        onToggleDone={mockOnToggleDone}
        onSubmit={mockOnSubmit}
        onContinue={mockOnContinue}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  test('shows "I\'m Done Annotating" button when not done', () => {
    render(
      <GameSubmission
        canSubmit={true}
        isDone={false}
        onToggleDone={mockOnToggleDone}
        onSubmit={mockOnSubmit}
        onContinue={mockOnContinue}
      />
    );

    expect(screen.getByText("I'm Done Annotating")).toBeInTheDocument();
  });

  test('calls onToggleDone when done button is clicked', () => {
    render(
      <GameSubmission
        canSubmit={true}
        isDone={false}
        onToggleDone={mockOnToggleDone}
        onSubmit={mockOnSubmit}
        onContinue={mockOnContinue}
      />
    );

    fireEvent.click(screen.getByText("I'm Done Annotating"));
    expect(mockOnToggleDone).toHaveBeenCalled();
  });

  test('shows submit UI when isDone is true', () => {
    render(
      <GameSubmission
        canSubmit={true}
        isDone={true}
        onToggleDone={mockOnToggleDone}
        onSubmit={mockOnSubmit}
        onContinue={mockOnContinue}
      />
    );

    expect(screen.getByText('🚀 Submit for AI Coaching')).toBeInTheDocument();
    expect(screen.getByText('← Continue annotating')).toBeInTheDocument();
    expect(screen.getByText(/Ready to submit/)).toBeInTheDocument();
  });

  test('calls onSubmit when submit button is clicked', () => {
    render(
      <GameSubmission
        canSubmit={true}
        isDone={true}
        onToggleDone={mockOnToggleDone}
        onSubmit={mockOnSubmit}
        onContinue={mockOnContinue}
      />
    );

    fireEvent.click(screen.getByText('🚀 Submit for AI Coaching'));
    expect(mockOnSubmit).toHaveBeenCalled();
  });

  test('calls onContinue when continue button is clicked', () => {
    render(
      <GameSubmission
        canSubmit={true}
        isDone={true}
        onToggleDone={mockOnToggleDone}
        onSubmit={mockOnSubmit}
        onContinue={mockOnContinue}
      />
    );

    fireEvent.click(screen.getByText('← Continue annotating'));
    expect(mockOnContinue).toHaveBeenCalled();
  });
});