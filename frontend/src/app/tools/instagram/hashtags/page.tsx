'use client';

import React, { useState } from 'react';
import { api } from '@/utils/api';
import { HashtagAnalysis } from '@/types';

export default function HashtagAnalysisPage() {
  const [hashtags, setHashtags] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<HashtagAnalysis | null>(null);
  
  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      setError(null);
      
      // Clean and validate hashtags
      const hashtagsList = hashtags
        .split(',')
        .map(tag => tag.trim().replace(/^#/, ''))
        .filter(tag => tag.length > 0);
      
      if (hashtagsList.length === 0) {
        throw new Error('Inserisci almeno un hashtag');
      }
      
      const result = await api.tools.analyzeHashtags(hashtagsList);
      setAnalysis(result);
    } catch (err) {
      console.error('Failed to analyze hashtags:', err);
      setError(err instanceof Error ? err.message : 'Si è verificato un errore durante l\'analisi degli hashtag');
    } finally {
      setLoading(false);
    }
  };
  
  const getTrendingBadge = (trending: boolean) => {
    return trending ? (
      <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
        Trending
      </span>
    ) : (
      <span className="bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded-full">
        Stabile
      </span>
    );
  };
  
  return (
    <div className="container mx-auto max-w-4xl">
      <h1 className="text-2xl font-semibold mb-2">Analisi Hashtag</h1>
      <p className="text-gray-600 mb-6">
        Analizza hashtag di Instagram per determinare popolarità, trend e hashtag correlati.
      </p>
      
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <form onSubmit={handleAnalyze}>
          <div className="mb-4">
            <label htmlFor="hashtags" className="block text-sm font-medium text-gray-700 mb-1">
              Hashtag da analizzare
            </label>
            <input
              type="text"
              id="hashtags"
              value={hashtags}
              onChange={(e) => setHashtags(e.target.value)}
              placeholder="travel, photography, italy (separati da virgole)"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              Inserisci gli hashtag che desideri analizzare, separati da virgole
            </p>
          </div>
          
          <div className="flex justify-end">
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition flex items-center"
              disabled={loading}
            >
              {loading ? (
                <>
                  <div className="h-4 w-4 border-2 border-white border-r-transparent rounded-full animate-spin mr-2"></div>
                  Analisi...
                </>
              ) : (
                'Analizza'
              )}
            </button>
          </div>
        </form>
      </div>
      
      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-md mb-6">
          {error}
        </div>
      )}
      
      {analysis && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-medium mb-4">Risultati Analisi</h2>
          
          {analysis.analysis && (
            <div className="bg-indigo-50 p-4 rounded-md mb-6">
              <h3 className="font-medium text-indigo-800 mb-2">Raccomandazione</h3>
              <p className="text-indigo-700">{analysis.analysis.recommendation}</p>
              
              {analysis.analysis.trending_hashtags.length > 0 && (
                <div className="mt-2">
                  <p className="text-sm text-indigo-700 mb-1">Hashtag in tendenza:</p>
                  <div className="flex flex-wrap gap-2">
                    {analysis.analysis.trending_hashtags.map((tag) => (
                      <span key={tag} className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          
          <div className="space-y-6">
            {Object.entries(analysis)
              .filter(([key]) => key !== 'analysis')
              .map(([hashtag, data]) => (
                <div key={hashtag} className="border border-gray-200 rounded-md p-4">
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="font-medium text-lg">#{hashtag}</h3>
                    {getTrendingBadge(data.trending)}
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="bg-gray-50 p-3 rounded-md">
                      <p className="text-sm text-gray-500">Post totali</p>
                      <p className="font-medium">{data.posts_count.toLocaleString()}</p>
                    </div>
                    
                    <div className="bg-gray-50 p-3 rounded-md">
                      <p className="text-sm text-gray-500">Popolarità</p>
                      <p className="font-medium">{data.popularity_score}/10</p>
                    </div>
                    
                    <div className="bg-gray-50 p-3 rounded-md">
                      <p className="text-sm text-gray-500">Tasso di engagement</p>
                      <p className="font-medium">{data.engagement_rate}</p>
                    </div>
                    
                    <div className="bg-gray-50 p-3 rounded-md">
                      <p className="text-sm text-gray-500">Tasso di crescita</p>
                      <p className={`font-medium ${
                        parseFloat(data.growth_rate) > 0 ? 'text-green-600' : 
                        parseFloat(data.growth_rate) < 0 ? 'text-red-600' : ''
                      }`}>
                        {data.growth_rate}
                      </p>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-gray-500 mb-1">Hashtag correlati</p>
                      <div className="flex flex-wrap gap-2">
                        {data.related_tags.map((tag) => (
                          <span key={tag} className="bg-indigo-50 text-indigo-700 text-xs px-2 py-1 rounded-full">
                            #{tag}
                          </span>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <p className="text-sm text-gray-500 mb-1">Orari di pubblicazione consigliati</p>
                      <div className="flex flex-wrap gap-2">
                        {data.best_posting_times.map((time) => (
                          <span key={time} className="bg-blue-50 text-blue-700 text-xs px-2 py-1 rounded-full">
                            {time}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}