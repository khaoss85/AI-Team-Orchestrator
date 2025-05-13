"use client"

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '@/utils/api';

const Header = () => {
  const [pendingFeedbackCount, setPendingFeedbackCount] = useState(0);

  useEffect(() => {
    const fetchPendingCount = async () => {
      try {
        const requests = await api.humanFeedback.getPendingRequests();
        setPendingFeedbackCount(requests.length);
      } catch (error) {
        console.error('Error fetching pending feedback count:', error);
      }
    };

    fetchPendingCount();
    const interval = setInterval(fetchPendingCount, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="bg-white shadow h-16 flex items-center px-6 justify-between">
      <div className="flex items-center space-x-4">
        <span className="font-medium text-gray-800">AI Team Orchestrator</span>
      </div>
      <div className="flex items-center space-x-4">
        {/* Feedback Indicator */}
        {pendingFeedbackCount > 0 && (
          <Link 
            href="/human-feedback"
            className="relative px-3 py-2 text-sm bg-red-50 text-red-700 rounded-md hover:bg-red-100 transition"
          >
            <span className="font-medium">Feedback Richiesto</span>
            <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full">
              {pendingFeedbackCount}
            </span>
          </Link>
        )}
        
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