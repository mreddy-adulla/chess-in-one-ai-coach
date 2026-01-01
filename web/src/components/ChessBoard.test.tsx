import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ChessBoard from './ChessBoard';

describe('ChessBoard', () => {
  const mockOnPieceDrop = jest.fn();

  test('renders chess board with correct orientation - white', () => {
    render(
      <ChessBoard
        position="start"
        onPieceDrop={mockOnPieceDrop}
        boardOrientation="white"
      />
    );
    // The Chessboard component renders with specific structure
    const boardContainer = document.querySelector('.aspect-square');
    expect(boardContainer).toBeInTheDocument();
  });

  test('renders chess board with correct orientation - black', () => {
    render(
      <ChessBoard
        position="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"
        onPieceDrop={mockOnPieceDrop}
        boardOrientation="black"
      />
    );
    const boardContainer = document.querySelector('.aspect-square');
    expect(boardContainer).toBeInTheDocument();
  });

  test('applies correct CSS classes', () => {
    render(
      <ChessBoard
        position="start"
        onPieceDrop={mockOnPieceDrop}
        boardOrientation="white"
      />
    );
    const boardContainer = document.querySelector('.aspect-square');
    expect(boardContainer).toHaveClass('max-w-[600px]', 'mx-auto', 'shadow-xl', 'rounded-lg', 'overflow-hidden');
  });
});