import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from '@/components/ui/dialog';
import { Plus, Edit3, Trash2, Flag, Archive, RotateCcw, Lightbulb, Award, BookOpen } from 'lucide-react';
import { InsightEditorModal } from './InsightEditorModal';
import { BulkActionsBar } from './BulkActionsBar';

interface KnowledgeInsight {
  id: string;
  title: string;
  content: string;
  category: 'insight' | 'best_practice' | 'learning';
  source: 'ai' | 'user';
  confidence?: number;
  ai_reasoning?: string;
  flags: {
    verified: boolean;
    important: boolean;
    outdated: boolean;
  };
  created_at: string;
  created_by?: string;
  modified_at?: string;
  modified_by?: string;
  tags: string[];
}

interface KnowledgeInsightManagerProps {
  workspaceId: string;
  currentUserId: string;
}

const KnowledgeInsightManager: React.FC<KnowledgeInsightManagerProps> = ({
  workspaceId,
  currentUserId
}) => {
  const [insights, setInsights] = useState<KnowledgeInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedInsights, setSelectedInsights] = useState<Set<string>>(new Set());
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingInsight, setEditingInsight] = useState<KnowledgeInsight | null>(null);
  const [activeTab, setActiveTab] = useState<'all' | 'insights' | 'best_practices' | 'learnings'>('all');
  const [lastDeletedInsight, setLastDeletedInsight] = useState<string | null>(null);

  // Load insights from API
  useEffect(() => {
    fetchInsights();
  }, [workspaceId]);

  const fetchInsights = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/user-insights/${workspaceId}/insights`, {
        headers: {
          'X-User-Id': currentUserId,
        },
      });
      const data = await response.json();
      setInsights(data.insights || []);
    } catch (error) {
      console.error('Failed to fetch insights:', error);
    } finally {
      setLoading(false);
    }
  };

  const createInsight = async (insightData: Partial<KnowledgeInsight>) => {
    try {
      const response = await fetch(`/api/user-insights/${workspaceId}/insights`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': currentUserId,
        },
        body: JSON.stringify(insightData),
      });
      
      if (response.ok) {
        await fetchInsights();
        setEditorOpen(false);
        setEditingInsight(null);
      }
    } catch (error) {
      console.error('Failed to create insight:', error);
    }
  };

  const updateInsight = async (id: string, updates: Partial<KnowledgeInsight>) => {
    try {
      const response = await fetch(`/api/user-insights/insights/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': currentUserId,
        },
        body: JSON.stringify(updates),
      });
      
      if (response.ok) {
        await fetchInsights();
        setEditorOpen(false);
        setEditingInsight(null);
      }
    } catch (error) {
      console.error('Failed to update insight:', error);
    }
  };

  const deleteInsight = async (id: string) => {
    try {
      const response = await fetch(`/api/user-insights/insights/${id}`, {
        method: 'DELETE',
        headers: {
          'X-User-Id': currentUserId,
        },
      });
      
      if (response.ok) {
        setLastDeletedInsight(id);
        await fetchInsights();
        
        // Auto-hide undo button after 10 seconds
        setTimeout(() => setLastDeletedInsight(null), 10000);
      }
    } catch (error) {
      console.error('Failed to delete insight:', error);
    }
  };

  const undoLastDelete = async () => {
    if (!lastDeletedInsight) return;
    
    try {
      const response = await fetch(`/api/user-insights/insights/${lastDeletedInsight}/restore`, {
        method: 'POST',
        headers: {
          'X-User-Id': currentUserId,
        },
      });
      
      if (response.ok) {
        await fetchInsights();
        setLastDeletedInsight(null);
      }
    } catch (error) {
      console.error('Failed to undo delete:', error);
    }
  };

  const toggleFlag = async (id: string, flagType: 'verified' | 'important' | 'outdated') => {
    const insight = insights.find(i => i.id === id);
    if (!insight) return;

    try {
      const response = await fetch(`/api/user-insights/insights/${id}/flags`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': currentUserId,
        },
        body: JSON.stringify({
          flag_type: flagType,
          flag_value: !insight.flags[flagType],
        }),
      });
      
      if (response.ok) {
        await fetchInsights();
      }
    } catch (error) {
      console.error('Failed to toggle flag:', error);
    }
  };

  const bulkDelete = async (ids: string[]) => {
    try {
      const response = await fetch(`/api/user-insights/${workspaceId}/insights/bulk`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': currentUserId,
        },
        body: JSON.stringify({ insight_ids: ids }),
      });
      
      if (response.ok) {
        await fetchInsights();
        setSelectedInsights(new Set());
      }
    } catch (error) {
      console.error('Failed to bulk delete:', error);
    }
  };

  const bulkCategorize = async (ids: string[], category: string) => {
    try {
      const response = await fetch(`/api/user-insights/${workspaceId}/insights/bulk`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': currentUserId,
        },
        body: JSON.stringify({ 
          insight_ids: ids,
          updates: { category }
        }),
      });
      
      if (response.ok) {
        await fetchInsights();
        setSelectedInsights(new Set());
      }
    } catch (error) {
      console.error('Failed to bulk categorize:', error);
    }
  };

  const handleEdit = (insight: KnowledgeInsight) => {
    setEditingInsight(insight);
    setEditorOpen(true);
  };

  const handleCreate = () => {
    setEditingInsight(null);
    setEditorOpen(true);
  };

  const toggleSelection = (id: string) => {
    const newSelected = new Set(selectedInsights);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedInsights(newSelected);
  };

  const getFilteredInsights = () => {
    switch (activeTab) {
      case 'insights':
        return insights.filter(i => i.category === 'insight');
      case 'best_practices':
        return insights.filter(i => i.category === 'best_practice');
      case 'learnings':
        return insights.filter(i => i.category === 'learning');
      default:
        return insights;
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'insight':
        return <Lightbulb className="w-4 h-4" />;
      case 'best_practice':
        return <Award className="w-4 h-4" />;
      case 'learning':
        return <BookOpen className="w-4 h-4" />;
      default:
        return <Lightbulb className="w-4 h-4" />;
    }
  };

  const InsightCard = ({ insight }: { insight: KnowledgeInsight }) => (
    <Card key={insight.id} className={`mb-4 ${selectedInsights.has(insight.id) ? 'ring-2 ring-blue-500' : ''}`}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-2 flex-1">
            <input
              type="checkbox"
              checked={selectedInsights.has(insight.id)}
              onChange={() => toggleSelection(insight.id)}
              className="rounded"
            />
            {getCategoryIcon(insight.category)}
            <CardTitle className="text-sm font-medium">{insight.title}</CardTitle>
            <Badge variant={insight.source === 'ai' ? 'secondary' : 'default'} className="text-xs">
              {insight.source === 'ai' ? '🤖 AI' : '👤 User'}
            </Badge>
          </div>
          <div className="flex items-center space-x-1">
            {insight.flags.verified && (
              <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">
                ✓ Verified
              </Badge>
            )}
            {insight.flags.important && (
              <Badge variant="outline" className="text-xs bg-yellow-50 text-yellow-700 border-yellow-200">
                ★ Important
              </Badge>
            )}
            {insight.flags.outdated && (
              <Badge variant="outline" className="text-xs bg-gray-50 text-gray-700 border-gray-200">
                ⚠ Outdated
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-gray-600 mb-3">{insight.content}</p>
        
        {insight.source === 'ai' && insight.confidence && (
          <div className="text-xs text-gray-500 mb-2">
            AI Confidence: {Math.round(insight.confidence * 100)}%
            {insight.ai_reasoning && (
              <span className="ml-2">• {insight.ai_reasoning}</span>
            )}
          </div>
        )}
        
        {insight.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {insight.tags.map((tag, index) => (
              <Badge key={index} variant="outline" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        )}
        
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>
            Created: {new Date(insight.created_at).toLocaleDateString()}
            {insight.created_by && ` by ${insight.created_by}`}
          </span>
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => toggleFlag(insight.id, 'verified')}
              className={insight.flags.verified ? 'text-green-600' : ''}
            >
              ✓
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => toggleFlag(insight.id, 'important')}
              className={insight.flags.important ? 'text-yellow-600' : ''}
            >
              <Flag className="w-3 h-3" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleEdit(insight)}
            >
              <Edit3 className="w-3 h-3" />
            </Button>
            <Dialog>
              <DialogTrigger asChild>
                <Button variant="ghost" size="sm" className="text-red-600">
                  <Trash2 className="w-3 h-3" />
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Delete Insight</DialogTitle>
                  <DialogDescription>
                    Are you sure you want to delete "{insight.title}"? You can undo this action within 10 seconds.
                  </DialogDescription>
                </DialogHeader>
                <div className="flex justify-end gap-2 mt-4">
                  <Button variant="outline" onClick={() => {}}>
                    Cancel
                  </Button>
                  <Button variant="destructive" onClick={() => deleteInsight(insight.id)}>
                    Delete
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  if (loading) {
    return <div className="flex justify-center p-8">Loading insights...</div>;
  }

  return (
    <div className="space-y-4">
      {/* Header with Actions */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Knowledge Insights</h2>
        <div className="flex items-center space-x-2">
          {lastDeletedInsight && (
            <Button
              variant="outline"
              size="sm"
              onClick={undoLastDelete}
              className="text-blue-600 border-blue-200"
            >
              <RotateCcw className="w-4 h-4 mr-1" />
              Undo Delete
            </Button>
          )}
          <Button onClick={handleCreate}>
            <Plus className="w-4 h-4 mr-1" />
            Add Insight
          </Button>
        </div>
      </div>

      {/* Bulk Actions Bar */}
      {selectedInsights.size > 0 && (
        <BulkActionsBar
          selectedCount={selectedInsights.size}
          onBulkDelete={() => bulkDelete(Array.from(selectedInsights))}
          onBulkCategorize={bulkCategorize}
          selectedIds={Array.from(selectedInsights)}
          onClearSelection={() => setSelectedInsights(new Set())}
        />
      )}

      {/* Category Tabs */}
      <Tabs value={activeTab} onValueChange={(value: any) => setActiveTab(value)}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="all">All ({insights.length})</TabsTrigger>
          <TabsTrigger value="insights">
            <Lightbulb className="w-4 h-4 mr-1" />
            Insights ({insights.filter(i => i.category === 'insight').length})
          </TabsTrigger>
          <TabsTrigger value="best_practices">
            <Award className="w-4 h-4 mr-1" />
            Best Practices ({insights.filter(i => i.category === 'best_practice').length})
          </TabsTrigger>
          <TabsTrigger value="learnings">
            <BookOpen className="w-4 h-4 mr-1" />
            Learnings ({insights.filter(i => i.category === 'learning').length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="space-y-4">
          {getFilteredInsights().length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-2">🤔</div>
              <p>No insights found in this category</p>
              <Button variant="outline" onClick={handleCreate} className="mt-4">
                <Plus className="w-4 h-4 mr-1" />
                Create your first insight
              </Button>
            </div>
          ) : (
            getFilteredInsights().map(insight => (
              <InsightCard key={insight.id} insight={insight} />
            ))
          )}
        </TabsContent>
      </Tabs>

      {/* Editor Modal */}
      <InsightEditorModal
        open={editorOpen}
        onClose={() => {
          setEditorOpen(false);
          setEditingInsight(null);
        }}
        insight={editingInsight}
        onSave={editingInsight ? 
          (updates) => updateInsight(editingInsight.id, updates) :
          (data) => createInsight(data)
        }
      />
    </div>
  );
};

export default KnowledgeInsightManager;