'use client';

import React from 'react';

interface GenericArrayViewerProps {
  items: any[];
  fieldName: string;
  additionalData?: Record<string, any>;
  assetName: string;
}

// Smart asset type detection based on content patterns
const detectAssetType = (fieldName: string, items: any[], assetName: string) => {
  const nameLower = assetName.toLowerCase();
  const fieldLower = fieldName.toLowerCase();
  
  // Check for calendar/scheduling content
  if (nameLower.includes('calendar') || fieldLower.includes('calendar') || 
      nameLower.includes('schedule') || fieldLower.includes('posts')) {
    return {
      type: 'calendar',
      icon: '📅',
      color: 'blue',
      title: 'Content Calendar',
      itemLabel: 'posts'
    };
  }
  
  // Check for contacts/people
  if (nameLower.includes('contact') || fieldLower.includes('people') ||
      nameLower.includes('directory') || fieldLower.includes('team')) {
    return {
      type: 'contacts',
      icon: '👤', 
      color: 'green',
      title: 'Directory',
      itemLabel: 'contacts'
    };
  }
  
  // Check for products/inventory
  if (nameLower.includes('product') || fieldLower.includes('inventory') ||
      nameLower.includes('catalog') || fieldLower.includes('items')) {
    return {
      type: 'products',
      icon: '📦',
      color: 'purple',
      title: 'Product Catalog',
      itemLabel: 'products'
    };
  }
  
  // Check for tasks/workflows
  if (nameLower.includes('task') || fieldLower.includes('workflow') ||
      nameLower.includes('checklist') || fieldLower.includes('steps')) {
    return {
      type: 'tasks',
      icon: '✅',
      color: 'orange',
      title: 'Task List',
      itemLabel: 'tasks'
    };
  }
  
  // Default fallback
  return {
    type: 'generic',
    icon: '📋',
    color: 'gray',
    title: 'Data Collection',
    itemLabel: 'items'
  };
};

// Smart field detection for display
const getDisplayFields = (items: any[]) => {
  if (!items.length) return [];
  
  const firstItem = items[0];
  const fields = Object.keys(firstItem);
  
  // Priority fields to show first
  const priorityFields = ['title', 'name', 'date', 'caption', 'content', 'description', 'type'];
  const secondaryFields = ['hashtags', 'tags', 'category', 'status', 'engagement'];
  
  const sortedFields = [
    ...priorityFields.filter(f => fields.includes(f)),
    ...fields.filter(f => !priorityFields.includes(f) && !secondaryFields.includes(f)),
    ...secondaryFields.filter(f => fields.includes(f))
  ];
  
  return sortedFields.slice(0, 5); // Show max 5 fields
};

// Smart value formatting
const formatValue = (value: any, key: string): string => {
  if (value === null || value === undefined) return 'N/A';
  
  if (Array.isArray(value)) {
    if (key.toLowerCase().includes('hashtag')) {
      return value.join(' ');
    }
    return value.slice(0, 3).join(', ') + (value.length > 3 ? `... (+${value.length - 3} more)` : '');
  }
  
  if (typeof value === 'string') {
    if (value.length > 150) {
      return value.substring(0, 150) + '...';
    }
    return value;
  }
  
  if (typeof value === 'object') {
    return JSON.stringify(value).substring(0, 100) + '...';
  }
  
  return String(value);
};

const GenericArrayViewer: React.FC<GenericArrayViewerProps> = ({ 
  items, 
  fieldName, 
  additionalData, 
  assetName 
}) => {
  const assetType = detectAssetType(fieldName, items, assetName);
  const displayFields = getDisplayFields(items);
  
  console.log('🔍 GenericArrayViewer detected type:', assetType.type, 'for', items.length, 'items');
  
  // Color scheme mapping
  const colorSchemes = {
    blue: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      header: 'text-blue-800',
      text: 'text-blue-700',
      accent: 'text-blue-600'
    },
    green: {
      bg: 'bg-green-50',
      border: 'border-green-200', 
      header: 'text-green-800',
      text: 'text-green-700',
      accent: 'text-green-600'
    },
    purple: {
      bg: 'bg-purple-50',
      border: 'border-purple-200',
      header: 'text-purple-800', 
      text: 'text-purple-700',
      accent: 'text-purple-600'
    },
    orange: {
      bg: 'bg-orange-50',
      border: 'border-orange-200',
      header: 'text-orange-800',
      text: 'text-orange-700', 
      accent: 'text-orange-600'
    },
    gray: {
      bg: 'bg-gray-50',
      border: 'border-gray-200',
      header: 'text-gray-800',
      text: 'text-gray-700',
      accent: 'text-gray-600'
    }
  };
  
  const colors = colorSchemes[assetType.color as keyof typeof colorSchemes] || colorSchemes.gray;

  return (
    <div className="p-4">
      <div className={`${colors.bg} ${colors.border} border rounded-lg p-4 mb-6`}>
        <h2 className={`text-xl font-bold ${colors.header} mb-2`}>
          {assetType.icon} {assetType.title}
        </h2>
        <p className={colors.text}>Found {items.length} {assetType.itemLabel} in the collection</p>
        {additionalData?.executive_summary && (
          <p className={`text-sm ${colors.accent} mt-2`}>{additionalData.executive_summary}</p>
        )}
      </div>

      <div className="space-y-4">
        {items.map((item, index) => {
          console.log(`🔍 Rendering item ${index + 1}:`, Object.keys(item));

          return (
            <div key={index} className="bg-white border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-gray-900">
                  {assetType.icon} #{index + 1}
                  {item.type && ` - ${item.type}`}
                  {item.title && ` - ${item.title}`}
                  {item.name && ` - ${item.name}`}
                </h3>
                {(item.date || item.created_at || item.timestamp) && (
                  <span className="text-sm text-gray-500">
                    {item.date || item.created_at || item.timestamp}
                  </span>
                )}
              </div>
              
              {displayFields.map(field => {
                const value = item[field];
                if (!value) return null;
                
                return (
                  <div key={field} className="mb-2">
                    <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                      {field.replace(/_/g, ' ')}
                    </div>
                    <div className="text-sm text-gray-700 bg-gray-50 p-2 rounded">
                      {formatValue(value, field)}
                    </div>
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>

      {/* Smart summary based on content type */}
      <div className="mt-6 bg-gray-50 border rounded-lg p-4">
        <h3 className="font-medium text-gray-800 mb-2">📊 Summary</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>Total {assetType.itemLabel}: <strong>{items.length}</strong></div>
          
          {/* Dynamic summary based on detected patterns */}
          {assetType.type === 'calendar' && (
            <>
              <div>Reels: <strong>{items.filter(p => p.type === 'Reel').length}</strong></div>
              <div>Carousels: <strong>{items.filter(p => p.type === 'Carousel').length}</strong></div>
              <div>Videos: <strong>{items.filter(p => p.type === 'Video').length}</strong></div>
            </>
          )}
          
          {assetType.type === 'contacts' && (
            <>
              <div>Active: <strong>{items.filter(p => p.status === 'active' || !p.status).length}</strong></div>
              <div>With Email: <strong>{items.filter(p => p.email).length}</strong></div>
            </>
          )}
          
          {assetType.type === 'products' && (
            <>
              <div>In Stock: <strong>{items.filter(p => p.status === 'in_stock' || !p.status).length}</strong></div>
              <div>Categories: <strong>{new Set(items.map(p => p.category).filter(Boolean)).size}</strong></div>
            </>
          )}
          
          {assetType.type === 'tasks' && (
            <>
              <div>Completed: <strong>{items.filter(p => p.status === 'completed').length}</strong></div>
              <div>Pending: <strong>{items.filter(p => p.status === 'pending' || !p.status).length}</strong></div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default GenericArrayViewer;