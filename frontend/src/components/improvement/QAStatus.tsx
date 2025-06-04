import React from 'react';

interface Props {
  approved: boolean;
}

export const QAStatus: React.FC<Props> = ({ approved }) => (
  <span className={approved ? 'text-green-600' : 'text-red-600'}>
    {approved ? 'QA Approved' : 'Needs Review'}
  </span>
);
