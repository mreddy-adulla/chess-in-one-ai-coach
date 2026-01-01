import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import MoveNavigator from './MoveNavigator';
import { Move } from 'chess.js';

describe('MoveNavigator', () => {
  const mockOnNavigate = jest.fn();
  const mockMoves = [
    { from: 'e2', to: 'e4', piece: 'p' } as Move,
    { from: 'e7', to: 'e5', piece: 'p' } as Move,
    { from: 'g1', to: 'f3', piece: 'n' } as Move,
  ];

  beforeEach(() => {
    mockOnNavigate.mockClear();
  });

  test('renders navigation buttons', () => {
    render(
      <MoveNavigator
        moveHistory={mockMoves}
        currentMoveIndex={1}
        onNavigate={mockOnNavigate}
      />
    );

    expect(screen.getByTitle('First Move')).toBeInTheDocument();
    expect(screen.getByTitle('Previous Move')).toBeInTheDocument();
    expect(screen.getByTitle('Next Move')).toBeInTheDocument();
    expect(screen.getByTitle('Last Move')).toBeInTheDocument();
  });

  test('displays correct move notation for current position', () => {
    render(
      <MoveNavigator
        moveHistory={mockMoves}
        currentMoveIndex={1}
        onNavigate={mockOnNavigate}
      />
    );

    expect(screen.getByText('Move 1...')).toBeInTheDocument();
  });

  test('displays "Starting Position" when at index -1', () => {
    render(
      <MoveNavigator
        moveHistory={mockMoves}
        currentMoveIndex={-1}
        onNavigate={mockOnNavigate}
      />
    );

    expect(screen.getByText('Starting Position')).toBeInTheDocument();
  });

  test('calls onNavigate with -1 for first move button', () => {
    render(
      <MoveNavigator
        moveHistory={mockMoves}
        currentMoveIndex={1}
        onNavigate={mockOnNavigate}
      />
    );

    fireEvent.click(screen.getByTitle('First Move'));
    expect(mockOnNavigate).toHaveBeenCalledWith(-1);
  });

  test('calls onNavigate with currentMoveIndex - 1 for previous button', () => {
    render(
      <MoveNavigator
        moveHistory={mockMoves}
        currentMoveIndex={2}
        onNavigate={mockOnNavigate}
      />
    );

    fireEvent.click(screen.getByTitle('Previous Move'));
    expect(mockOnNavigate).toHaveBeenCalledWith(1);
  });

  test('calls onNavigate with currentMoveIndex + 1 for next button', () => {
    render(
      <MoveNavigator
        moveHistory={mockMoves}
        currentMoveIndex={1}
        onNavigate={mockOnNavigate}
      />
    );

    fireEvent.click(screen.getByTitle('Next Move'));
    expect(mockOnNavigate).toHaveBeenCalledWith(2);
  });

  test('calls onNavigate with moveHistory.length - 1 for last move button', () => {
    render(
      <MoveNavigator
        moveHistory={mockMoves}
        currentMoveIndex={0}
        onNavigate={mockOnNavigate}
      />
    );

    fireEvent.click(screen.getByTitle('Last Move'));
    expect(mockOnNavigate).toHaveBeenCalledWith(2);
  });


});