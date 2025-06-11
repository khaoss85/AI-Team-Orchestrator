// frontend/src/components/StructuredAssetRenderer.tsx
'use client';

import React, { useState, useMemo } from 'react';

// Simple icon components
const ChevronUpIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
  </svg>
);

const ChevronDownIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
  </svg>
);

const FunnelIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
  </svg>
);

const ArrowDownTrayIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
  </svg>
);

const TableCellsIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
  </svg>
);

const CreditCardIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
  </svg>
);

const ClockIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const ChartBarIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

interface ProcessedMarkup {
  tables: TableData[];
  cards: CardData[];
  timelines: TimelineData[];
  metrics: MetricData[];
  plain_text?: string;
  has_structured_content: boolean;
}

interface TableData {
  type: 'table';
  name: string;
  display_name: string;
  headers: string[];
  rows: Record<string, any>[];
  row_count: number;
  column_count: number;
  metadata: {
    sortable: boolean;
    filterable: boolean;
    exportable: boolean;
    type?: 'calendar' | 'contacts' | 'scoring';
  };
}

interface CardData {
  type: 'card';
  card_type: string;
  fields: {
    title?: string;
    subtitle?: string;
    content?: string;
    action?: string;
    metadata?: string;
  };
  style: 'contact' | 'social' | 'action' | 'default';
  icon: string;
}

interface TimelineData {
  type: 'timeline';
  name: string;
  display_name: string;
  entries: Array<{
    date: string;
    event: string;
    status: string;
    parsed_date?: string;
  }>;
  entry_count: number;
}

interface MetricData {
  type: 'metric';
  name: string;
  display_name: string;
  value: number | string;
  unit?: string;
  trend?: string;
  trend_icon?: string;
  trend_color?: string;
  target?: number;
  percentage_to_target?: number;
}

interface StructuredAssetRendererProps {
  data: ProcessedMarkup;
  onExport?: (format: string) => void;
}

const StructuredAssetRenderer: React.FC<StructuredAssetRendererProps> = ({ data, onExport }) => {
  // Ensure data has default values
  const safeData = {
    ...data,
    tables: data.tables || [],
    cards: data.cards || [],
    timelines: data.timelines || [],
    metrics: data.metrics || [],
    has_structured_content: data.has_structured_content !== undefined ? data.has_structured_content : true
  };
  
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    tables: true,
    cards: true,
    timelines: true,
    metrics: true
  });

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  if (!safeData.has_structured_content) {
    return (
      <div className="bg-gray-50 rounded-lg p-6 text-gray-600">
        <p>No structured content available. Displaying raw content:</p>
        <pre className="mt-4 whitespace-pre-wrap font-mono text-sm">
          {safeData.plain_text || 'No content'}
        </pre>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Metrics Section - Always show first if available */}
      {safeData.metrics.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div 
            className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-4 cursor-pointer"
            onClick={() => toggleSection('metrics')}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <ChartBarIcon className="w-6 h-6" />
                <h3 className="text-lg font-semibold">Key Metrics</h3>
                <span className="bg-white/20 px-2 py-1 rounded-full text-sm">
                  {safeData.metrics.length} metrics
                </span>
              </div>
              {expandedSections.metrics ? 
                <ChevronUpIcon className="w-5 h-5" /> : 
                <ChevronDownIcon className="w-5 h-5" />
              }
            </div>
          </div>
          
          {expandedSections.metrics && (
            <div className="p-6">
              <MetricsGrid metrics={safeData.metrics} />
            </div>
          )}
        </div>
      )}

      {/* Tables Section */}
      {safeData.tables.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div 
            className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white p-4 cursor-pointer"
            onClick={() => toggleSection('tables')}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <TableCellsIcon className="w-6 h-6" />
                <h3 className="text-lg font-semibold">Data Tables</h3>
                <span className="bg-white/20 px-2 py-1 rounded-full text-sm">
                  {safeData.tables.length} tables
                </span>
              </div>
              {expandedSections.tables ? 
                <ChevronUpIcon className="w-5 h-5" /> : 
                <ChevronDownIcon className="w-5 h-5" />
              }
            </div>
          </div>
          
          {expandedSections.tables && (
            <div className="p-6 space-y-6">
              {safeData.tables.map((table, idx) => (
                <EnhancedTable key={idx} table={table} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Cards Section */}
      {safeData.cards.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div 
            className="bg-gradient-to-r from-emerald-600 to-green-600 text-white p-4 cursor-pointer"
            onClick={() => toggleSection('cards')}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <CreditCardIcon className="w-6 h-6" />
                <h3 className="text-lg font-semibold">Action Cards</h3>
                <span className="bg-white/20 px-2 py-1 rounded-full text-sm">
                  {safeData.cards.length} cards
                </span>
              </div>
              {expandedSections.cards ? 
                <ChevronUpIcon className="w-5 h-5" /> : 
                <ChevronDownIcon className="w-5 h-5" />
              }
            </div>
          </div>
          
          {expandedSections.cards && (
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {safeData.cards.map((card, idx) => (
                  <StructuredCard key={idx} card={card} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Timelines Section */}
      {safeData.timelines.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div 
            className="bg-gradient-to-r from-orange-600 to-red-600 text-white p-4 cursor-pointer"
            onClick={() => toggleSection('timelines')}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <ClockIcon className="w-6 h-6" />
                <h3 className="text-lg font-semibold">Timelines</h3>
                <span className="bg-white/20 px-2 py-1 rounded-full text-sm">
                  {safeData.timelines.length} timelines
                </span>
              </div>
              {expandedSections.timelines ? 
                <ChevronUpIcon className="w-5 h-5" /> : 
                <ChevronDownIcon className="w-5 h-5" />
              }
            </div>
          </div>
          
          {expandedSections.timelines && (
            <div className="p-6 space-y-6">
              {safeData.timelines.map((timeline, idx) => (
                <TimelineVisualization key={idx} timeline={timeline} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Export Button */}
      {onExport && (
        <div className="flex justify-end space-x-3">
          <button
            onClick={() => onExport('json')}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition"
          >
            <ArrowDownTrayIcon className="w-5 h-5" />
            <span>Export JSON</span>
          </button>
          <button
            onClick={() => onExport('csv')}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition"
          >
            <ArrowDownTrayIcon className="w-5 h-5" />
            <span>Export CSV</span>
          </button>
          <button
            onClick={() => onExport('html')}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition"
          >
            <ArrowDownTrayIcon className="w-5 h-5" />
            <span>Export HTML</span>
          </button>
        </div>
      )}
    </div>
  );
};

// Enhanced Table Component with sorting and filtering
const EnhancedTable: React.FC<{ table: TableData }> = ({ table }) => {
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [filterText, setFilterText] = useState('');

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const filteredAndSortedRows = useMemo(() => {
    let rows = [...table.rows];

    // Filter
    if (filterText) {
      rows = rows.filter(row => 
        Object.values(row).some(value => 
          String(value).toLowerCase().includes(filterText.toLowerCase())
        )
      );
    }

    // Sort
    if (sortColumn) {
      rows.sort((a, b) => {
        const aVal = a[sortColumn];
        const bVal = b[sortColumn];
        
        if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return rows;
  }, [table.rows, filterText, sortColumn, sortDirection]);

  const getTableStyle = () => {
    switch (table.metadata.type) {
      case 'calendar':
        return 'border-purple-200';
      case 'contacts':
        return 'border-blue-200';
      case 'scoring':
        return 'border-green-200';
      default:
        return 'border-gray-200';
    }
  };

  return (
    <div className={`border rounded-lg overflow-hidden ${getTableStyle()}`}>
      <div className="bg-gray-50 px-4 py-3 border-b">
        <div className="flex items-center justify-between">
          <h4 className="font-medium text-gray-900">{table.display_name}</h4>
          {table.metadata.filterable && (
            <div className="flex items-center space-x-2">
              <FunnelIcon className="w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Filter..."
                value={filterText}
                onChange={(e) => setFilterText(e.target.value)}
                className="px-3 py-1 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              {table.headers.map((header, idx) => (
                <th
                  key={idx}
                  className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
                    table.metadata.sortable ? 'cursor-pointer hover:bg-gray-100' : ''
                  }`}
                  onClick={() => table.metadata.sortable && handleSort(header)}
                >
                  <div className="flex items-center space-x-1">
                    <span>{header}</span>
                    {table.metadata.sortable && sortColumn === header && (
                      <span className="text-blue-600">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredAndSortedRows.map((row, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                {table.headers.map((header, cellIdx) => (
                  <td key={cellIdx} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <CellRenderer value={row[header]} columnType={header.toLowerCase()} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div className="bg-gray-50 px-4 py-2 border-t text-sm text-gray-600">
        Showing {filteredAndSortedRows.length} of {table.row_count} rows
      </div>
    </div>
  );
};

// Cell Renderer for special formatting
const CellRenderer: React.FC<{ value: any; columnType: string }> = ({ value, columnType }) => {
  // Email formatting
  if (columnType.includes('email') && value && value.includes('@')) {
    return (
      <a href={`mailto:${value}`} className="text-blue-600 hover:underline">
        {value}
      </a>
    );
  }
  
  // Score formatting
  if (columnType.includes('score') && value) {
    const numValue = parseFloat(String(value).replace(/[^0-9.]/g, ''));
    const maxValue = String(value).includes('/') ? 
      parseFloat(String(value).split('/')[1]) : 10;
    const percentage = (numValue / maxValue) * 100;
    
    return (
      <div className="flex items-center space-x-2">
        <div className="w-20 bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full ${
              percentage >= 80 ? 'bg-green-500' : 
              percentage >= 60 ? 'bg-yellow-500' : 'bg-red-500'
            }`}
            style={{ width: `${percentage}%` }}
          />
        </div>
        <span className="text-sm font-medium">{value}</span>
      </div>
    );
  }
  
  // Date formatting
  if (columnType.includes('date') && value) {
    try {
      const date = new Date(value);
      if (!isNaN(date.getTime())) {
        return <span>{date.toLocaleDateString()}</span>;
      }
    } catch {}
  }
  
  // Hashtag formatting
  if (String(value).includes('#')) {
    const parts = String(value).split(/(\#\w+)/g);
    return (
      <span>
        {parts.map((part, idx) => 
          part.startsWith('#') ? (
            <span key={idx} className="text-blue-600 font-medium">{part}</span>
          ) : part
        )}
      </span>
    );
  }
  
  return <span>{value}</span>;
};

// Structured Card Component
const StructuredCard: React.FC<{ card: CardData }> = ({ card }) => {
  const getCardStyle = () => {
    switch (card.style) {
      case 'contact':
        return 'border-blue-200 bg-blue-50';
      case 'social':
        return 'border-purple-200 bg-purple-50';
      case 'action':
        return 'border-green-200 bg-green-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  return (
    <div className={`rounded-lg p-6 border-2 ${getCardStyle()} hover:shadow-lg transition-shadow`}>
      <div className="flex items-start justify-between mb-4">
        <div className="text-3xl">{card.icon}</div>
        <span className="text-xs font-medium text-gray-500 uppercase">
          {card.card_type.replace(/_/g, ' ')}
        </span>
      </div>
      
      {card.fields.title && (
        <h4 className="text-lg font-semibold text-gray-900 mb-2">
          {card.fields.title}
        </h4>
      )}
      
      {card.fields.subtitle && (
        <p className="text-sm text-gray-600 mb-3">
          {card.fields.subtitle}
        </p>
      )}
      
      {card.fields.content && (
        <div className="text-sm text-gray-700 mb-4 whitespace-pre-line">
          {card.fields.content}
        </div>
      )}
      
      {card.fields.action && (
        <button className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition">
          {card.fields.action}
        </button>
      )}
      
      {card.fields.metadata && (
        <div className="mt-3 pt-3 border-t border-gray-200 text-xs text-gray-500">
          {card.fields.metadata}
        </div>
      )}
    </div>
  );
};

// Timeline Visualization Component
const TimelineVisualization: React.FC<{ timeline: TimelineData }> = ({ timeline }) => {
  const sortedEntries = useMemo(() => {
    return [...timeline.entries].sort((a, b) => {
      const dateA = new Date(a.parsed_date || a.date).getTime();
      const dateB = new Date(b.parsed_date || b.date).getTime();
      return dateA - dateB;
    });
  }, [timeline.entries]);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'bg-green-500';
      case 'in_progress':
        return 'bg-yellow-500';
      case 'upcoming':
        return 'bg-blue-500';
      default:
        return 'bg-gray-400';
    }
  };

  return (
    <div>
      <h4 className="font-medium text-gray-900 mb-4">{timeline.display_name}</h4>
      <div className="relative">
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-300"></div>
        {sortedEntries.map((entry, idx) => (
          <div key={idx} className="relative flex items-start mb-6">
            <div className={`absolute left-2.5 w-3 h-3 rounded-full ${getStatusColor(entry.status)} ring-4 ring-white`}></div>
            <div className="ml-10">
              <div className="flex items-center space-x-2 text-sm text-gray-500 mb-1">
                <span className="font-medium">{entry.date}</span>
                <span className={`px-2 py-0.5 rounded-full text-xs text-white ${getStatusColor(entry.status)}`}>
                  {entry.status}
                </span>
              </div>
              <p className="text-gray-900">{entry.event}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Metrics Grid Component
const MetricsGrid: React.FC<{ metrics: MetricData[] }> = ({ metrics }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric, idx) => (
        <div key={idx} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="text-sm text-gray-600 mb-1">{metric.display_name}</div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-gray-900">{metric.value}</span>
            {metric.unit && (
              <span className="text-sm text-gray-500">{metric.unit}</span>
            )}
            {metric.trend_icon && (
              <span className={`text-lg ${
                metric.trend_color === 'green' ? 'text-green-500' : 
                metric.trend_color === 'red' ? 'text-red-500' : 'text-gray-500'
              }`}>
                {metric.trend_icon}
              </span>
            )}
          </div>
          {metric.percentage_to_target && (
            <div className="mt-2">
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>Progress</span>
                <span>{metric.percentage_to_target}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div 
                  className="bg-blue-500 h-1.5 rounded-full"
                  style={{ width: `${Math.min(metric.percentage_to_target, 100)}%` }}
                />
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default StructuredAssetRenderer;