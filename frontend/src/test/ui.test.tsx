import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

describe('cn', () => {
  it('joins class names', () => {
    expect(cn('a', 'b', 'c')).toBe('a b c');
  });
  it('handles conditional classes', () => {
    expect(cn('a', false && 'b', 'c')).toBe('a c');
  });
  it('merges tailwind classes preferring later values', () => {
    expect(cn('p-2', 'p-4')).toBe('p-4');
  });
});

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('fires onClick', async () => {
    let clicked = false;
    render(<Button onClick={() => (clicked = true)}>Go</Button>);
    await userEvent.click(screen.getByText('Go'));
    expect(clicked).toBe(true);
  });

  it('applies the destructive variant class', () => {
    render(<Button variant="destructive">Delete</Button>);
    const el = screen.getByText('Delete');
    expect(el.className).toMatch(/destructive/);
  });
});
