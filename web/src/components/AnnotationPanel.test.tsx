import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import AnnotationPanel from './AnnotationPanel';

describe('AnnotationPanel', () => {
  const mockOnAnnotationChange = jest.fn();
  const mockOnSaveAnnotation = jest.fn();
  const mockStartVoiceInput = jest.fn();

  beforeEach(() => {
    mockOnAnnotationChange.mockClear();
    mockOnSaveAnnotation.mockClear();
    mockStartVoiceInput.mockClear();
  });

  test('renders self-review title', () => {
    render(
      <AnnotationPanel
        annotation=""
        onAnnotationChange={mockOnAnnotationChange}
        onSaveAnnotation={mockOnSaveAnnotation}
        startVoiceInput={mockStartVoiceInput}
        isListening={false}
        canEdit={true}
        currentMoveText="e4"
      />
    );

    expect(screen.getByText('Self-Review')).toBeInTheDocument();
  });

  test('displays annotation in textarea', () => {
    const testAnnotation = 'This is a test annotation';
    render(
      <AnnotationPanel
        annotation={testAnnotation}
        onAnnotationChange={mockOnAnnotationChange}
        onSaveAnnotation={mockOnSaveAnnotation}
        startVoiceInput={mockStartVoiceInput}
        isListening={false}
        canEdit={true}
        currentMoveText="e4"
      />
    );

    const textarea = screen.getByDisplayValue(testAnnotation);
    expect(textarea).toBeInTheDocument();
  });

  test('shows currentMoveText as placeholder when canEdit is true', () => {
    render(
      <AnnotationPanel
        annotation=""
        onAnnotationChange={mockOnAnnotationChange}
        onSaveAnnotation={mockOnSaveAnnotation}
        startVoiceInput={mockStartVoiceInput}
        isListening={false}
        canEdit={true}
        currentMoveText="Nf3"
      />
    );

    const textarea = screen.getByPlaceholderText('Nf3');
    expect(textarea).toBeInTheDocument();
  });

  test('shows locked placeholder when canEdit is false', () => {
    render(
      <AnnotationPanel
        annotation=""
        onAnnotationChange={mockOnAnnotationChange}
        onSaveAnnotation={mockOnSaveAnnotation}
        startVoiceInput={mockStartVoiceInput}
        isListening={false}
        canEdit={false}
        currentMoveText="e4"
      />
    );

    const textarea = screen.getByPlaceholderText('Annotations are locked.');
    expect(textarea).toBeInTheDocument();
  });

  test('textarea is disabled when canEdit is false', () => {
    render(
      <AnnotationPanel
        annotation=""
        onAnnotationChange={mockOnAnnotationChange}
        onSaveAnnotation={mockOnSaveAnnotation}
        startVoiceInput={mockStartVoiceInput}
        isListening={false}
        canEdit={false}
        currentMoveText="e4"
      />
    );

    const textarea = screen.getByPlaceholderText('Annotations are locked.');
    expect(textarea).toBeDisabled();
  });

  test('calls onAnnotationChange when textarea value changes', () => {
    render(
      <AnnotationPanel
        annotation=""
        onAnnotationChange={mockOnAnnotationChange}
        onSaveAnnotation={mockOnSaveAnnotation}
        startVoiceInput={mockStartVoiceInput}
        isListening={false}
        canEdit={true}
        currentMoveText="e4"
      />
    );

    const textarea = screen.getByPlaceholderText('e4');
    fireEvent.change(textarea, { target: { value: 'New annotation' } });
    expect(mockOnAnnotationChange).toHaveBeenCalledWith('New annotation');
  });

  test('shows voice input button when canEdit is true', () => {
    render(
      <AnnotationPanel
        annotation=""
        onAnnotationChange={mockOnAnnotationChange}
        onSaveAnnotation={mockOnSaveAnnotation}
        startVoiceInput={mockStartVoiceInput}
        isListening={false}
        canEdit={true}
        currentMoveText="e4"
      />
    );

    expect(screen.getAllByTitle('Voice Input')).toHaveLength(2); // Header and bottom button
  });

  test('hides voice input button when canEdit is false', () => {
    render(
      <AnnotationPanel
        annotation=""
        onAnnotationChange={mockOnAnnotationChange}
        onSaveAnnotation={mockOnSaveAnnotation}
        startVoiceInput={mockStartVoiceInput}
        isListening={false}
        canEdit={false}
        currentMoveText="e4"
      />
    );

    expect(screen.queryByTitle('Voice Input')).not.toBeInTheDocument();
  });

  test('shows save button when canEdit is true', () => {
    render(
      <AnnotationPanel
        annotation="Some annotation"
        onAnnotationChange={mockOnAnnotationChange}
        onSaveAnnotation={mockOnSaveAnnotation}
        startVoiceInput={mockStartVoiceInput}
        isListening={false}
        canEdit={true}
        currentMoveText="e4"
      />
    );

    expect(screen.getByText('Save Move Note')).toBeInTheDocument();
  });

  test('save button is disabled when annotation is empty', () => {
    render(
      <AnnotationPanel
        annotation=""
        onAnnotationChange={mockOnAnnotationChange}
        onSaveAnnotation={mockOnSaveAnnotation}
        startVoiceInput={mockStartVoiceInput}
        isListening={false}
        canEdit={true}
        currentMoveText="e4"
      />
    );

    const saveButton = screen.getByText('Save Move Note');
    expect(saveButton).toBeDisabled();
  });

  test('calls onSaveAnnotation when save button is clicked', () => {
    render(
      <AnnotationPanel
        annotation="Some annotation"
        onAnnotationChange={mockOnAnnotationChange}
        onSaveAnnotation={mockOnSaveAnnotation}
        startVoiceInput={mockStartVoiceInput}
        isListening={false}
        canEdit={true}
        currentMoveText="e4"
      />
    );

    const saveButton = screen.getByText('Save Move Note');
    fireEvent.click(saveButton);
    expect(mockOnSaveAnnotation).toHaveBeenCalled();
  });

  test('calls startVoiceInput when voice button is clicked', () => {
    render(
      <AnnotationPanel
        annotation=""
        onAnnotationChange={mockOnAnnotationChange}
        onSaveAnnotation={mockOnSaveAnnotation}
        startVoiceInput={mockStartVoiceInput}
        isListening={false}
        canEdit={true}
        currentMoveText="e4"
      />
    );

    const voiceButtons = screen.getAllByTitle('Voice Input');
    fireEvent.click(voiceButtons[0]); // Click the first one
    expect(mockStartVoiceInput).toHaveBeenCalled();
  });

  test('applies listening styles when isListening is true', () => {
    render(
      <AnnotationPanel
        annotation=""
        onAnnotationChange={mockOnAnnotationChange}
        onSaveAnnotation={mockOnSaveAnnotation}
        startVoiceInput={mockStartVoiceInput}
        isListening={true}
        canEdit={true}
        currentMoveText="e4"
      />
    );

    // Check that the voice button has listening classes
    const voiceButtons = screen.getAllByTitle('Voice Input');
    expect(voiceButtons[0]).toHaveClass('bg-red-100', 'text-red-600', 'animate-pulse');
  });
});