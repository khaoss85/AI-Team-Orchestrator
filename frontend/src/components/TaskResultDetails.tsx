import React, { useState } from 'react';

export default function TaskResultDetails({ result }) {
  if (!result) return null;

  // Extract main fields from result
  const {
    summary,
    output,
    status,
    key_points = [],
    next_steps = [],
    detailed_results_json,
    execution_time_seconds,
    cost_estimated,
    tokens_used,
    model_used,
    agent_name,
    agent_role,
    assigned_agent_name,
    assigned_agent_role,
    rationale
  } = result;

  // Use only one source for the main content - prefer summary, then output
  const mainContent = summary || output || "Nessun risultato disponibile";

  // Parse detailed JSON if available
  let detailedResults = null;
  try {
    if (detailed_results_json) {
      detailedResults = typeof detailed_results_json === 'string' 
        ? JSON.parse(detailed_results_json)
        : detailed_results_json;
    } else if (result.detailed_results) {
      // Alternative field name
      detailedResults = result.detailed_results;
    }
  } catch (e) {
    console.log('Errore nel parsing del JSON dettagliato', e);
  }

  // Combine key points from different possible sources
  const allKeyPoints = Array.isArray(key_points) && key_points.length > 0 
    ? key_points 
    : (result.keyPoints && Array.isArray(result.keyPoints)) 
      ? result.keyPoints 
      : [];

  return (
    <div className="space-y-6">
      {/* Main Output Section - Improved styling */}
      <div className="bg-gradient-to-br from-indigo-50 to-blue-50 p-6 rounded-lg border border-indigo-100 shadow-sm">
        <h3 className="font-semibold text-indigo-800 text-lg mb-4 flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
          </svg>
          Risultato
        </h3>
        <div className="text-indigo-900 text-lg leading-relaxed bg-white bg-opacity-60 p-5 rounded-lg shadow-inner whitespace-pre-line">
          {mainContent}
        </div>
        
        {execution_time_seconds && (
          <div className="mt-4 flex items-center text-indigo-600 text-sm">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
            </svg>
            Completato in {execution_time_seconds.toFixed(1)}s
          </div>
        )}

        {rationale && (
          <div className="mt-4 bg-white bg-opacity-60 p-4 rounded-lg">
            <h4 className="font-medium text-indigo-700 mb-1">Rationale</h4>
            <p className="text-indigo-900 whitespace-pre-line">{rationale}</p>
          </div>
        )}
      </div>

      {/* Key Points Section - Improved styling */}
      {allKeyPoints.length > 0 && (
        <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-6 rounded-lg border border-purple-100 shadow-sm">
          <h3 className="font-semibold text-purple-800 text-lg mb-4 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z" />
            </svg>
            Punti Chiave
          </h3>
          <ul className="space-y-3">
            {allKeyPoints.map((point, index) => (
              <li key={index} className="flex bg-white bg-opacity-60 p-3 rounded-lg shadow-sm">
                <span className="bg-purple-200 text-purple-800 h-6 w-6 rounded-full flex items-center justify-center text-sm mr-3 flex-shrink-0 shadow-sm">
                  {index + 1}
                </span>
                <span className="text-purple-900">{point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Next Steps Section - Improved styling */}
      {next_steps && next_steps.length > 0 && (
        <div className="bg-gradient-to-br from-green-50 to-teal-50 p-6 rounded-lg border border-green-100 shadow-sm">
          <h3 className="font-semibold text-green-800 text-lg mb-4 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L9 9.414V13a1 1 0 102 0V9.414l1.293 1.293a1 1 0 001.414-1.414z" clipRule="evenodd" />
            </svg>
            Prossimi Passi
          </h3>
          <ul className="space-y-3">
            {next_steps.map((step, index) => (
              <li key={index} className="flex bg-white bg-opacity-60 p-3 rounded-lg shadow-sm">
                <span className="bg-green-200 text-green-800 h-6 w-6 rounded-full flex items-center justify-center text-sm mr-3 flex-shrink-0 shadow-sm">
                  {index + 1}
                </span>
                <span className="text-green-900">{step}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Detailed Results Section - Improved styling */}
      {detailedResults && (
        <div className="bg-gradient-to-br from-gray-50 to-slate-50 p-6 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="font-semibold text-gray-800 text-lg mb-4 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
            </svg>
            Dettagli
          </h3>
          
          <div className="bg-white p-4 rounded-lg shadow-inner">
            <GenericDataRenderer data={detailedResults} />
          </div>
        </div>
      )}

      {/* Technical Details - Collapsible with improved styling */}
      <details className="group bg-gray-50 rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <summary className="list-none cursor-pointer">
          <div className="flex items-center p-4 bg-gray-100 hover:bg-gray-200 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-600 mr-2 group-open:rotate-90 transition-transform" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
            <span className="font-medium text-gray-700">Dettagli Tecnici</span>
          </div>
        </summary>
        
        <div className="p-5 bg-gray-50">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <h4 className="text-sm font-medium text-gray-700 mb-3 border-b pb-2">Metriche di Esecuzione</h4>
              <div className="space-y-3">
                {cost_estimated && (
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Costo stimato:</span>
                    <span className="font-medium bg-blue-50 px-3 py-1 rounded-full text-blue-700">${cost_estimated.toFixed(6)}</span>
                  </div>
                )}
                {execution_time_seconds && (
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Tempo di esecuzione:</span>
                    <span className="font-medium bg-green-50 px-3 py-1 rounded-full text-green-700">{execution_time_seconds.toFixed(2)}s</span>
                  </div>
                )}
                {tokens_used && (
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Token utilizzati:</span>
                    <span className="font-medium bg-purple-50 px-3 py-1 rounded-full text-purple-700">
                      {tokens_used.input + tokens_used.output} 
                      <span className="text-xs text-gray-600 ml-1">
                        ({tokens_used.input} in, {tokens_used.output} out)
                      </span>
                    </span>
                  </div>
                )}
              </div>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <h4 className="text-sm font-medium text-gray-700 mb-3 border-b pb-2">Informazioni di Esecuzione</h4>
              <div className="space-y-3">
                {result.model_used && (
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Modello:</span>
                    <span className="font-medium bg-indigo-50 px-3 py-1 rounded-full text-indigo-700">{result.model_used}</span>
                  </div>
                )}
                {(agent_name || assigned_agent_name) && (
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Agente:</span>
                    <span className="font-medium bg-teal-50 px-3 py-1 rounded-full text-teal-700">
                      {agent_name || assigned_agent_name}
                      {agent_role || assigned_agent_role ? ` (${agent_role || assigned_agent_role})` : ''}
                    </span>
                  </div>
                )}
                {result.status_detail && (
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Stato:</span>
                    <span className="font-medium bg-amber-50 px-3 py-1 rounded-full text-amber-700">{result.status_detail}</span>
                  </div>
                )}
                {result.task_id && (
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">ID Task:</span>
                    <span className="font-medium bg-gray-100 px-3 py-1 rounded-full text-gray-700 font-mono text-xs">{result.task_id}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </details>

      {/* Raw JSON View - Collapsible with improved styling */}
      <details className="group bg-gray-50 rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <summary className="list-none cursor-pointer">
          <div className="flex items-center p-4 bg-gray-100 hover:bg-gray-200 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-600 mr-2 group-open:rotate-90 transition-transform" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
            <span className="font-medium text-gray-700">Visualizza JSON Grezzo</span>
          </div>
        </summary>
        
        <div className="p-5 bg-gray-50">
          <div className="flex justify-end mb-3">
            <button 
              onClick={() => {
                const jsonStr = JSON.stringify(result, null, 2);
                navigator.clipboard.writeText(jsonStr);
                // Feedback visivo
                const btn = event.currentTarget;
                const originalText = btn.innerText;
                btn.innerText = 'Copiato!';
                btn.classList.add('bg-green-200', 'text-green-800');
                setTimeout(() => {
                  btn.innerText = originalText;
                  btn.classList.remove('bg-green-200', 'text-green-800');
                }, 2000);
              }}
              className="text-xs px-3 py-1.5 bg-indigo-100 text-indigo-700 rounded-md hover:bg-indigo-200 transition-colors flex items-center shadow-sm"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              Copia JSON
            </button>
          </div>
          <pre className="whitespace-pre-wrap bg-slate-800 text-slate-100 p-5 rounded-lg border border-slate-700 text-sm overflow-auto max-h-[400px] shadow-inner font-mono">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      </details>
    </div>
  );
}

// Il componente GenericDataRenderer rimane praticamente uguale
// Universal data rendering component that handles different data structures
const GenericDataRenderer = ({ data }) => {
  // If data is null or not an object
  if (!data || typeof data !== 'object') {
    return <p className="text-gray-500 italic">Nessun dettaglio disponibile</p>;
  }

  // For arrays
  if (Array.isArray(data)) {
    return <ArrayRenderer data={data} />;
  }

  // For objects
  return <ObjectRenderer data={data} />;
};

// Component to render arrays - with improved styling
const ArrayRenderer = ({ data }) => {
  if (data.length === 0) {
    return <p className="text-gray-500 italic">Array vuoto</p>;
  }

  // Check if array contains simple items
  const hasSimpleItems = data.some(item => typeof item !== 'object' || item === null);

  if (hasSimpleItems) {
    return (
      <div className="flex flex-wrap gap-2 mb-3">
        {data.map((item, index) => (
          <span key={index} className="bg-blue-100 text-blue-800 px-3 py-1.5 rounded-md text-sm shadow-sm">
            {String(item)}
          </span>
        ))}
      </div>
    );
  }

  // For arrays of objects
  return (
    <div className="space-y-4">
      {data.map((item, index) => (
        <div key={index} className="bg-blue-50 p-4 rounded-lg border border-blue-100 shadow-sm">
          <div className="text-sm text-blue-700 font-medium mb-2 border-b border-blue-100 pb-1">Item {index + 1}</div>
          {typeof item === 'object' && item !== null ? (
            <ObjectRenderer data={item} />
          ) : (
            <span>{String(item)}</span>
          )}
        </div>
      ))}
    </div>
  );
};

// Component to render objects - with improved styling
const ObjectRenderer = ({ data, level = 0 }) => {
  // For nested levels, limit depth for readability
  const MAX_DEPTH = 3; 
  
  if (level > MAX_DEPTH) {
    return (
      <div className="p-2.5 bg-gray-100 rounded-md text-sm shadow-inner">
        <button className="text-blue-600 hover:underline flex items-center" 
                onClick={() => alert(JSON.stringify(data, null, 2))}>
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          Oggetto nidificato (clicca per visualizzare)
        </button>
      </div>
    );
  }

  // Organize properties into categories for better visual structure
  const properties = Object.entries(data);
  
  // Split properties by type for better rendering
  const simpleProps = [];
  const arrayProps = [];
  const objectProps = [];

  properties.forEach(([key, value]) => {
    if (Array.isArray(value)) {
      arrayProps.push([key, value]);
    } else if (typeof value === 'object' && value !== null) {
      objectProps.push([key, value]);
    } else {
      simpleProps.push([key, value]);
    }
  });

  return (
    <div className="space-y-4">
      {/* Simple properties */}
      {simpleProps.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {simpleProps.map(([key, value]) => (
            <div key={key} className="flex justify-between items-center bg-white p-2.5 rounded-md shadow-sm border border-gray-100">
              <span className="font-medium text-gray-700 capitalize">{key.replace(/_/g, ' ')}</span>
              <span className="text-gray-800 bg-gray-100 px-2.5 py-1 rounded-md">{String(value)}</span>
            </div>
          ))}
        </div>
      )}

      {/* Array properties */}
      {arrayProps.map(([key, value]) => (
        <div key={key} className="mt-4">
          <h4 className="text-md font-medium text-indigo-700 mb-2 capitalize border-b border-indigo-100 pb-1">{key.replace(/_/g, ' ')}</h4>
          <ArrayRenderer data={value} />
        </div>
      ))}

      {/* Object properties */}
      {objectProps.map(([key, value]) => (
        <div key={key} className="mt-4 bg-gray-50 p-4 rounded-lg border border-gray-200">
          <h4 className="text-md font-medium text-gray-700 mb-2 capitalize">{key.replace(/_/g, ' ')}</h4>
          <ObjectRenderer data={value} level={level + 1} />
        </div>
      ))}

      {/* If no properties were rendered */}
      {properties.length === 0 && (
        <p className="text-gray-500 italic">Oggetto vuoto</p>
      )}
    </div>
  );
};