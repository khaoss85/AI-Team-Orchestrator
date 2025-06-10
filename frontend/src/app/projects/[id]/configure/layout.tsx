'use client';

import React from 'react';

interface Props {
  children: React.ReactNode;
}

export default function ConfigureLayout({ children }: Props) {
  // Layout semplice senza menu di navigazione
  return (
    <div>
      {children}
    </div>
  );
}