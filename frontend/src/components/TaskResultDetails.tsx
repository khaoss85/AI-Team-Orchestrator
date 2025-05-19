// frontend/src/components/TaskResultDetails.tsx
import React from 'react';

export default function TaskResultDetails({ result }) {
  if (!result) return null;

  // Estrai i campi principali dal risultato
  const {
    summary,
    output,
    status,
    key_points = [],
    next_steps = [],
    detailed_results_json,
    execution_time_seconds,
    cost_estimated,
    tokens_used
  } = result;

  // Evita duplicazioni: mostra output o summary, non entrambi
  const mainOutput = output || summary;

  // Parse del JSON dettagliato
  let detailedResults = null;
  try {
    detailedResults = typeof detailed_results_json === 'string' 
      ? JSON.parse(detailed_results_json)
      : detailed_results_json;
  } catch (e) {
    console.log('Errore nel parsing del JSON dettagliato', e);
  }

  return (
    <div className="space-y-6">
      {/* Output Summary */}
      <div className="bg-gradient-to-r from-indigo-50 to-blue-50 p-5 rounded-lg border border-indigo-100">
        <h3 className="font-semibold text-indigo-800 text-lg mb-3 flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
          </svg>
          Risultato
        </h3>
        <p className="text-indigo-700 text-lg font-medium">{mainOutput}</p>
        
        {execution_time_seconds && (
          <div className="mt-3 flex items-center text-indigo-600 text-sm">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
            </svg>
            Completato in {execution_time_seconds.toFixed(1)}s
          </div>
        )}
      </div>

      {/* Key Points - Stilizzati meglio */}
      {(Array.isArray(key_points) && key_points.length > 0) || 
       (result.keyPoints && Array.isArray(result.keyPoints) && result.keyPoints.length > 0) ? (
        <div className="bg-purple-50 p-5 rounded-lg border border-purple-100">
          <h3 className="font-semibold text-purple-800 text-lg mb-3 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z" />
            </svg>
            Punti Chiave
          </h3>
          <ul className="space-y-2">
            {(key_points.length > 0 ? key_points : result.keyPoints).map((point, index) => (
              <li key={index} className="flex">
                <span className="bg-purple-200 text-purple-800 h-6 w-6 rounded-full flex items-center justify-center text-sm mr-3 flex-shrink-0">
                  {index + 1}
                </span>
                <span className="text-purple-800">{point}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {/* Next Steps */}
      {next_steps && next_steps.length > 0 && (
        <div className="bg-green-50 p-5 rounded-lg border border-green-100">
          <h3 className="font-semibold text-green-800 text-lg mb-3 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L9 9.414V13a1 1 0 102 0V9.414l1.293 1.293a1 1 0 001.414-1.414z" clipRule="evenodd" />
            </svg>
            Prossimi Passi
          </h3>
          <ul className="space-y-2">
            {next_steps.map((step, index) => (
              <li key={index} className="flex">
                <span className="bg-green-200 text-green-800 h-6 w-6 rounded-full flex items-center justify-center text-sm mr-3 flex-shrink-0">
                  {index + 1}
                </span>
                <span className="text-green-800">{step}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Detailed Results - Enhanced with better data recognition */}
      {(detailedResults || result.audience_profile || result.competitors) && (
        <div className="bg-white p-5 rounded-lg border border-gray-200">
          <h3 className="font-semibold text-gray-800 text-lg mb-4 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
            </svg>
            Dettagli
          </h3>
          
          {renderEnhancedDetailedResults(detailedResults || result.audience_profile || result.competitors || {})}
        </div>
      )}

      {/* Technical Details - Collapsible */}
      <details className="group">
        <summary className="list-none cursor-pointer">
          <div className="flex items-center p-3 bg-gray-50 hover:bg-gray-100 rounded-md transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-500 mr-2 group-open:rotate-90 transition-transform" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
            <span className="font-medium text-gray-700">Dettagli Tecnici</span>
          </div>
        </summary>
        
        <div className="p-4 mt-2 bg-gray-50 rounded-md border border-gray-200 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Metriche di Esecuzione</h4>
            <div className="space-y-2">
              {cost_estimated && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Costo stimato:</span>
                  <span className="font-medium">${cost_estimated.toFixed(6)}</span>
                </div>
              )}
              {execution_time_seconds && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Tempo di esecuzione:</span>
                  <span className="font-medium">{execution_time_seconds.toFixed(2)}s</span>
                </div>
              )}
              {tokens_used && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Token utilizzati:</span>
                  <span className="font-medium">
                    {tokens_used.input + tokens_used.output} 
                    <span className="text-xs text-gray-400 ml-1">
                      ({tokens_used.input} input, {tokens_used.output} output)
                    </span>
                  </span>
                </div>
              )}
            </div>
          </div>
          
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Informazioni di Esecuzione</h4>
            <div className="space-y-2">
              {result.model_used && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Modello:</span>
                  <span className="font-medium">{result.model_used}</span>
                </div>
              )}
              {result.status_detail && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Stato:</span>
                  <span className="font-medium">{result.status_detail}</span>
                </div>
              )}
              {result.task_id && (
                <div className="flex justify-between">
                  <span className="text-gray-500">ID Task:</span>
                  <span className="font-medium font-mono text-xs">{result.task_id}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </details>

      {/* Raw JSON View - Collapsible */}
      <details className="group">
        <summary className="list-none cursor-pointer">
          <div className="flex items-center p-3 bg-gray-50 hover:bg-gray-100 rounded-md transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-500 mr-2 group-open:rotate-90 transition-transform" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
            <span className="font-medium text-gray-700">Visualizza JSON Grezzo</span>
          </div>
        </summary>
        
        <div className="p-4 mt-2 bg-gray-50 rounded-md border border-gray-200">
          <div className="flex justify-end mb-2">
            <button 
              onClick={() => navigator.clipboard.writeText(JSON.stringify(result, null, 2))}
              className="text-xs px-3 py-1 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
            >
              Copia JSON
            </button>
          </div>
          <pre className="whitespace-pre-wrap bg-white p-4 rounded border border-gray-200 text-sm text-gray-700 overflow-auto max-h-[400px]">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      </details>
    </div>
  );
}

// Helper function to render complex nested objects with enhanced pattern recognition
function renderEnhancedDetailedResults(data) {
  if (!data || typeof data !== 'object') {
    return <p className="text-gray-500 italic">Nessun dettaglio disponibile</p>;
  }

  // Check if it's an array of competitors
  if (Array.isArray(data) && data.length > 0 && data[0].name && (data[0].description || data[0].key_features)) {
    return renderCompetitorsAnalysis(data);
  }
  
  // Check for audience profile pattern
  if (data.demographics || data.interests || data.audience_profile || data.content_preferences) {
    return renderAudienceProfile(data);
  }

  // Check for weekly themes (editorial calendar)
  if (data.weekly_themes) {
    return renderEditorialCalendar(data);
  }
  
  // Default rendering for other structured data
  return renderStructuredData(data);
}

function renderCompetitorsAnalysis(competitors) {
  return (
    <div className="space-y-5">
      <h4 className="text-md font-medium text-indigo-700 mb-3">Analisi Competitor</h4>
      
      <div className="grid grid-cols-1 gap-4">
        {competitors.map((competitor, index) => (
          <div key={index} className="bg-blue-50 p-4 rounded-lg border border-blue-100">
            <div className="flex justify-between items-start">
              <h5 className="text-lg font-semibold text-blue-800">{competitor.name}</h5>
              {competitor.market_share && (
                <span className="bg-blue-200 text-blue-800 px-2 py-1 rounded-full text-sm">
                  {competitor.market_share}
                </span>
              )}
            </div>
            
            {competitor.description && (
              <p className="text-blue-700 mt-2">{competitor.description}</p>
            )}
            
            {competitor.key_features && Array.isArray(competitor.key_features) && (
              <div className="mt-3">
                <p className="text-sm font-medium text-blue-800 mb-1">Caratteristiche chiave:</p>
                <div className="flex flex-wrap gap-2">
                  {competitor.key_features.map((feature, i) => (
                    <span key={i} className="bg-blue-200 text-blue-800 px-2 py-1 rounded-full text-xs">
                      {feature}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            {competitor.user_engagement && (
              <div className="mt-3">
                <p className="text-sm font-medium text-blue-800 mb-1">Engagement:</p>
                <p className="text-blue-700 text-sm">{competitor.user_engagement}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function renderAudienceProfile(data) {
  // Normalize different possible structures
  const audience = data.audience_profile || data;
  const demographics = audience.demographics || {};
  const interests = audience.interests || [];
  const contentPreferences = audience.content_preferences || {};
  
  return (
    <div className="space-y-5">
      <h4 className="text-md font-medium text-indigo-700 mb-3">Profilo Audience</h4>
      
      {/* Demographics */}
      {Object.keys(demographics).length > 0 && (
        <div className="bg-purple-50 p-4 rounded-lg border border-purple-100">
          <h5 className="text-purple-800 font-medium mb-2">Demografia</h5>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.entries(demographics).map(([key, value]) => (
              <div key={key} className="flex">
                <span className="text-purple-800 font-medium mr-2 capitalize">{key.replace(/_/g, ' ')}:</span>
                <span className="text-purple-700">{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Interests */}
      {interests.length > 0 && (
        <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-100">
          <h5 className="text-indigo-800 font-medium mb-2">Interessi</h5>
          <div className="flex flex-wrap gap-2">
            {interests.map((interest, index) => (
              <span key={index} className="bg-indigo-200 text-indigo-800 px-3 py-1 rounded-md text-sm">
                {interest}
              </span>
            ))}
          </div>
        </div>
      )}
      
      {/* Content Preferences */}
      {Object.keys(contentPreferences).length > 0 && (
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
          <h5 className="text-blue-800 font-medium mb-3">Preferenze di Contenuto</h5>
          <div className="space-y-4">
            {Object.entries(contentPreferences).map(([key, value]) => (
              <div key={key}>
                <h6 className="text-sm font-medium text-blue-800 mb-2 capitalize">{key.replace(/_/g, ' ')}:</h6>
                {Array.isArray(value) ? (
                  <div className="flex flex-wrap gap-2">
                    {value.map((item, i) => (
                      <span key={i} className="bg-blue-200 text-blue-800 px-2 py-1 rounded-full text-xs">
                        {item}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-blue-700">{value}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function renderEditorialCalendar(data) {
  return (
    <div className="space-y-5">
      {/* Weekly Themes */}
      <div>
        <h4 className="text-md font-medium text-indigo-700 mb-3">Temi Settimanali</h4>
        <div className="grid grid-cols-2 gap-3">
          {Object.entries(data.weekly_themes).map(([week, theme]) => (
            <div key={week} className="bg-indigo-50 p-3 rounded-lg border border-indigo-100">
              <p className="font-medium text-indigo-800">{week.replace('_', ' ').toUpperCase()}</p>
              <p className="text-indigo-700">{theme}</p>
            </div>
          ))}
        </div>
      </div>
      
      {/* Posting Schedule */}
      {data.posting_schedule && (
        <div>
          <h4 className="text-md font-medium text-indigo-700 mb-3">Calendario di Pubblicazione</h4>
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
            <div className="flex justify-between mb-3">
              <div>
                <p className="text-blue-800 font-medium">Post settimanali</p>
                <p className="text-2xl font-bold text-blue-900">{data.posting_schedule.posts_per_week}</p>
              </div>
              <div>
                <p className="text-blue-800 font-medium">Reels settimanali</p>
                <p className="text-2xl font-bold text-blue-900">{data.posting_schedule.reels_per_week}</p>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-blue-800 font-medium mb-2">Giorni Post</p>
                <div className="flex flex-wrap gap-2">
                  {data.posting_schedule.post_days.map(day => (
                    <span key={day} className="bg-blue-200 text-blue-800 px-2 py-1 rounded-full text-xs">
                      {day}
                    </span>
                  ))}
                </div>
              </div>
              
              <div>
                <p className="text-blue-800 font-medium mb-2">Giorni Reels</p>
                <div className="flex flex-wrap gap-2">
                  {data.posting_schedule.reels_days.map(day => (
                    <span key={day} className="bg-purple-200 text-purple-800 px-2 py-1 rounded-full text-xs">
                      {day}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Content Types */}
      {data.content_types && (
        <div>
          <h4 className="text-md font-medium text-indigo-700 mb-3">Tipi di Contenuto</h4>
          <div className="flex flex-wrap gap-2">
            {data.content_types.map(type => (
              <span key={type} className="bg-green-100 text-green-800 px-3 py-1.5 rounded-md">
                {type}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function renderStructuredData(data) {
  if (Array.isArray(data)) {
    return (
      <div className="bg-gray-50 rounded-lg p-4 overflow-auto max-h-[500px]">
        <div className="space-y-4">
          {data.map((item, index) => (
            <div key={index} className="p-3 bg-white rounded-md border border-gray-200">
              {typeof item === 'object' ? (
                <div>
                  {Object.entries(item).map(([key, value]) => (
                    <div key={key} className="mb-2">
                      <span className="font-medium text-gray-700 capitalize">{key.replace(/_/g, ' ')}:</span>
                      <span className="ml-2">{
                        typeof value === 'object' 
                          ? JSON.stringify(value) 
                          : Array.isArray(value) 
                            ? value.join(', ') 
                            : value
                      }</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div>{item}</div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  }
  
  return (
    <div className="space-y-4">
      {Object.entries(data).map(([key, value]) => (
        <div key={key} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <h4 className="text-md font-medium text-gray-800 mb-2 capitalize">
            {key.replace(/_/g, ' ')}
          </h4>
          
          {typeof value === 'object' ? (
            Array.isArray(value) ? (
              <div className="flex flex-wrap gap-2">
                {value.map((item, i) => (
                  <span key={i} className="bg-gray-200 text-gray-800 px-3 py-1 rounded-md text-sm">
                    {typeof item === 'object' ? JSON.stringify(item) : item}
                  </span>
                ))}
              </div>
            ) : (
              <pre className="bg-white p-3 rounded-md overflow-auto text-sm">
                {JSON.stringify(value, null, 2)}
              </pre>
            )
          ) : (
            <p className="text-gray-700">{value}</p>
          )}
        </div>
      ))}
    </div>
  );
}