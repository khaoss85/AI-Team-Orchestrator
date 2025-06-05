import React, { useState, useEffect } from 'react';

const TeamExplanationAnimation = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isAnimating, setIsAnimating] = useState(true);

  const steps = [
    {
      id: 'intro',
      title: 'Team Reale vs Replica AI',
      description: 'Trasformiamo un singolo LLM in una squadra auto-gestita, misurabile e antifrode',
      icon: '👥',
      highlight: 'Team reale ma composto da agenti AI autonomi'
    },
    {
      id: 'director',
      title: 'AI Director',
      description: 'Analizza il progetto e crea il team ottimale',
      icon: '🎯',
      highlight: 'Strategia e budget di profondità'
    },
    {
      id: 'manager',
      title: 'AI Manager',
      description: 'Coordina il team e gestisce gli handoff',
      icon: '🧠',
      highlight: 'Project manager per evitare loop infiniti'
    },
    {
      id: 'specialists',
      title: 'Specialist Skills',
      description: 'Embeddings personali + vector-DB dedicata',
      icon: '⚡',
      highlight: 'Strumenti potenziati per ogni specialista'
    },
    {
      id: 'persona',
      title: 'Soft Skills',
      description: 'Prompt persona collaborativo e risultato-oriented',
      icon: '🎭',
      highlight: 'Personalità dedicate per ogni ruolo'
    },
    {
      id: 'tools',
      title: 'Strumenti',
      description: 'API/tool call: Instagram, SMTP, SQL...',
      icon: '🔧',
      highlight: 'Tool-wrapper specializzati'
    },
    {
      id: 'communication',
      title: 'Colleghi',
      description: 'Message passing con protocollo JSON',
      icon: '💬',
      highlight: 'Comunicazione strutturata tra agenti'
    },
    {
      id: 'qa',
      title: 'QA Interna',
      description: 'Critic Agent con scoring + grounded-RAG',
      icon: '🛡️',
      highlight: 'Sistema antifrode e anti-allucinazioni'
    },
    {
      id: 'human',
      title: 'Human in the Loop',
      description: 'Approvazione per passaggi critici',
      icon: '👤',
      highlight: 'Controllo umano su budget e decisioni critiche'
    }
  ];

  useEffect(() => {
    if (!isAnimating) return;

    const interval = setInterval(() => {
      setCurrentStep((prev) => (prev + 1) % steps.length);
    }, 3000);

    return () => clearInterval(interval);
  }, [isAnimating, steps.length]);

  const currentStepData = steps[currentStep];

  return (
    <div className="bg-gradient-to-br from-indigo-50 via-purple-50 to-blue-50 rounded-xl p-8 border border-indigo-200 shadow-lg ai-team-container no-spacing">
      {/* Main Title */}
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-3">
          Come Funziona il Nostro Team AI
        </h2>
        <p className="text-gray-700 leading-relaxed max-w-4xl mx-auto">
          <strong>Portiamo in cloud l'organigramma:</strong> un AI Director crea il team mettendo al centro un AI Manager 
          che forma e coordina specialisti virtuali, ognuno equipaggiato con skill, tool e personalità dedicati. 
          Il Critic garantisce qualità e dati veri. <strong>Risultato:</strong> la stessa collaborazione di un team umano, 
          ma scalabile, 24/7 e misurabile a token-cost.
        </p>
      </div>

      {/* Animation Controls */}
      <div className="flex justify-center mb-6">
        <button
          onClick={() => setIsAnimating(!isAnimating)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            isAnimating 
              ? 'bg-red-100 text-red-700 hover:bg-red-200' 
              : 'bg-green-100 text-green-700 hover:bg-green-200'
          }`}
        >
          {isAnimating ? '⏸️ Pausa' : '▶️ Riproduci'} Animazione
        </button>
      </div>

      {/* Main Animation Area */}
      <div className="relative">
        {/* Central Hub */}
        <div className="flex justify-center mb-8">
          <div className="relative">
            {/* Central Circle - AI Manager */}
            <div className={`w-32 h-32 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white text-4xl font-bold shadow-lg transform transition-all duration-500 ${
              currentStep === 2 ? 'scale-110 ring-4 ring-purple-300' : ''
            }`}>
              🧠
            </div>
            <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 text-center">
              <div className="text-sm font-medium text-purple-700">AI Manager</div>
              <div className="text-xs text-purple-600">Coordinamento</div>
            </div>

            {/* Orbiting Elements */}
            {[
              { icon: '🎯', label: 'Director', angle: 0, step: 1 },
              { icon: '⚡', label: 'Specialist', angle: 60, step: 3 },
              { icon: '🎭', label: 'Persona', angle: 120, step: 4 },
              { icon: '🔧', label: 'Tools', angle: 180, step: 5 },
              { icon: '💬', label: 'Communication', angle: 240, step: 6 },
              { icon: '🛡️', label: 'QA Critic', angle: 300, step: 7 }
            ].map((element, index) => {
              const isActive = currentStep === element.step;
              const x = Math.round(Math.cos((element.angle * Math.PI) / 180) * 100);
              const y = Math.round(Math.sin((element.angle * Math.PI) / 180) * 100);

              return (
                <div
                  key={element.label}
                  className={`absolute w-16 h-16 rounded-full bg-white flex items-center justify-center text-2xl shadow-md transform transition-all duration-500 z-float ${
                    isActive ? 'scale-125 ring-3 ring-blue-300 bg-blue-50' : 'hover:scale-105'
                  }`}
                  style={{
                    left: `calc(50% + ${x}px - 2rem)`,
                    top: `calc(50% + ${y}px - 2rem)`,
                  }}
                >
                  {element.icon}
                  {isActive && (
                    <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 whitespace-nowrap">
                      <div className="text-xs font-medium text-blue-700">{element.label}</div>
                    </div>
                  )}
                </div>
              );
            })}

            {/* Connection Lines */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ width: '200px', height: '200px', left: '-34px', top: '-34px' }}>
              {[0, 60, 120, 180, 240, 300].map((angle, index) => {
                const x1 = 100 + Math.cos((angle * Math.PI) / 180) * 50;
                const y1 = 100 + Math.sin((angle * Math.PI) / 180) * 50;
                const x2 = 100 + Math.cos((angle * Math.PI) / 180) * 84;
                const y2 = 100 + Math.sin((angle * Math.PI) / 180) * 84;
                
                return (
                  <line
                    key={angle}
                    x1={x1}
                    y1={y1}
                    x2={x2}
                    y2={y2}
                    stroke="#6366f1"
                    strokeWidth="2"
                    strokeDasharray="5,5"
                    className={`transition-opacity duration-500 ${
                      currentStep === index + 1 ? 'opacity-100' : 'opacity-30'
                    }`}
                  />
                );
              })}
            </svg>
          </div>
        </div>

        {/* Human in the Loop - Separate */}
        <div className={`flex justify-center transform transition-all duration-500 ${
          currentStep === 8 ? 'scale-110' : ''
        }`}>
          <div className={`bg-gradient-to-r from-green-500 to-emerald-600 rounded-lg p-4 text-white flex items-center space-x-3 shadow-lg ${
            currentStep === 8 ? 'ring-4 ring-green-300' : ''
          }`}>
            <div className="text-2xl">👤</div>
            <div>
              <div className="font-medium">Human in the Loop</div>
              <div className="text-sm opacity-90">Approvazioni critiche</div>
            </div>
          </div>
        </div>
      </div>

      {/* Step Information */}
      <div className="mt-8 bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <div className="flex items-start space-x-4">
          <div className="text-4xl">{currentStepData.icon}</div>
          <div className="flex-1">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              {currentStepData.title}
            </h3>
            <p className="text-gray-700 mb-3">
              {currentStepData.description}
            </p>
            <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3">
              <div className="text-sm font-medium text-indigo-800">
                💡 {currentStepData.highlight}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Step Indicators */}
      <div className="flex justify-center mt-6 space-x-2">
        {steps.map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrentStep(index)}
            className={`w-3 h-3 rounded-full transition-all duration-300 ${
              index === currentStep 
                ? 'bg-indigo-600 scale-125' 
                : 'bg-gray-300 hover:bg-gray-400'
            }`}
          />
        ))}
      </div>

      {/* Benefits Footer */}
      <div className="mt-8 bg-gradient-to-r from-purple-100 to-indigo-100 rounded-lg p-6 border border-purple-200">
        <h4 className="font-semibold text-purple-800 mb-3">🚀 Vantaggi del Sistema</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center space-x-2">
            <div className="text-green-600">✅</div>
            <span className="text-sm text-purple-700">Scalabile 24/7</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="text-green-600">✅</div>
            <span className="text-sm text-purple-700">Costi misurabili</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="text-green-600">✅</div>
            <span className="text-sm text-purple-700">Output verificati</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="text-green-600">✅</div>
            <span className="text-sm text-purple-700">Anti-allucinazioni</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="text-green-600">✅</div>
            <span className="text-sm text-purple-700">Controllo umano</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="text-green-600">✅</div>
            <span className="text-sm text-purple-700">Specializzazione</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TeamExplanationAnimation;