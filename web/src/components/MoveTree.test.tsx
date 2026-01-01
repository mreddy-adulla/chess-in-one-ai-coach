import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import MoveTree from './MoveTree';

describe('MoveTree', () => {
  const mockOnMoveClick = jest.fn();
  const mockMoves = [
    { san: 'e4' } as any,
    { san: 'e5' } as any,
    { san: 'Nf3' } as any,
  ];
  const mockAnnotations = { 2: 'Good move' }; // For move index 1 (e5)

  beforeEach(() => {
    mockOnMoveClick.mockClear();
  });

  test('renders move tree title', () => {
    render(
      <MoveTree
        moveHistory={mockMoves}
        annotations={mockAnnotations}
        currentMoveIndex={0}
        onMoveClick={mockOnMoveClick}
      />
    );

    expect(screen.getByText('Move Tree')).toBeInTheDocument();
  });

  test('renders moves with correct notation', () => {
    render(
      <MoveTree
        moveHistory={mockMoves}
        annotations={mockAnnotations}
        currentMoveIndex={0}
        onMoveClick={mockOnMoveClick}
      />
    );

    // Check that the move texts are present (they're split into spans)
    expect(screen.getByText('e4')).toBeInTheDocument();
    expect(screen.getByText('e5')).toBeInTheDocument();
    expect(screen.getByText('Nf3')).toBeInTheDocument();
  });

  test('highlights current move', () => {
    render(
      <MoveTree
        moveHistory={mockMoves}
        annotations={mockAnnotations}
        currentMoveIndex={1}
        onMoveClick={mockOnMoveClick}
      />
    );

    // Find the div containing e5 that is highlighted
    const moveDivs = screen.getAllByText('e5').map(el => el.closest('div'));
    const currentMove = moveDivs.find(div => div?.classList.contains('bg-slate-800'));
    expect(currentMove).toBeInTheDocument();
  });

  test('shows annotation indicator for moves with annotations', () => {
    render(
      <MoveTree
        moveHistory={mockMoves}
        annotations={mockAnnotations}
        currentMoveIndex={0}
        onMoveClick={mockOnMoveClick}
      />
    );

    // The second move (e5) has annotation at key 2, so should show indicator
    const e5Divs = screen.getAllByText('e5').map(el => el.closest('div'));
    const annotatedMove = e5Divs.find(div => div?.textContent?.includes('●'));
    expect(annotatedMove).toBeInTheDocument();
  });

  test('calls onMoveClick when move is clicked', () => {
    render(
      <MoveTree
        moveHistory={mockMoves}
        annotations={mockAnnotations}
        currentMoveIndex={0}
        onMoveClick={mockOnMoveClick}
      />
    );

    // Click on the div containing e5
    const e5Div = screen.getByText('e5').closest('div');
    fireEvent.click(e5Div!);
    expect(mockOnMoveClick).toHaveBeenCalledWith(1);
  });

  test('shows no moves message when empty', () => {
    render(
      <MoveTree
        moveHistory={[]}
        annotations={{}}
        currentMoveIndex={-1}
        onMoveClick={mockOnMoveClick}
      />
    );

    expect(screen.getByText('No moves entered yet.')).toBeInTheDocument();
  });

  test('applies correct CSS classes', () => {
    render(
      <MoveTree
        moveHistory={mockMoves}
        annotations={mockAnnotations}
        currentMoveIndex={0}
        onMoveClick={mockOnMoveClick}
      />
    );

    const container = screen.getByText('Move Tree').closest('div');
    expect(container).toHaveClass('bg-white', 'border', 'rounded-xl', 'shadow-sm', 'h-[300px]');
  });
});