import React from 'react';

interface TableElement {
  type: string;
  name: string;
  display_name: string;
  headers: string[];
  rows: Record<string, any>[];
  row_count: number;
  metadata?: {
    sortable?: boolean;
    filterable?: boolean;
    exportable?: boolean;
    type?: string;
  };
}

interface CardElement {
  type: string;
  card_type: string;
  fields: {
    title?: string;
    subtitle?: string;
    content?: string;
    action?: string;
    metadata?: string;
  };
  style: string;
  icon: string;
}

interface MetricElement {
  type: string;
  name: string;
  display_name: string;
  value?: number | string;
  unit?: string;
  trend?: string;
  trend_icon?: string;
  trend_color?: string;
  target?: number;
  percentage_to_target?: number;
}

interface TimelineElement {
  type: string;
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

interface StructuredElements {
  tables?: TableElement[];
  cards?: CardElement[];
  metrics?: MetricElement[];
  timelines?: TimelineElement[];
}

interface StructuredContentRendererProps {
  elements: StructuredElements;
  rawData?: any;
}

export default function StructuredContentRenderer({ elements, rawData }: StructuredContentRendererProps) {
  // Render tables
  const renderTable = (table: TableElement) => (
    <div key={table.name} className="mb-6">
      <h4 className="text-lg font-semibold mb-3 text-gray-800">{table.display_name}</h4>
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border border-gray-200 rounded-lg shadow-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {table.headers.map((header, idx) => (
                <th key={idx} className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {table.rows.map((row, rowIdx) => (
              <tr key={rowIdx} className="hover:bg-gray-50 transition-colors">
                {table.headers.map((header, cellIdx) => (
                  <td key={cellIdx} className="px-4 py-3 text-sm text-gray-900">
                    {formatCellValue(row[header])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {table.metadata?.type && (
        <p className="text-xs text-gray-500 mt-1">
          Type: {table.metadata.type} • {table.row_count} rows
        </p>
      )}
    </div>
  );

  // Render cards
  const renderCard = (card: CardElement) => (
    <div key={`${card.card_type}-${card.fields.title}`} className={`p-4 rounded-lg border ${getCardStyle(card.style)} mb-4`}>
      <div className="flex items-start">
        <span className="text-2xl mr-3">{card.icon}</span>
        <div className="flex-1">
          {card.fields.title && (
            <h5 className="font-semibold text-gray-800 mb-1">{card.fields.title}</h5>
          )}
          {card.fields.subtitle && (
            <p className="text-sm text-gray-600 mb-2">{card.fields.subtitle}</p>
          )}
          {card.fields.content && (
            <p className="text-gray-700 whitespace-pre-line">{card.fields.content}</p>
          )}
          {card.fields.action && (
            <p className="mt-2 text-sm font-medium text-blue-600">
              Action: {card.fields.action}
            </p>
          )}
        </div>
      </div>
    </div>
  );

  // Render metrics
  const renderMetric = (metric: MetricElement) => (
    <div key={metric.name} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
      <h5 className="text-sm font-medium text-gray-700 mb-2">{metric.display_name}</h5>
      <div className="flex items-baseline justify-between">
        <div className="flex items-baseline">
          <span className="text-2xl font-bold text-gray-900">
            {metric.value ?? 'N/A'}
          </span>
          {metric.unit && (
            <span className="ml-1 text-sm text-gray-600">{metric.unit}</span>
          )}
        </div>
        {metric.trend_icon && (
          <span className={`text-lg ${getMetricTrendColor(metric.trend_color)}`}>
            {metric.trend_icon}
          </span>
        )}
      </div>
      {metric.percentage_to_target !== undefined && (
        <div className="mt-2">
          <div className="text-xs text-gray-600 mb-1">Progress to target</div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full"
              style={{ width: `${Math.min(100, metric.percentage_to_target)}%` }}
            />
          </div>
          <div className="text-xs text-gray-600 mt-1">{metric.percentage_to_target}%</div>
        </div>
      )}
    </div>
  );

  // Render timelines
  const renderTimeline = (timeline: TimelineElement) => (
    <div key={timeline.name} className="mb-6">
      <h4 className="text-lg font-semibold mb-3 text-gray-800">{timeline.display_name}</h4>
      <div className="space-y-3">
        {timeline.entries.map((entry, idx) => (
          <div key={idx} className="flex items-start">
            <div className="flex-shrink-0 w-24 text-sm text-gray-500">
              {entry.date}
            </div>
            <div className="flex-shrink-0 w-4 h-4 bg-blue-500 rounded-full mt-0.5 mx-3" />
            <div className="flex-1">
              <p className="text-gray-700">{entry.event}</p>
              <span className={`inline-block mt-1 text-xs px-2 py-1 rounded-full ${getStatusStyle(entry.status)}`}>
                {entry.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  // Helper functions
  const formatCellValue = (value: any): string => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'boolean') return value ? '✓' : '✗';
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  };

  const getCardStyle = (style: string): string => {
    const styles: Record<string, string> = {
      contact: 'bg-blue-50 border-blue-200',
      social: 'bg-purple-50 border-purple-200',
      action: 'bg-green-50 border-green-200',
      default: 'bg-gray-50 border-gray-200'
    };
    return styles[style] || styles.default;
  };

  const getMetricTrendColor = (color?: string): string => {
    const colors: Record<string, string> = {
      green: 'text-green-600',
      red: 'text-red-600',
      gray: 'text-gray-600'
    };
    return colors[color || 'gray'];
  };

  const getStatusStyle = (status: string): string => {
    const styles: Record<string, string> = {
      completed: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      in_progress: 'bg-blue-100 text-blue-800'
    };
    return styles[status] || 'bg-gray-100 text-gray-800';
  };

  // Main render
  return (
    <div className="space-y-8">
      {/* Tables Section */}
      {elements.tables && elements.tables.length > 0 && (
        <div>
          <h3 className="text-xl font-semibold mb-4 text-gray-800 flex items-center">
            <svg className="w-5 h-5 mr-2" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
              <path d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
            </svg>
            Tables & Data
          </h3>
          {elements.tables.map(renderTable)}
        </div>
      )}

      {/* Cards Section */}
      {elements.cards && elements.cards.length > 0 && (
        <div>
          <h3 className="text-xl font-semibold mb-4 text-gray-800 flex items-center">
            <svg className="w-5 h-5 mr-2" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
              <path d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
            </svg>
            Key Items
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {elements.cards.map(renderCard)}
          </div>
        </div>
      )}

      {/* Metrics Section */}
      {elements.metrics && elements.metrics.length > 0 && (
        <div>
          <h3 className="text-xl font-semibold mb-4 text-gray-800 flex items-center">
            <svg className="w-5 h-5 mr-2" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
              <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
            </svg>
            Metrics
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {elements.metrics.map(renderMetric)}
          </div>
        </div>
      )}

      {/* Timelines Section */}
      {elements.timelines && elements.timelines.length > 0 && (
        <div>
          <h3 className="text-xl font-semibold mb-4 text-gray-800 flex items-center">
            <svg className="w-5 h-5 mr-2" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
              <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            Timelines
          </h3>
          {elements.timelines.map(renderTimeline)}
        </div>
      )}

      {/* Raw Data Fallback */}
      {(!elements.tables?.length && !elements.cards?.length && !elements.metrics?.length && !elements.timelines?.length) && rawData && (
        <div>
          <h3 className="text-xl font-semibold mb-4 text-gray-800">Structured Data</h3>
          <pre className="bg-gray-50 p-4 rounded-lg overflow-auto text-sm">
            {JSON.stringify(rawData, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}