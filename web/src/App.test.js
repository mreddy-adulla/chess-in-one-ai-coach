import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders chess app title', () => {
  render(<App />);
  const titleElement = screen.getByText(/chess-in-one ai coach/i);
  expect(titleElement).toBeInTheDocument();
});