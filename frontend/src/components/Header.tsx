"use client"

import React from 'react';
import Link from 'next/link';

const Header = () => {
  return (
    <header className="bg-white shadow h-16 flex items-center px-6 justify-between">
      <div className="flex items-center space-x-4">
        <span className="font-medium text-gray-800">AI Team Orchestrator</span>
      </div>
      <div className="flex items-center space-x-4">
        <button className="px-4 py-2 rounded-md bg-gray-100 text-gray-700 text-sm">
          Documentazione
        </button>
        <div className="h-8 w-8 rounded-full bg-indigo-600 flex items-center justify-center text-white">
          U
        </div>
      </div>
    </header>
  );
};

export default Header;