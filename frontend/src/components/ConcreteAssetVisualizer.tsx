// frontend/src/components/ConcreteAssetVisualizer.tsx - WOW EFFECT VISUAL ASSET VIEWER
'use client';

import React, { useState, useEffect } from 'react';
import type { ActionableAsset } from '@/types';

interface ConcreteAssetVisualizerProps {
  asset: ActionableAsset;
  onClose: () => void;
  onExport?: (format: string) => void;
  onEnhance?: () => void;
}

const ConcreteAssetVisualizer: React.FC<ConcreteAssetVisualizerProps> = ({
  asset,
  onClose,
  onExport,
  onEnhance
}) => {
  const [activeTab, setActiveTab] = useState<'preview' | 'interactive' | 'export'>('preview');
  const [animationClass, setAnimationClass] = useState('');

  useEffect(() => {
    setAnimationClass('animate-slide-in');
  }, []);

  // Render different asset types with WOW visual effects
  const renderAssetPreview = () => {
    const assetType = asset.asset_name.toLowerCase();
    const data = asset.asset_data;

    // Instagram Content Calendar
    if (assetType.includes('calendar') || assetType.includes('content')) {
      return <ContentCalendarVisualizer data={data} />;
    }

    // Contact Database
    if (assetType.includes('contact') || assetType.includes('database')) {
      return <ContactDatabaseVisualizer data={data} />;
    }

    // Email Templates
    if (assetType.includes('email') || assetType.includes('template')) {
      return <EmailTemplateVisualizer data={data} />;
    }

    // Training Program
    if (assetType.includes('training') || assetType.includes('workout')) {
      return <TrainingProgramVisualizer data={data} />;
    }

    // Financial Model
    if (assetType.includes('financial') || assetType.includes('budget')) {
      return <FinancialModelVisualizer data={data} />;
    }

    // Generic fallback
    return <GenericAssetVisualizer data={data} />;
  };

  const getQualityBadge = () => {
    const score = asset.quality_score || 0.85;
    if (score >= 0.9) return { text: 'Premium', color: 'bg-purple-500' };
    if (score >= 0.8) return { text: 'High Quality', color: 'bg-green-500' };
    if (score >= 0.7) return { text: 'Good', color: 'bg-blue-500' };
    return { text: 'Draft', color: 'bg-gray-500' };
  };

  const qualityBadge = getQualityBadge();

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className={`bg-white rounded-3xl shadow-2xl max-w-7xl w-full max-h-[95vh] overflow-hidden ${animationClass}`}>
        
        {/* Premium Header */}
        <div className="bg-gradient-to-r from-purple-600 via-blue-600 to-emerald-600 p-8 text-white relative overflow-hidden">
          <div className="absolute inset-0 bg-black/20"></div>
          <div className="relative z-10 flex items-center justify-between">
            <div>
              <div className="flex items-center space-x-4 mb-3">
                <div className="text-5xl animate-bounce">{getAssetIcon(asset.asset_name)}</div>
                <div>
                  <h1 className="text-3xl font-bold mb-1">
                    {asset.asset_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </h1>
                  <p className="text-lg opacity-90">Ready for immediate business deployment</p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <span className={`${qualityBadge.color} px-4 py-2 rounded-full text-sm font-bold animate-pulse`}>
                  ✨ {qualityBadge.text}
                </span>
                <span className="bg-white/20 px-4 py-2 rounded-full text-sm">
                  💎 Business Value: €{Math.round((asset.business_value || 5000)).toLocaleString()}
                </span>
              </div>
            </div>
            <button 
              onClick={onClose}
              className="text-white hover:bg-white/20 rounded-full p-3 transition-all duration-300 hover:rotate-90"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Interactive Tabs */}
        <div className="bg-gray-50 border-b border-gray-200">
          <div className="flex">
            {[
              { key: 'preview', icon: '👁️', label: 'Visual Preview', desc: 'See your asset in action' },
              { key: 'interactive', icon: '🎯', label: 'Interactive Mode', desc: 'Edit and customize' },
              { key: 'export', icon: '📦', label: 'Export Options', desc: 'Download in any format' }
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as any)}
                className={`flex-1 px-6 py-5 text-center border-b-3 transition-all duration-300 ${
                  activeTab === tab.key
                    ? 'border-purple-500 text-purple-600 bg-white shadow-md transform -translate-y-0.5'
                    : 'border-transparent text-gray-600 hover:text-gray-800'
                }`}
              >
                <div className="text-2xl mb-1">{tab.icon}</div>
                <div className="font-semibold">{tab.label}</div>
                <div className="text-xs text-gray-500">{tab.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Content Area */}
        <div className="p-8 overflow-y-auto max-h-[60vh] bg-gray-50">
          {activeTab === 'preview' && (
            <div className="animate-fade-in">
              {renderAssetPreview()}
            </div>
          )}

          {activeTab === 'interactive' && (
            <InteractiveEditor asset={asset} onSave={onEnhance} />
          )}

          {activeTab === 'export' && (
            <ExportOptions asset={asset} onExport={onExport} />
          )}
        </div>

        {/* Action Footer */}
        <div className="bg-white border-t border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6 text-sm text-gray-600">
              <span className="flex items-center">
                <span className="text-green-500 mr-2">✅</span>
                {Math.round((asset.actionability_score || 0.9) * 100)}% Ready to Use
              </span>
              <span className="flex items-center">
                <span className="text-blue-500 mr-2">📊</span>
                {Object.keys(asset.asset_data || {}).length} Data Points
              </span>
              <span className="flex items-center">
                <span className="text-purple-500 mr-2">⚡</span>
                AI-Enhanced Asset
              </span>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => onExport?.('json')}
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-semibold hover:shadow-lg transform hover:-translate-y-0.5 transition-all duration-300"
              >
                Export Asset
              </button>
              <button
                onClick={onEnhance}
                className="px-6 py-3 bg-gradient-to-r from-orange-500 to-pink-500 text-white rounded-xl font-semibold hover:shadow-lg transform hover:-translate-y-0.5 transition-all duration-300"
              >
                AI Enhance
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Specialized Visualizers for different asset types

const ContentCalendarVisualizer: React.FC<{ data: any }> = ({ data }) => {
  const posts = Array.isArray(data) ? data : (data.posts || []);
  
  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-pink-100 to-purple-100 rounded-2xl p-6 border border-purple-200">
        <h3 className="text-2xl font-bold text-purple-800 mb-4 flex items-center">
          <span className="mr-3">📅</span>
          Instagram Content Calendar
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {posts.slice(0, 6).map((post: any, index: number) => (
            <div key={index} className="bg-white rounded-xl p-4 shadow-md hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold text-purple-600">Post {index + 1}</span>
                <span className="text-xs text-gray-500">{post.date || `Day ${index + 1}`}</span>
              </div>
              <div className="aspect-square bg-gradient-to-br from-pink-400 to-purple-400 rounded-lg mb-3 flex items-center justify-center text-white text-4xl">
                {getPostEmoji(post.content || post.caption || '')}
              </div>
              <p className="text-sm text-gray-700 mb-2 line-clamp-3">
                {post.caption || post.content || 'Content preview...'}
              </p>
              {post.hashtags && (
                <div className="flex flex-wrap gap-1">
                  {(typeof post.hashtags === 'string' ? post.hashtags.split(' ') : post.hashtags)
                    .slice(0, 3)
                    .map((tag: string, i: number) => (
                      <span key={i} className="text-xs bg-purple-100 text-purple-600 px-2 py-1 rounded-full">
                        {tag.startsWith('#') ? tag : `#${tag}`}
                      </span>
                    ))}
                </div>
              )}
            </div>
          ))}
        </div>
        {posts.length > 6 && (
          <div className="mt-4 text-center text-purple-600 font-medium">
            + {posts.length - 6} more posts in calendar
          </div>
        )}
      </div>
    </div>
  );
};

const ContactDatabaseVisualizer: React.FC<{ data: any }> = ({ data }) => {
  const contacts = Array.isArray(data) ? data : (data.contacts || []);
  
  return (
    <div className="bg-gradient-to-r from-blue-100 to-cyan-100 rounded-2xl p-6 border border-blue-200">
      <h3 className="text-2xl font-bold text-blue-800 mb-4 flex items-center">
        <span className="mr-3">👥</span>
        Qualified Contact Database
      </h3>
      <div className="bg-white rounded-xl shadow-md overflow-hidden">
        <table className="w-full">
          <thead className="bg-blue-500 text-white">
            <tr>
              <th className="px-6 py-3 text-left">Name</th>
              <th className="px-6 py-3 text-left">Company</th>
              <th className="px-6 py-3 text-left">Email</th>
              <th className="px-6 py-3 text-left">Score</th>
            </tr>
          </thead>
          <tbody>
            {contacts.slice(0, 10).map((contact: any, index: number) => (
              <tr key={index} className="border-b hover:bg-blue-50 transition-colors">
                <td className="px-6 py-4 font-medium">{contact.name || `Contact ${index + 1}`}</td>
                <td className="px-6 py-4">{contact.company || 'Company'}</td>
                <td className="px-6 py-4 text-blue-600">{contact.email || 'email@example.com'}</td>
                <td className="px-6 py-4">
                  <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm font-medium">
                    {contact.score || '85%'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {contacts.length > 10 && (
          <div className="p-4 text-center bg-blue-50 text-blue-600 font-medium">
            + {contacts.length - 10} more qualified contacts
          </div>
        )}
      </div>
    </div>
  );
};

const EmailTemplateVisualizer: React.FC<{ data: any }> = ({ data }) => {
  const templates = Array.isArray(data) ? data : [data];
  const [selectedTemplate, setSelectedTemplate] = useState(0);
  const template = templates[selectedTemplate] || {};
  
  return (
    <div className="space-y-6">
      {templates.length > 1 && (
        <div className="flex space-x-2 overflow-x-auto pb-2">
          {templates.map((_, index) => (
            <button
              key={index}
              onClick={() => setSelectedTemplate(index)}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                selectedTemplate === index
                  ? 'bg-orange-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Template {index + 1}
            </button>
          ))}
        </div>
      )}
      <div className="bg-gradient-to-r from-orange-100 to-red-100 rounded-2xl p-6 border border-orange-200">
        <h3 className="text-2xl font-bold text-orange-800 mb-4 flex items-center">
          <span className="mr-3">📧</span>
          Email Template Preview
        </h3>
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="border-b pb-4 mb-4">
            <div className="text-sm text-gray-600 mb-1">Subject Line:</div>
            <div className="text-xl font-bold text-gray-800">
              {template.subject || 'Professional Email Template'}
            </div>
          </div>
          <div className="prose max-w-none">
            <div className="whitespace-pre-wrap text-gray-700">
              {template.body || template.content || 'Email content preview...'}
            </div>
          </div>
          {template.call_to_action && (
            <div className="mt-6">
              <button className="bg-orange-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-orange-600 transition">
                {template.call_to_action}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const TrainingProgramVisualizer: React.FC<{ data: any }> = ({ data }) => {
  const exercises = Array.isArray(data) ? data : (data.exercises || data.workouts || []);
  
  return (
    <div className="bg-gradient-to-r from-green-100 to-emerald-100 rounded-2xl p-6 border border-green-200">
      <h3 className="text-2xl font-bold text-green-800 mb-4 flex items-center">
        <span className="mr-3">💪</span>
        Training Program
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {exercises.slice(0, 8).map((exercise: any, index: number) => (
          <div key={index} className="bg-white rounded-xl p-4 shadow-md hover:shadow-lg transition-all">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-bold text-green-700">
                {exercise.name || exercise.exercise || `Exercise ${index + 1}`}
              </h4>
              <span className="text-2xl">{getExerciseEmoji(exercise.name || '')}</span>
            </div>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Sets:</span>
                <span className="font-semibold">{exercise.sets || '3'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Reps:</span>
                <span className="font-semibold">{exercise.reps || '10-12'}</span>
              </div>
              {exercise.weight && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Weight:</span>
                  <span className="font-semibold">{exercise.weight}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const FinancialModelVisualizer: React.FC<{ data: any }> = ({ data }) => {
  const categories = Array.isArray(data) ? data : (data.categories || data.budget_items || []);
  const total = categories.reduce((sum: number, cat: any) => sum + (cat.amount || 0), 0);
  
  return (
    <div className="bg-gradient-to-r from-indigo-100 to-purple-100 rounded-2xl p-6 border border-indigo-200">
      <h3 className="text-2xl font-bold text-indigo-800 mb-4 flex items-center">
        <span className="mr-3">💰</span>
        Financial Model
      </h3>
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="space-y-3">
          {categories.slice(0, 10).map((cat: any, index: number) => (
            <div key={index} className="flex items-center justify-between p-3 hover:bg-indigo-50 rounded-lg transition">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-indigo-500 rounded-full flex items-center justify-center text-white font-bold">
                  {(cat.category || cat.name || `Item ${index + 1}`).charAt(0).toUpperCase()}
                </div>
                <span className="font-medium">{cat.category || cat.name || `Budget Item ${index + 1}`}</span>
              </div>
              <span className="text-xl font-bold text-indigo-600">
                €{(cat.amount || 0).toLocaleString()}
              </span>
            </div>
          ))}
        </div>
        <div className="mt-6 pt-6 border-t border-gray-200 flex items-center justify-between">
          <span className="text-lg font-semibold text-gray-700">Total Budget</span>
          <span className="text-2xl font-bold text-indigo-600">€{total.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
};

const GenericAssetVisualizer: React.FC<{ data: any }> = ({ data }) => {
  const entries = Object.entries(data || {});
  
  return (
    <div className="bg-gradient-to-r from-gray-100 to-slate-100 rounded-2xl p-6 border border-gray-300">
      <h3 className="text-2xl font-bold text-gray-800 mb-4">Asset Preview</h3>
      <div className="space-y-4">
        {entries.map(([key, value]) => (
          <div key={key} className="bg-white rounded-lg p-4 shadow">
            <div className="font-semibold text-gray-700 mb-2">
              {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </div>
            <div className="text-gray-600">
              {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Interactive Editor Component
const InteractiveEditor: React.FC<{ asset: ActionableAsset; onSave?: () => void }> = ({ asset, onSave }) => {
  return (
    <div className="bg-yellow-50 rounded-2xl p-6 border border-yellow-300">
      <h3 className="text-xl font-bold text-yellow-800 mb-4 flex items-center">
        <span className="mr-3">✏️</span>
        Interactive Asset Editor (Coming Soon)
      </h3>
      <p className="text-yellow-700">
        Direct editing capabilities will be available in the next update. 
        For now, use the AI Enhancement feature to request specific changes.
      </p>
      <button
        onClick={onSave}
        className="mt-4 bg-yellow-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-yellow-600 transition"
      >
        Request AI Enhancement
      </button>
    </div>
  );
};

// Export Options Component
const ExportOptions: React.FC<{ asset: ActionableAsset; onExport?: (format: string) => void }> = ({ asset, onExport }) => {
  const formats = [
    { id: 'json', name: 'JSON', icon: '📄', desc: 'Raw data format' },
    { id: 'csv', name: 'CSV', icon: '📊', desc: 'Excel compatible' },
    { id: 'pdf', name: 'PDF', icon: '📑', desc: 'Professional document' },
    { id: 'html', name: 'HTML', icon: '🌐', desc: 'Web ready' },
  ];

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-gray-800 mb-4">Choose Export Format</h3>
      <div className="grid grid-cols-2 gap-4">
        {formats.map((format) => (
          <button
            key={format.id}
            onClick={() => onExport?.(format.id)}
            className="bg-white rounded-xl p-6 shadow-md hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 border-2 border-transparent hover:border-purple-500"
          >
            <div className="text-4xl mb-3">{format.icon}</div>
            <div className="font-semibold text-gray-800">{format.name}</div>
            <div className="text-sm text-gray-600">{format.desc}</div>
          </button>
        ))}
      </div>
    </div>
  );
};

// Helper functions
const getAssetIcon = (assetName: string): string => {
  const name = assetName.toLowerCase();
  if (name.includes('calendar') || name.includes('content')) return '📅';
  if (name.includes('contact') || name.includes('database')) return '👥';
  if (name.includes('email') || name.includes('template')) return '📧';
  if (name.includes('training') || name.includes('workout')) return '💪';
  if (name.includes('financial') || name.includes('budget')) return '💰';
  return '📋';
};

const getPostEmoji = (content: string): string => {
  const lower = content.toLowerCase();
  if (lower.includes('motivat')) return '🔥';
  if (lower.includes('tips') || lower.includes('advice')) return '💡';
  if (lower.includes('workout') || lower.includes('exercise')) return '💪';
  if (lower.includes('nutrition') || lower.includes('food')) return '🥗';
  if (lower.includes('transform')) return '✨';
  return '📸';
};

const getExerciseEmoji = (name: string): string => {
  const lower = name.toLowerCase();
  if (lower.includes('squat')) return '🏋️';
  if (lower.includes('bench') || lower.includes('press')) return '💪';
  if (lower.includes('deadlift')) return '🏋️‍♂️';
  if (lower.includes('curl')) return '💪';
  if (lower.includes('cardio') || lower.includes('run')) return '🏃';
  return '🏋️';
};

// Animation styles
const styles = `
@keyframes slide-in {
  from {
    transform: translateY(100px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.animate-slide-in {
  animation: slide-in 0.5s ease-out;
}

.animate-fade-in {
  animation: fade-in 0.3s ease-out;
}

.line-clamp-3 {
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}
`;

export default ConcreteAssetVisualizer;