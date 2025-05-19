import React from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';

// Interfaccia per le dimensioni di competenza
interface SkillDimension {
  name: string;
  value: number;
  fullMark: number;
}

interface AgentSkillRadarChartProps {
  skills: SkillDimension[];
  title?: string;
  size?: number;
  className?: string;
  colorScheme?: 'agent' | 'team';
}

const AgentSkillRadarChart: React.FC<AgentSkillRadarChartProps> = ({ 
  skills, 
  title, 
  size = 300,
  className = '',
  colorScheme = 'agent'
}) => {
  // Assicuriamoci di avere sempre esattamente 6 dimensioni per il radar chart
  const normalizedSkills = skills.slice(0, 6);
  
  // Padding per rendere il grafico più leggibile
  const paddingSize = size * 0.15;
  
  // Colori in base allo schema scelto
  const fillColor = colorScheme === 'agent' ? 'rgba(99, 102, 241, 0.6)' : 'rgba(139, 92, 246, 0.6)';
  const strokeColor = colorScheme === 'agent' ? '#4f46e5' : '#7c3aed';
  
  return (
    <div className={`flex flex-col items-center ${className}`}>
      {title && <h3 className="text-sm font-medium text-center mb-2">{title}</h3>}
      <div style={{ width: size, height: size }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="70%" data={normalizedSkills} margin={{ top: paddingSize, right: paddingSize, bottom: paddingSize, left: paddingSize }}>
            <PolarGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <PolarAngleAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 11 }} />
            <PolarRadiusAxis domain={[0, 5]} tick={{ fill: '#6b7280', fontSize: 10 }} />
            <Radar
              name={title || "Skills"}
              dataKey="value"
              stroke={strokeColor}
              fill={fillColor}
              fillOpacity={0.6}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// Helper per convertire livelli di skill in valori numerici
export const skillLevelToValue = (level?: string): number => {
  if (!level) return 0;
  switch(level.toLowerCase()) {
    case 'beginner': return 1;
    case 'intermediate': return 3;
    case 'expert': return 5;
    default: return 0;
  }
};

// Helper per tradurre i trait in valori numerici
export const traitToValue = (traits: string[] | null | undefined, trait: string): number => {
  if (!traits || !Array.isArray(traits)) return 0;
  return traits.includes(trait) ? 4 : 0;
};

// Helper per calcolare le dimensioni di un agente
export const calculateAgentDimensions = (agent: any): SkillDimension[] => {
  if (!agent) return [];
  
  const dimensions: SkillDimension[] = [];
  
  // Raccogliamo le hard skills
  if (agent.hard_skills && Array.isArray(agent.hard_skills)) {
    agent.hard_skills.forEach((skill: any) => {
      if (skill.name && skill.level) {
        dimensions.push({
          name: skill.name,
          value: skillLevelToValue(skill.level),
          fullMark: 5
        });
      }
    });
  }
  
  // Aggiungiamo le soft skills
  if (agent.soft_skills && Array.isArray(agent.soft_skills)) {
    agent.soft_skills.forEach((skill: any) => {
      if (skill.name && skill.level) {
        dimensions.push({
          name: skill.name,
          value: skillLevelToValue(skill.level),
          fullMark: 5
        });
      }
    });
  }
  
  // Aggiungiamo tratti di personalità rilevanti
  const personalityTraits = [
    'analytical', 'creative', 'detail-oriented', 
    'collaborative', 'decisive', 'innovative',
    'adaptable', 'diplomatic', 'methodical', 'proactive'
  ];
  
  personalityTraits.forEach(trait => {
    dimensions.push({
      name: trait.charAt(0).toUpperCase() + trait.slice(1).replace(/-/g, ' '),
      value: traitToValue(agent.personality_traits, trait),
      fullMark: 5
    });
  });
  
  // Prendiamo le 6 dimensioni con i valori più alti
  return dimensions
    .sort((a, b) => b.value - a.value)
    .slice(0, 6);
};

// Helper per calcolare le dimensioni medie del team
export const calculateTeamDimensions = (agents: any[]): SkillDimension[] => {
  if (!agents || agents.length === 0) return [];
  
  // Raccogli tutte le dimensioni da tutti gli agenti
  const allDimensions: Record<string, number[]> = {};
  
  agents.forEach(agent => {
    const agentDimensions = calculateAgentDimensions(agent);
    agentDimensions.forEach(dim => {
      if (!allDimensions[dim.name]) {
        allDimensions[dim.name] = [];
      }
      allDimensions[dim.name].push(dim.value);
    });
  });
  
  // Calcola la media per ogni dimensione
  const averagedDimensions: SkillDimension[] = [];
  for (const [name, values] of Object.entries(allDimensions)) {
    const average = values.reduce((sum, val) => sum + val, 0) / values.length;
    averagedDimensions.push({
      name,
      value: Number(average.toFixed(1)),
      fullMark: 5
    });
  }
  
  // Seleziona le 6 dimensioni più rilevanti (quelle con media più alta)
  return averagedDimensions
    .sort((a, b) => b.value - a.value)
    .slice(0, 6);
};

export default AgentSkillRadarChart;