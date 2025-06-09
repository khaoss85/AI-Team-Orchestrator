'use client';

import React from 'react';

interface SimpleCalendarViewerProps {
  calendar: any[];
  executiveSummary?: string;
}

const SimpleCalendarViewer: React.FC<SimpleCalendarViewerProps> = ({ calendar, executiveSummary }) => {
  console.log('🔍 SimpleCalendarViewer received:', { 
    calendarLength: calendar.length,
    hasExecutiveSummary: !!executiveSummary 
  });

  return (
    <div className="p-4">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <h2 className="text-xl font-bold text-blue-800 mb-2">📅 Instagram Editorial Calendar</h2>
        <p className="text-blue-700">Found {calendar.length} posts in the calendar</p>
        {executiveSummary && (
          <p className="text-sm text-blue-600 mt-2">{executiveSummary}</p>
        )}
      </div>

      <div className="space-y-4">
        {calendar.map((post, index) => {
          console.log(`🔍 Rendering post ${index + 1}:`, {
            date: post.date,
            type: post.type,
            hasCaption: !!post.caption,
            hashtagsType: typeof post.hashtags,
            hashtags: post.hashtags
          });

          return (
            <div key={index} className="bg-white border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-gray-900">
                  Post #{index + 1} - {post.type}
                </h3>
                <span className="text-sm text-gray-500">{post.date}</span>
              </div>
              
              {post.caption && (
                <div className="mb-2">
                  <p className="text-sm text-gray-700 bg-gray-50 p-2 rounded">
                    {post.caption.substring(0, 200)}
                    {post.caption.length > 200 && '...'}
                  </p>
                </div>
              )}
              
              {post.hashtags && (
                <div className="mb-2">
                  <div className="text-xs text-blue-600">
                    Hashtags: {Array.isArray(post.hashtags) ? post.hashtags.join(', ') : post.hashtags}
                  </div>
                </div>
              )}
              
              {post.engagement && (
                <div className="text-xs text-green-600">
                  📢 {post.engagement}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-6 bg-gray-50 border rounded-lg p-4">
        <h3 className="font-medium text-gray-800 mb-2">📊 Summary</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>Total Posts: <strong>{calendar.length}</strong></div>
          <div>Reels: <strong>{calendar.filter(p => p.type === 'Reel').length}</strong></div>
          <div>Carousels: <strong>{calendar.filter(p => p.type === 'Carousel').length}</strong></div>
          <div>Videos: <strong>{calendar.filter(p => p.type === 'Video').length}</strong></div>
        </div>
      </div>
    </div>
  );
};

export default SimpleCalendarViewer;