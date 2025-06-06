// frontend/src/components/MarkupDemo.tsx - Demo of structured markup rendering
'use client';

import React, { useState } from 'react';
import StructuredAssetRenderer from './StructuredAssetRenderer';

const sampleMarkupData = {
  tables: [
    {
      type: 'table',
      name: 'instagram_editorial_calendar',
      display_name: 'Instagram Editorial Calendar',
      headers: ['Date', 'Type', 'Caption Preview', 'Hashtags', 'Engagement'],
      rows: [
        {
          'Date': '15/01/2024',
          'Type': 'Carousel',
          'Caption Preview': '💪 5 ESERCIZI PER MASSA MUSCOLARE...',
          'Hashtags': '#bodybuilding #palestra #massa',
          'Engagement': 'Save post + Follow'
        },
        {
          'Date': '16/01/2024',
          'Type': 'Reel',
          'Caption Preview': 'MORNING WORKOUT ROUTINE ☀️ 6:00...',
          'Hashtags': '#morningworkout #routine',
          'Engagement': 'Comment below'
        },
        {
          'Date': '17/01/2024',
          'Type': 'Photo',
          'Caption Preview': 'MEAL PREP SUNDAY 🥗 Prepara...',
          'Hashtags': '#mealprep #nutrition',
          'Engagement': 'Tag a friend'
        }
      ],
      row_count: 3,
      column_count: 5,
      metadata: {
        sortable: true,
        filterable: true,
        exportable: true,
        type: 'calendar'
      }
    },
    {
      type: 'table',
      name: 'qualified_contacts_database',
      display_name: 'Qualified Contacts Database',
      headers: ['Name', 'Company', 'Email', 'Phone', 'Score', 'Next Action'],
      rows: [
        {
          'Name': 'Mario Rossi',
          'Company': 'TechCorp Italia',
          'Email': 'mario.rossi@techcorp.it',
          'Phone': '+39 02 1234567',
          'Score': '8/10',
          'Next Action': 'Send intro email'
        },
        {
          'Name': 'Laura Bianchi',
          'Company': 'Digital Solutions',
          'Email': 'l.bianchi@digitalsol.it',
          'Phone': '+39 06 9876543',
          'Score': '9/10',
          'Next Action': 'Schedule call'
        },
        {
          'Name': 'Giuseppe Verdi',
          'Company': 'StartupHub',
          'Email': 'g.verdi@startuphub.it',
          'Phone': '+39 02 5555555',
          'Score': '7/10',
          'Next Action': 'Nurture campaign'
        }
      ],
      row_count: 3,
      column_count: 6,
      metadata: {
        sortable: true,
        filterable: true,
        exportable: true,
        type: 'contacts'
      }
    }
  ],
  cards: [
    {
      type: 'card',
      card_type: 'hot_lead_1',
      fields: {
        title: 'Laura Bianchi - Digital Solutions',
        subtitle: 'Score: 9/10 - Hot Lead',
        content: 'Marketing Director interested in automation solutions.\nBudget: €50-75k annual\nTimeline: Q1 2024\nPain points: Manual processes, lack of integration',
        action: 'Schedule discovery call this week',
        metadata: 'Last contact: 2 days ago'
      },
      style: 'contact',
      icon: '👤'
    },
    {
      type: 'card',
      card_type: 'instagram_post_1',
      fields: {
        title: '5 ESERCIZI PER MASSA MUSCOLARE',
        subtitle: 'Carousel - 5 slides',
        content: '1. SQUAT - 4 serie x 8-10 reps\n2. PANCA PIANA - 4 serie x 6-8 reps\n3. STACCHI - 3 serie x 5-6 reps\n4. MILITARY PRESS - 3 serie x 8-10 reps\n5. TRAZIONI - 3 serie x max reps',
        action: 'Salva questo post e seguimi! 🔥',
        metadata: 'Best time to post: 18:00'
      },
      style: 'social',
      icon: '📱'
    },
    {
      type: 'card',
      card_type: 'action_item',
      fields: {
        title: 'Email Campaign Setup',
        subtitle: 'Priority: High',
        content: 'Configure automated email sequence for new leads\n- Welcome email (day 0)\n- Value content (day 3)\n- Case study (day 7)\n- Demo offer (day 14)',
        action: 'Start campaign setup',
        metadata: 'Due: End of week'
      },
      style: 'action',
      icon: '✅'
    }
  ],
  timelines: [
    {
      type: 'timeline',
      name: 'content_posting_schedule',
      display_name: 'Content Posting Schedule',
      entries: [
        {
          date: '2024-01-15',
          event: 'Carousel: 5 Esercizi per Massa',
          status: 'completed',
          parsed_date: '2024-01-15T00:00:00'
        },
        {
          date: '2024-01-16',
          event: 'Reel: Morning Workout Routine',
          status: 'in_progress',
          parsed_date: '2024-01-16T00:00:00'
        },
        {
          date: '2024-01-17',
          event: 'Photo: Meal Prep Sunday',
          status: 'upcoming',
          parsed_date: '2024-01-17T00:00:00'
        },
        {
          date: '2024-01-18',
          event: 'Story: Behind the Scenes Gym',
          status: 'upcoming',
          parsed_date: '2024-01-18T00:00:00'
        }
      ],
      entry_count: 4
    }
  ],
  metrics: [
    {
      type: 'metric',
      name: 'engagement_rate',
      display_name: 'Engagement Rate',
      value: 8.5,
      unit: 'percentage',
      trend: 'up',
      trend_icon: '↑',
      trend_color: 'green',
      target: 10,
      percentage_to_target: 85
    },
    {
      type: 'metric',
      name: 'total_qualified_leads',
      display_name: 'Total Qualified Leads',
      value: 25,
      unit: 'contacts',
      trend: 'up',
      trend_icon: '↑',
      trend_color: 'green',
      target: 30,
      percentage_to_target: 83.3
    },
    {
      type: 'metric',
      name: 'database_quality',
      display_name: 'Database Quality',
      value: 95,
      unit: 'percentage',
      trend: 'stable',
      trend_icon: '→',
      trend_color: 'gray',
      target: 90,
      percentage_to_target: 105.6
    },
    {
      type: 'metric',
      name: 'conversion_rate',
      display_name: 'Lead Conversion Rate',
      value: 12.3,
      unit: 'percentage',
      trend: 'up',
      trend_icon: '↑',
      trend_color: 'green',
      target: 15,
      percentage_to_target: 82
    }
  ],
  has_structured_content: true,
  plain_text: 'This is a demonstration of structured markup rendering with tables, cards, timelines, and metrics.'
};

const MarkupDemo: React.FC = () => {
  const [showDemo, setShowDemo] = useState(false);

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg p-6 mb-6">
          <h1 className="text-2xl font-bold mb-2">Structured Markup Demo</h1>
          <p className="text-purple-100">
            This demonstrates how our AI agents now generate beautifully structured, 
            immediately readable business assets instead of raw JSON data.
          </p>
          <button
            onClick={() => setShowDemo(!showDemo)}
            className="mt-4 bg-white text-purple-600 px-6 py-2 rounded-lg font-medium hover:bg-purple-50 transition"
          >
            {showDemo ? 'Hide Demo' : 'Show Demo'} ✨
          </button>
        </div>

        {showDemo && (
          <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4 text-gray-800">
              🎯 AI-Generated Business Assets (Structured View)
            </h2>
            <StructuredAssetRenderer 
              data={sampleMarkupData}
              onExport={(format) => {
                alert(`Export in ${format} format - Implementation ready!`);
              }}
            />
          </div>
        )}

        {showDemo && (
          <div className="mt-6 bg-gray-50 rounded-lg p-6">
            <h3 className="font-semibold text-gray-800 mb-3">🔥 Benefits:</h3>
            <ul className="space-y-2 text-gray-700">
              <li className="flex items-center space-x-2">
                <span className="text-green-500">✅</span>
                <span><strong>Immediate Readability:</strong> Tables instead of JSON objects</span>
              </li>
              <li className="flex items-center space-x-2">
                <span className="text-green-500">✅</span>
                <span><strong>Interactive Features:</strong> Sort, filter, expand/collapse</span>
              </li>
              <li className="flex items-center space-x-2">
                <span className="text-green-500">✅</span>
                <span><strong>Visual Indicators:</strong> Progress bars, trend arrows, status colors</span>
              </li>
              <li className="flex items-center space-x-2">
                <span className="text-green-500">✅</span>
                <span><strong>Export Ready:</strong> JSON, CSV, HTML formats available</span>
              </li>
              <li className="flex items-center space-x-2">
                <span className="text-green-500">✅</span>
                <span><strong>Business Focused:</strong> Email links, score bars, action buttons</span>
              </li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default MarkupDemo;