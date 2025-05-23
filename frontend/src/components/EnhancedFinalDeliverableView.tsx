// frontend/src/components/EnhancedFinalDeliverableView.tsx
import React, { useState } from 'react';

interface EnhancedFinalDeliverableViewProps {
  result: any; // Il risultato che contiene i dati del deliverable finale
}

export default function EnhancedFinalDeliverableView({ result }: EnhancedFinalDeliverableViewProps) {
  const [activeSection, setActiveSection] = useState('overview');
  
  // Estrai dati aggiuntivi dai campi extra del deliverable finale
  const keyInsights = result.content?.keyInsights || [];
  const metrics = result.content?.metrics || {};
  const recommendations = result.content?.recommendations || [];
  const nextSteps = result.content?.nextSteps || [];
  
  const renderMetrics = () => {
    if (!metrics || Object.keys(metrics).length === 0) return null;
    
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(metrics).map(([key, values]) => (
          <div key={key} className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <h4 className="text-sm font-medium text-gray-700 capitalize mb-2">
              {key.replace(/_/g, ' ')}
            </h4>
            {Array.isArray(values) ? (
              <div className="space-y-1">
                {values.map((value, idx) => (
                  <div key={idx} className="text-lg font-semibold text-indigo-600">
                    {value}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-lg font-semibold text-indigo-600">{values}</div>
            )}
          </div>
        ))}
      </div>
    );
  };
  
  return (
    <div className="space-y-6">
      {/* Navigation tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: '📋 Panoramica', icon: '📋' },
            { id: 'insights', label: '💡 Insights Chiave', icon: '💡' },
            { id: 'metrics', label: '📊 Metriche', icon: '📊' },
            { id: 'actions', label: '🎯 Prossimi Passi', icon: '🎯' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveSection(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeSection === tab.id
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>
      
      {/* Content based on active section */}
      {activeSection === 'overview' && (
        <div className="space-y-6">
          {/* Executive Summary */}
          <div className="bg-gradient-to-br from-indigo-50 to-blue-50 p-6 rounded-lg border border-indigo-100">
            <h3 className="font-semibold text-indigo-800 text-lg mb-4 flex items-center">
              <span className="text-2xl mr-2">🎯</span>
              Executive Summary
            </h3>
            <div className="prose max-w-none">
              <p className="text-indigo-900 leading-relaxed">
                {result.content?.summary || result.description}
              </p>
            </div>
          </div>
          
          {/* Quick Stats Overview */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-green-50 p-4 rounded-lg border border-green-200 text-center">
              <div className="text-2xl font-bold text-green-700">{keyInsights.length}</div>
              <div className="text-sm text-green-600">Key Insights</div>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200 text-center">
              <div className="text-2xl font-bold text-blue-700">{Object.keys(metrics).length}</div>
              <div className="text-sm text-blue-600">Metriche</div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg border border-purple-200 text-center">
              <div className="text-2xl font-bold text-purple-700">{recommendations.length}</div>
              <div className="text-sm text-purple-600">Raccomandazioni</div>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg border border-orange-200 text-center">
              <div className="text-2xl font-bold text-orange-700">{nextSteps.length}</div>
              <div className="text-sm text-orange-600">Prossimi Passi</div>
            </div>
          </div>
          
          {/* Detailed Content */}
          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <h4 className="font-medium text-gray-900 mb-3">Contenuto Completo</h4>
            <div className="prose max-w-none text-gray-700">
              <pre className="whitespace-pre-wrap font-sans">{result.content?.details || result.content?.summary}</pre>
            </div>
          </div>
        </div>
      )}
      
      {activeSection === 'insights' && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">💡 Insights Chiave</h3>
          
          {keyInsights.length > 0 ? (
            <div className="grid grid-cols-1 gap-4">
              {keyInsights.map((insight, index) => (
                <div key={index} className="bg-gradient-to-r from-purple-50 to-pink-50 p-5 rounded-lg border border-purple-100 shadow-sm">
                  <div className="flex items-start">
                    <div className="bg-purple-200 text-purple-800 h-8 w-8 rounded-full flex items-center justify-center text-sm font-bold mr-4 flex-shrink-0">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <p className="text-purple-900 font-medium leading-relaxed">{insight}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 bg-gray-50 rounded-lg">
              <div className="text-4xl mb-2">💡</div>
              <p className="text-gray-600">Nessun insight specifico identificato</p>
            </div>
          )}
        </div>
      )}
      
      {activeSection === 'metrics' && (
        <div className="space-y-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 Metriche del Progetto</h3>
          
          {Object.keys(metrics).length > 0 ? (
            <div className="space-y-6">
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg border border-blue-100">
                <h4 className="font-semibold text-blue-900 mb-4">Risultati Quantitativi</h4>
                {renderMetrics()}
              </div>
              
              {/* Visualizzazione aggiuntiva per percentuali */}
              {metrics.percentages && (
                <div className="bg-white p-6 rounded-lg border border-gray-200">
                  <h4 className="font-medium text-gray-900 mb-4">Performance Percentuali</h4>
                  <div className="space-y-3">
                    {metrics.percentages.map((percentage, idx) => (
                      <div key={idx} className="flex items-center">
                        <div className="w-full bg-gray-200 rounded-full h-3 mr-3">
                          <div 
                            className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                            style={{ width: percentage }}
                          ></div>
                        </div>
                        <span className="font-semibold text-blue-700 min-w-0 flex-shrink-0">
                          {percentage}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 bg-gray-50 rounded-lg">
              <div className="text-4xl mb-2">📊</div>
              <p className="text-gray-600">Nessuna metrica quantitativa disponibile</p>
            </div>
          )}
        </div>
      )}
      
      {activeSection === 'actions' && (
        <div className="space-y-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">🎯 Raccomandazioni e Prossimi Passi</h3>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Raccomandazioni */}
            {recommendations.length > 0 && (
              <div className="bg-green-50 p-6 rounded-lg border border-green-100">
                <h4 className="font-semibold text-green-800 mb-4 flex items-center">
                  <span className="text-xl mr-2">💡</span>
                  Raccomandazioni
                </h4>
                <ul className="space-y-3">
                  {recommendations.map((rec, index) => (
                    <li key={index} className="flex items-start">
                      <div className="bg-green-200 text-green-800 h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold mr-3 flex-shrink-0 mt-0.5">
                        {index + 1}
                      </div>
                      <span className="text-green-900 text-sm leading-relaxed">{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            {/* Prossimi Passi */}
            {nextSteps.length > 0 && (
              <div className="bg-blue-50 p-6 rounded-lg border border-blue-100">
                <h4 className="font-semibold text-blue-800 mb-4 flex items-center">
                  <span className="text-xl mr-2">🎯</span>
                  Prossimi Passi
                </h4>
                <ul className="space-y-3">
                  {nextSteps.map((step, index) => (
                    <li key={index} className="flex items-start">
                      <div className="bg-blue-200 text-blue-800 h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold mr-3 flex-shrink-0 mt-0.5">
                        {index + 1}
                      </div>
                      <span className="text-blue-900 text-sm leading-relaxed">{step}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          
          {(recommendations.length === 0 && nextSteps.length === 0) && (
            <div className="text-center py-8 bg-gray-50 rounded-lg">
              <div className="text-4xl mb-2">🎯</div>
              <p className="text-gray-600">Nessuna raccomandazione o prossimo passo specificato</p>
            </div>
          )}
        </div>
      )}
      
      {/* Action buttons */}
      <div className="flex justify-between pt-6 border-t border-gray-200">
        <div className="flex space-x-3">
          <button 
            onClick={() => console.log('Download deliverable', result.id)} 
            className="px-4 py-2 bg-indigo-50 text-indigo-700 rounded-md text-sm hover:bg-indigo-100 transition flex items-center"
          >
            <span className="mr-1">📄</span> Scarica Report
          </button>
          <button 
            onClick={() => console.log('Share deliverable', result.id)} 
            className="px-4 py-2 bg-gray-50 text-gray-700 rounded-md text-sm hover:bg-gray-100 transition flex items-center"
          >
            <span className="mr-1">📤</span> Condividi
          </button>
        </div>
        
        <div className="flex space-x-3">
          <button 
            onClick={() => console.log('Request changes', result.id)} 
            className="px-4 py-2 bg-yellow-600 text-white rounded-md text-sm hover:bg-yellow-700 transition flex items-center"
          >
            <span className="mr-1">✏️</span> Richiedi Modifiche
          </button>
          <button 
            onClick={() => console.log('Approve deliverable', result.id)} 
            className="px-4 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700 transition flex items-center"
          >
            <span className="mr-1">✓</span> Approva Finale
          </button>
        </div>
      </div>
    </div>
  );
}