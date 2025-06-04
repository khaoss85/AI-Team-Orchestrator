import React from 'react';

interface Props {
  count: number;
  max?: number;
}

export const IterationCounter: React.FC<Props> = ({ count, max }) => (
  <span className="text-sm text-gray-600">Iteration {count}{max ? ` / ${max}` : ''}</span>
);
