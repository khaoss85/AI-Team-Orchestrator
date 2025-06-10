'use client';

import React, { useState, useEffect, useRef } from 'react';

// Configurazione flessibile per diversi domini
const DOMAIN_STYLES = {
  marketing: { color: '#3B82F6', bgColor: '#EFF6FF', icon: '📱' },
  finance: { color: '#10B981', bgColor: '#ECFDF5', icon: '💰' },
  product: { color: '#8B5CF6', bgColor: '#F3E8FF', icon: '🚀' },
  research: { color: '#F59E0B', bgColor: '#FFFBEB', icon: '🔬' },
  operations: { color: '#6B7280', bgColor: '#F9FAFB', icon: '⚙️' },
  strategy: { color: '#4F46E5', bgColor: '#EEF2FF', icon: '🎯' },
  content: { color: '#EA580C', bgColor: '#FFF7ED', icon: '📝' },
  design: { color: '#EC4899', bgColor: '#FDF2F8', icon: '🎨' },
  technology: { color: '#06B6D4', bgColor: '#ECFEFF', icon: '💻' },
  legal: { color: '#DC2626', bgColor: '#FEF2F2', icon: '⚖️' },
  hr: { color: '#059669', bgColor: '#ECFDF5', icon: '👥' },
  default: { color: '#64748B', bgColor: '#F1F5F9', icon: '📊' }
};

const IMPACT_STYLES = {
  critical: { strokeWidth: 4, strokeColor: '#DC2626', dashArray: 'none' },
  high: { strokeWidth: 3, strokeColor: '#EA580C', dashArray: 'none' },
  medium: { strokeWidth: 2, strokeColor: '#D97706', dashArray: '5,5' },
  low: { strokeWidth: 1, strokeColor: '#65A30D', dashArray: '2,3' }
};

const STATUS_STYLES = {
  updated: { borderColor: '#10B981', borderWidth: 3, pulseColor: '#10B981' },
  stale: { borderColor: '#F59E0B', borderWidth: 2, pulseColor: '#F59E0B' },
  processing: { borderColor: '#3B82F6', borderWidth: 2, pulseColor: '#3B82F6' },
  current: { borderColor: '#6B7280', borderWidth: 1, pulseColor: null },
  error: { borderColor: '#DC2626', borderWidth: 2, pulseColor: '#DC2626' }
};

export interface AssetNode {
  id: string;
  name: string;
  type: string;
  category: string; // Domain flessibile
  status: 'updated' | 'stale' | 'processing' | 'current' | 'error';
  quality_score?: number;
  last_updated: string;
  size?: 'small' | 'medium' | 'large';
  business_value?: number;
}

export interface AssetEdge {
  source: string;
  target: string;
  impact: 'critical' | 'high' | 'medium' | 'low';
  relationship_type: string; // "depends_on", "influences", "derived_from", etc.
  strength: number; // 0-1
  bidirectional?: boolean;
}

interface Props {
  nodes: AssetNode[];
  edges: AssetEdge[];
  centralNodeId?: string;
  onNodeClick?: (node: AssetNode) => void;
  onEdgeClick?: (edge: AssetEdge) => void;
  className?: string;
  interactive?: boolean;
  showLabels?: boolean;
  layout?: 'circular' | 'hierarchical' | 'force';
}

export const DependencyGraph: React.FC<Props> = ({
  nodes,
  edges,
  centralNodeId,
  onNodeClick,
  onEdgeClick,
  className = '',
  interactive = true,
  showLabels = true,
  layout = 'circular'
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [nodePositions, setNodePositions] = useState<Record<string, {x: number, y: number}>>({});
  const [svgDimensions, setSvgDimensions] = useState({ width: 800, height: 600 });

  // Calcola posizioni dei nodi basate sul layout
  useEffect(() => {
    if (nodes.length === 0) return;

    const { width, height } = svgDimensions;
    const centerX = width / 2;
    const centerY = height / 2;
    const positions: Record<string, {x: number, y: number}> = {};

    if (layout === 'circular') {
      // Layout circolare con nodo centrale
      const centralNode = nodes.find(n => n.id === centralNodeId) || nodes[0];
      const otherNodes = nodes.filter(n => n.id !== centralNode.id);
      
      // Posiziona il nodo centrale
      positions[centralNode.id] = { x: centerX, y: centerY };
      
      // Posiziona gli altri nodi in cerchio
      const radius = Math.min(width, height) * 0.3;
      otherNodes.forEach((node, index) => {
        const angle = (2 * Math.PI * index) / otherNodes.length - Math.PI / 2;
        positions[node.id] = {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle)
        };
      });
    } else if (layout === 'hierarchical') {
      // Layout gerarchico basato sulle dipendenze
      const levels = buildHierarchy(nodes, edges, centralNodeId);
      const levelHeight = height / (levels.length + 1);
      
      levels.forEach((level, levelIndex) => {
        const levelWidth = width / (level.length + 1);
        level.forEach((nodeId, nodeIndex) => {
          positions[nodeId] = {
            x: levelWidth * (nodeIndex + 1),
            y: levelHeight * (levelIndex + 1)
          };
        });
      });
    } else {
      // Layout force-directed semplificato
      nodes.forEach((node, index) => {
        const angle = (2 * Math.PI * index) / nodes.length;
        const radius = Math.min(width, height) * 0.25;
        positions[node.id] = {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle)
        };
      });
    }

    setNodePositions(positions);
  }, [nodes, edges, centralNodeId, layout, svgDimensions]);

  // Funzione helper per costruire gerarchia
  const buildHierarchy = (nodes: AssetNode[], edges: AssetEdge[], rootId?: string): string[][] => {
    const levels: string[][] = [];
    const visited = new Set<string>();
    const adjList = new Map<string, string[]>();

    // Costruisci lista di adiacenza
    edges && edges.forEach(edge => {
      if (!adjList.has(edge.source)) adjList.set(edge.source, []);
      adjList.get(edge.source)!.push(edge.target);
    });

    // BFS per costruire livelli
    const queue = [rootId || nodes[0]?.id];
    visited.add(queue[0]);
    
    while (queue.length > 0) {
      const currentLevel: string[] = [];
      const levelSize = queue.length;
      
      for (let i = 0; i < levelSize; i++) {
        const nodeId = queue.shift()!;
        currentLevel.push(nodeId);
        
        const neighbors = adjList.get(nodeId) || [];
        neighbors.forEach(neighbor => {
          if (!visited.has(neighbor)) {
            visited.add(neighbor);
            queue.push(neighbor);
          }
        });
      }
      
      if (currentLevel.length > 0) {
        levels.push(currentLevel);
      }
    }
    
    // Aggiungi nodi non visitati
    const unvisited = nodes.filter(n => !visited.has(n.id));
    if (unvisited.length > 0) {
      levels.push(unvisited.map(n => n.id));
    }
    
    return levels;
  };

  const handleNodeClick = (node: AssetNode) => {
    setSelectedNode(node.id);
    onNodeClick?.(node);
  };

  const getDomainStyle = (category: string) => {
    return DOMAIN_STYLES[category.toLowerCase() as keyof typeof DOMAIN_STYLES] || DOMAIN_STYLES.default;
  };

  const getNodeSize = (node: AssetNode) => {
    const baseSize = 40;
    const sizeMultiplier = {
      small: 0.8,
      medium: 1.0,
      large: 1.2
    };
    return baseSize * (sizeMultiplier[node.size || 'medium']);
  };

  const getEdgeStyle = (edge: AssetEdge) => {
    return IMPACT_STYLES[edge.impact];
  };

  const getStatusStyle = (status: string) => {
    return STATUS_STYLES[status as keyof typeof STATUS_STYLES] || STATUS_STYLES.current;
  };

  // Calcola path per le connessioni
  const getEdgePath = (edge: AssetEdge) => {
    const sourcePos = nodePositions[edge.source];
    const targetPos = nodePositions[edge.target];
    
    if (!sourcePos || !targetPos) return '';
    
    // Calcola offset per evitare sovrapposizione con i nodi
    const dx = targetPos.x - sourcePos.x;
    const dy = targetPos.y - sourcePos.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    const nodeRadius = 25; // Raggio medio del nodo
    
    const offsetX = (dx / distance) * nodeRadius;
    const offsetY = (dy / distance) * nodeRadius;
    
    const startX = sourcePos.x + offsetX;
    const startY = sourcePos.y + offsetY;
    const endX = targetPos.x - offsetX;
    const endY = targetPos.y - offsetY;
    
    // Curva per connessioni più eleganti
    const midX = (startX + endX) / 2;
    const midY = (startY + endY) / 2;
    const curveOffset = distance * 0.1;
    const perpX = -dy / distance * curveOffset;
    const perpY = dx / distance * curveOffset;
    
    return `M ${startX} ${startY} Q ${midX + perpX} ${midY + perpY} ${endX} ${endY}`;
  };

  const highlightedEdges = selectedNode 
    ? (edges ? edges.filter(e => e.source === selectedNode || e.target === selectedNode) : [])
    : [];

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Asset Dependencies</h3>
          <div className="flex items-center space-x-4 text-xs">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-green-500"></div>
              <span>Updated</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
              <span>Stale</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-blue-500"></div>
              <span>Processing</span>
            </div>
          </div>
        </div>
      </div>

      {/* Graph */}
      <div className="p-4">
        <svg
          ref={svgRef}
          width="100%"
          height="400"
          viewBox={`0 0 ${svgDimensions.width} ${svgDimensions.height}`}
          className="border border-gray-100 rounded"
        >
          {/* Definisci gradients e pattern */}
          <defs>
            {Object.entries(STATUS_STYLES).map(([status, style]) => 
              style.pulseColor && (
                <radialGradient key={status} id={`pulse-${status}`}>
                  <stop offset="0%" stopColor={style.pulseColor} stopOpacity="0.3" />
                  <stop offset="100%" stopColor={style.pulseColor} stopOpacity="0" />
                </radialGradient>
              )
            )}
          </defs>

          {/* Render edges */}
          <g className="edges">
            {edges && edges.map((edge, index) => {
              const style = getEdgeStyle(edge);
              const isHighlighted = highlightedEdges.includes(edge);
              
              return (
                <g key={`${edge.source}-${edge.target}-${index}`}>
                  <path
                    d={getEdgePath(edge)}
                    stroke={style.strokeColor}
                    strokeWidth={style.strokeWidth}
                    strokeDasharray={style.dashArray}
                    fill="none"
                    opacity={isHighlighted ? 1 : selectedNode ? 0.3 : 0.7}
                    className={interactive ? 'cursor-pointer hover:stroke-current' : ''}
                    onClick={() => onEdgeClick?.(edge)}
                  />
                  
                  {/* Freccia per indicare direzione */}
                  <defs>
                    <marker
                      id={`arrow-${index}`}
                      viewBox="0 0 10 10"
                      refX="5"
                      refY="3"
                      markerWidth="6"
                      markerHeight="6"
                      orient="auto"
                    >
                      <path d="M0,0 L0,6 L9,3 z" fill={style.strokeColor} />
                    </marker>
                  </defs>
                  
                  <path
                    d={getEdgePath(edge)}
                    stroke="transparent"
                    strokeWidth={style.strokeWidth + 2}
                    fill="none"
                    markerEnd={`url(#arrow-${index})`}
                  />
                </g>
              );
            })}
          </g>

          {/* Render nodes */}
          <g className="nodes">
            {nodes.map(node => {
              const position = nodePositions[node.id];
              if (!position) return null;

              const domainStyle = getDomainStyle(node.category);
              const statusStyle = getStatusStyle(node.status);
              const nodeSize = getNodeSize(node);
              const isSelected = selectedNode === node.id;
              const isHovered = hoveredNode === node.id;
              const isCentral = node.id === centralNodeId;

              return (
                <g key={node.id} transform={`translate(${position.x}, ${position.y})`}>
                  {/* Pulse effect per nodi attivi */}
                  {statusStyle.pulseColor && (
                    <circle
                      r={nodeSize * 0.8}
                      fill={`url(#pulse-${node.status})`}
                      className="animate-pulse"
                    />
                  )}
                  
                  {/* Background circle */}
                  <circle
                    r={nodeSize * 0.6}
                    fill={domainStyle.bgColor}
                    stroke={statusStyle.borderColor}
                    strokeWidth={statusStyle.borderWidth}
                    className={`transition-all duration-200 ${
                      interactive ? 'cursor-pointer hover:stroke-4' : ''
                    } ${isSelected ? 'filter drop-shadow-lg' : ''}`}
                    onMouseEnter={() => setHoveredNode(node.id)}
                    onMouseLeave={() => setHoveredNode(null)}
                    onClick={() => handleNodeClick(node)}
                  />
                  
                  {/* Icon */}
                  <text
                    y="5"
                    textAnchor="middle"
                    fontSize={nodeSize * 0.4}
                    className="pointer-events-none select-none"
                  >
                    {domainStyle.icon}
                  </text>
                  
                  {/* Quality score indicator */}
                  {node.quality_score && (
                    <circle
                      cx={nodeSize * 0.4}
                      cy={-nodeSize * 0.4}
                      r="8"
                      fill={node.quality_score > 0.8 ? '#10B981' : node.quality_score > 0.6 ? '#F59E0B' : '#EF4444'}
                      className="text-white text-xs"
                    />
                  )}
                  
                  {/* Label */}
                  {showLabels && (isHovered || isCentral || isSelected) && (
                    <g>
                      <rect
                        x={-40}
                        y={nodeSize * 0.8}
                        width="80"
                        height="24"
                        rx="4"
                        fill="rgba(0,0,0,0.8)"
                        className="pointer-events-none"
                      />
                      <text
                        y={nodeSize * 0.8 + 16}
                        textAnchor="middle"
                        fill="white"
                        fontSize="10"
                        className="pointer-events-none select-none"
                      >
                        {node.name.length > 12 ? `${node.name.slice(0, 12)}...` : node.name}
                      </text>
                    </g>
                  )}
                </g>
              );
            })}
          </g>
        </svg>
      </div>

      {/* Legend */}
      <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
          <div>
            <div className="font-medium text-gray-700 mb-1">Impact Levels</div>
            <div className="space-y-1">
              {Object.entries(IMPACT_STYLES).map(([level, style]) => (
                <div key={level} className="flex items-center space-x-2">
                  <div 
                    className="w-4 h-0.5"
                    style={{ 
                      backgroundColor: style.strokeColor,
                      borderStyle: style.dashArray === 'none' ? 'solid' : 'dashed'
                    }}
                  ></div>
                  <span className="capitalize">{level}</span>
                </div>
              ))}
            </div>
          </div>
          
          <div>
            <div className="font-medium text-gray-700 mb-1">Domains</div>
            <div className="space-y-1">
              {Array.from(new Set(nodes.map(n => n.category))).slice(0, 4).map(category => {
                const style = getDomainStyle(category);
                return (
                  <div key={category} className="flex items-center space-x-2">
                    <span>{style.icon}</span>
                    <span className="capitalize">{category}</span>
                  </div>
                );
              })}
            </div>
          </div>
          
          <div>
            <div className="font-medium text-gray-700 mb-1">Node Status</div>
            <div className="space-y-1">
              {Object.entries(STATUS_STYLES).slice(0, 4).map(([status, style]) => (
                <div key={status} className="flex items-center space-x-2">
                  <div 
                    className="w-2 h-2 rounded-full border"
                    style={{ borderColor: style.borderColor, borderWidth: style.borderWidth }}
                  ></div>
                  <span className="capitalize">{status.replace('_', ' ')}</span>
                </div>
              ))}
            </div>
          </div>
          
          <div>
            <div className="font-medium text-gray-700 mb-1">Interactions</div>
            <div className="space-y-1 text-gray-600">
              <div>Click node: Details</div>
              <div>Click edge: Relationship</div>
              <div>Hover: Show label</div>
              <div>Center: Primary asset</div>
            </div>
          </div>
        </div>
      </div>

      {/* Selected Node Info */}
      {selectedNode && (
        <div className="px-4 py-3 border-t border-gray-200">
          {(() => {
            const node = nodes.find(n => n.id === selectedNode);
            if (!node) return null;
            
            const relatedEdges = edges ? edges.filter(e => e.source === selectedNode || e.target === selectedNode) : [];
            
            return (
              <div className="text-sm">
                <div className="font-medium text-gray-900 mb-2">{node.name}</div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-gray-600">
                  <div>Type: {node.type}</div>
                  <div>Category: {node.category}</div>
                  <div>Status: {node.status}</div>
                  <div>Connections: {relatedEdges.length}</div>
                </div>
                {node.quality_score && (
                  <div className="mt-2 text-xs text-gray-600">
                    Quality Score: {Math.round(node.quality_score * 100)}%
                  </div>
                )}
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
};