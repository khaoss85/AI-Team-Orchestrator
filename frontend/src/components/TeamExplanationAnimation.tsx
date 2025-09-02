import React, { useState, useEffect } from 'react';

const TeamExplanationAnimation = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isAnimating, setIsAnimating] = useState(true);

  const steps = [
    {
      id: 'intro',
      title: 'Real Team vs AI Replica',
      description: 'We transform a single LLM into a self-managed, measurable and anti-fraud team',
      icon: '👥',
      highlight: 'Real team but composed of autonomous AI agents'
    },
    {
      id: 'director',
      title: 'AI Director',
      description: 'Analyzes the project and creates the optimal team',
      icon: '🎯',
      highlight: 'In-depth strategy and budget analysis'
    },
    {
      id: 'manager',
      title: 'AI Manager',
      description: 'Coordinates the team and manages handoffs',
      icon: '🧠',
      highlight: 'Project manager to avoid infinite loops'
    },
    {
      id: 'specialists',
      title: 'Specialist Skills',
      description: 'Personal embeddings + dedicated vector-DB',
      icon: '⚡',
      highlight: 'Enhanced tools for each specialist'
    },
    {
      id: 'persona',
      title: 'Soft Skills',
      description: 'Collaborative and result-oriented persona prompts',
      icon: '🎭',
      highlight: 'Dedicated personalities for each role'
    },
    {
      id: 'tools',
      title: 'Tools',
      description: 'API/tool calls: Instagram, SMTP, SQL...',
      icon: '🔧',
      highlight: 'Specialized tool-wrappers'
    },
    {
      id: 'communication',
      title: 'Colleagues',
      description: 'Message passing with JSON protocol',
      icon: '💬',
      highlight: 'Structured communication between agents'
    },
    {
      id: 'qa',
      title: 'Internal QA',
      description: 'Critic Agent with scoring + grounded-RAG',
      icon: '🛡️',
      highlight: 'Anti-fraud and anti-hallucination system'
    },
    {
      id: 'human',
      title: 'Human in the Loop',
      description: 'Approval for critical steps',
      icon: '👤',
      highlight: 'Human control over budget and critical decisions'
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
    <div className="bg-gradient-to-br from-indigo-50 via-purple-50 to-blue-50 rounded-xl p-8 border border-indigo-200 shadow-lg overflow-hidden">
      {/* Main Title */}
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-3">
          How Our AI Team Works
        </h2>
        <p className="text-gray-700 leading-relaxed max-w-4xl mx-auto">
          <strong>We bring the organizational chart to the cloud:</strong> an AI Director creates the team centered around an AI Manager 
          that trains and coordinates virtual specialists, each equipped with dedicated skills, tools and personalities. 
          The Critic ensures quality and real data. <strong>Result:</strong> the same collaboration of a human team, 
          but scalable, 24/7 and measurable at token-cost.
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
          {isAnimating ? '⏸️ Pause' : '▶️ Play'} Animation
        </button>
      </div>

      {/* Main Animation Area */}
      <div className="relative min-h-[400px] flex flex-col items-center">
        {/* Central Hub */}
        <div className="flex justify-center mb-16">
          <div className="relative">
            {/* Central Circle - AI Manager */}
            <div className={`w-32 h-32 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white text-4xl font-bold shadow-lg transform transition-all duration-500 relative z-10 ${
              currentStep === 2 ? 'scale-110 ring-4 ring-purple-300' : ''
            }`}>
              🧠
            </div>
            <div className="absolute -bottom-12 left-1/2 transform -translate-x-1/2 text-center z-20">
              <div className="text-sm font-medium text-purple-700">AI Manager</div>
              <div className="text-xs text-purple-600">Coordination</div>
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
              const radius = 120; // Increased radius for better spacing
              const x = Math.round(Math.cos((element.angle * Math.PI) / 180) * radius);
              const y = Math.round(Math.sin((element.angle * Math.PI) / 180) * radius);

              return (
                <div
                  key={element.label}
                  className={`absolute w-16 h-16 rounded-full bg-white flex items-center justify-center text-2xl shadow-md transform transition-all duration-500 z-30 ${
                    isActive ? 'scale-125 ring-3 ring-blue-300 bg-blue-50' : 'hover:scale-105'
                  }`}
                  style={{
                    left: `calc(50% + ${x}px - 2rem)`,
                    top: `calc(50% + ${y}px - 2rem)`,
                  }}
                >
                  {element.icon}
                  {isActive && (
                    <div className="absolute -bottom-10 left-1/2 transform -translate-x-1/2 whitespace-nowrap z-40">
                      <div className="text-xs font-medium text-blue-700 bg-white px-2 py-1 rounded shadow-sm">{element.label}</div>
                    </div>
                  )}
                </div>
              );
            })}

            {/* Connection Lines */}
            <svg className="absolute inset-0 pointer-events-none z-0" style={{ width: '300px', height: '300px', left: '-84px', top: '-84px' }}>
              {[0, 60, 120, 180, 240, 300].map((angle, index) => {
                const radius = 120;
                const centerX = 150;
                const centerY = 150;
                const x1 = centerX + Math.cos((angle * Math.PI) / 180) * 64;
                const y1 = centerY + Math.sin((angle * Math.PI) / 180) * 64;
                const x2 = centerX + Math.cos((angle * Math.PI) / 180) * (radius - 16);
                const y2 = centerY + Math.sin((angle * Math.PI) / 180) * (radius - 16);
                
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
        <div className={`flex justify-center mt-8 transform transition-all duration-500 z-20 ${
          currentStep === 8 ? 'scale-110' : ''
        }`}>
          <div className={`bg-gradient-to-r from-green-500 to-emerald-600 rounded-lg p-4 text-white flex items-center space-x-3 shadow-lg relative ${
            currentStep === 8 ? 'ring-4 ring-green-300' : ''
          }`}>
            <div className="text-2xl">👤</div>
            <div>
              <div className="font-medium">Human in the Loop</div>
              <div className="text-sm opacity-90">Critical approvals</div>
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
        <h4 className="font-semibold text-purple-800 mb-3">🚀 System Benefits</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center space-x-2">
            <div className="text-green-600">✅</div>
            <span className="text-sm text-purple-700">Scalable 24/7</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="text-green-600">✅</div>
            <span className="text-sm text-purple-700">Measurable costs</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="text-green-600">✅</div>
            <span className="text-sm text-purple-700">Verified outputs</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="text-green-600">✅</div>
            <span className="text-sm text-purple-700">Anti-hallucinations</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="text-green-600">✅</div>
            <span className="text-sm text-purple-700">Human control</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="text-green-600">✅</div>
            <span className="text-sm text-purple-700">Specialization</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TeamExplanationAnimation;