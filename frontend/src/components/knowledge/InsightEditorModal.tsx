import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { X, Lightbulb, Award, BookOpen, Tag, Sparkles } from 'lucide-react';

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

interface InsightEditorModalProps {
  open: boolean;
  onClose: () => void;
  insight?: KnowledgeInsight | null;
  onSave: (data: Partial<KnowledgeInsight>) => void;
}

const InsightEditorModal: React.FC<InsightEditorModalProps> = ({
  open,
  onClose,
  insight,
  onSave,
}) => {
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    category: 'insight' as 'insight' | 'best_practice' | 'learning',
    tags: [] as string[],
    newTag: '',
  });

  const [aiSuggestions, setAiSuggestions] = useState<{
    suggestedCategory?: string;
    suggestedTags?: string[];
    confidence?: number;
  }>({});

  const [loading, setLoading] = useState(false);
  const [showAiSuggestions, setShowAiSuggestions] = useState(false);

  // Reset form when modal opens/closes or insight changes
  useEffect(() => {
    if (open) {
      if (insight) {
        // Editing existing insight
        setFormData({
          title: insight.title || '',
          content: insight.content || '',
          category: insight.category || 'insight',
          tags: insight.tags || [],
          newTag: '',
        });
      } else {
        // Creating new insight
        setFormData({
          title: '',
          content: '',
          category: 'insight',
          tags: [],
          newTag: '',
        });
      }
      setAiSuggestions({});
      setShowAiSuggestions(false);
    }
  }, [open, insight]);

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));

    // Trigger AI suggestions when content changes
    if (field === 'content' && value.length > 50 && !insight) {
      debouncedGetAiSuggestions(formData.title, value);
    }
  };

  const debouncedGetAiSuggestions = debounce(async (title: string, content: string) => {
    if (!title || !content) return;

    setLoading(true);
    try {
      // Call AI categorization service for suggestions
      const response = await fetch('/api/ai/categorize-insight', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title,
          content,
        }),
      });

      if (response.ok) {
        const suggestions = await response.json();
        setAiSuggestions(suggestions);
        setShowAiSuggestions(true);
      }
    } catch (error) {
      console.error('Failed to get AI suggestions:', error);
    } finally {
      setLoading(false);
    }
  }, 500);

  const handleAddTag = () => {
    if (formData.newTag.trim() && !formData.tags.includes(formData.newTag.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, prev.newTag.trim()],
        newTag: '',
      }));
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove),
    }));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.currentTarget === e.target) {
      e.preventDefault();
      handleAddTag();
    }
  };

  const applyAiSuggestion = (type: 'category' | 'tags') => {
    if (type === 'category' && aiSuggestions.suggestedCategory) {
      setFormData(prev => ({
        ...prev,
        category: aiSuggestions.suggestedCategory as any,
      }));
    } else if (type === 'tags' && aiSuggestions.suggestedTags) {
      setFormData(prev => ({
        ...prev,
        tags: [...new Set([...prev.tags, ...aiSuggestions.suggestedTags!])],
      }));
    }
  };

  const handleSave = () => {
    if (!formData.title.trim() || !formData.content.trim()) {
      return;
    }

    const saveData: Partial<KnowledgeInsight> = {
      title: formData.title.trim(),
      content: formData.content.trim(),
      category: formData.category,
      tags: formData.tags,
      source: 'user',
    };

    onSave(saveData);
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

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'insight':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'best_practice':
        return 'bg-green-50 text-green-700 border-green-200';
      case 'learning':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  return (
    <Dialog open={open} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <span>{insight ? 'Edit Insight' : 'Create New Insight'}</span>
            {insight?.source === 'ai' && (
              <Badge variant="secondary" className="text-xs">
                🤖 AI Generated
              </Badge>
            )}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title">Title *</Label>
            <Input
              id="title"
              value={formData.title}
              onChange={(e) => handleInputChange('title', e.target.value)}
              placeholder="Enter insight title..."
              className="w-full"
            />
          </div>

          {/* Content */}
          <div className="space-y-2">
            <Label htmlFor="content">Content *</Label>
            <Textarea
              id="content"
              value={formData.content}
              onChange={(e) => handleInputChange('content', e.target.value)}
              placeholder="Describe your insight in detail..."
              className="w-full min-h-[120px]"
            />
            {loading && (
              <div className="flex items-center text-sm text-gray-500">
                <Sparkles className="w-4 h-4 mr-1 animate-spin" />
                Getting AI suggestions...
              </div>
            )}
          </div>

          {/* AI Suggestions */}
          {showAiSuggestions && aiSuggestions.suggestedCategory && (
            <Card className="border-blue-200 bg-blue-50">
              <CardContent className="p-4">
                <div className="flex items-center space-x-2 mb-3">
                  <Sparkles className="w-4 h-4 text-blue-600" />
                  <span className="font-medium text-blue-800">AI Suggestions</span>
                  {aiSuggestions.confidence && (
                    <Badge variant="outline" className="text-xs">
                      {Math.round(aiSuggestions.confidence * 100)}% confidence
                    </Badge>
                  )}
                </div>
                
                <div className="space-y-3">
                  {/* Suggested Category */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-blue-700">Suggested category:</span>
                      <Badge className={getCategoryColor(aiSuggestions.suggestedCategory)}>
                        {getCategoryIcon(aiSuggestions.suggestedCategory)}
                        <span className="ml-1 capitalize">
                          {aiSuggestions.suggestedCategory.replace('_', ' ')}
                        </span>
                      </Badge>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => applyAiSuggestion('category')}
                    >
                      Apply
                    </Button>
                  </div>

                  {/* Suggested Tags */}
                  {aiSuggestions.suggestedTags && aiSuggestions.suggestedTags.length > 0 && (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm text-blue-700">Suggested tags:</span>
                        <div className="flex flex-wrap gap-1">
                          {aiSuggestions.suggestedTags.slice(0, 4).map((tag, index) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => applyAiSuggestion('tags')}
                      >
                        Add All
                      </Button>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Category Selection */}
          <div className="space-y-2">
            <Label htmlFor="category">Category</Label>
            <Select
              value={formData.category}
              onValueChange={(value: any) => handleInputChange('category', value)}
            >
              <SelectTrigger>
                <SelectValue>
                  <div className="flex items-center space-x-2">
                    {getCategoryIcon(formData.category)}
                    <span className="capitalize">
                      {formData.category.replace('_', ' ')}
                    </span>
                  </div>
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="insight">
                  <div className="flex items-center space-x-2">
                    <Lightbulb className="w-4 h-4" />
                    <span>Insight</span>
                  </div>
                </SelectItem>
                <SelectItem value="best_practice">
                  <div className="flex items-center space-x-2">
                    <Award className="w-4 h-4" />
                    <span>Best Practice</span>
                  </div>
                </SelectItem>
                <SelectItem value="learning">
                  <div className="flex items-center space-x-2">
                    <BookOpen className="w-4 h-4" />
                    <span>Learning</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Tags */}
          <div className="space-y-2">
            <Label>Tags</Label>
            <div className="flex space-x-2">
              <Input
                value={formData.newTag}
                onChange={(e) => setFormData(prev => ({ ...prev, newTag: e.target.value }))}
                onKeyPress={handleKeyPress}
                placeholder="Add a tag..."
                className="flex-1"
              />
              <Button
                type="button"
                variant="outline"
                onClick={handleAddTag}
                disabled={!formData.newTag.trim()}
              >
                <Tag className="w-4 h-4" />
              </Button>
            </div>
            
            {formData.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {formData.tags.map((tag, index) => (
                  <Badge
                    key={index}
                    variant="secondary"
                    className="flex items-center space-x-1"
                  >
                    <span>{tag}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveTag(tag)}
                      className="ml-1 hover:text-red-600"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-2 pt-4 border-t">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={!formData.title.trim() || !formData.content.trim()}
            >
              {insight ? 'Update Insight' : 'Create Insight'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Utility function for debouncing
function debounce<T extends (...args: any[]) => any>(func: T, wait: number): T {
  let timeout: NodeJS.Timeout;
  return ((...args: any[]) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(null, args), wait);
  }) as T;
}

export { InsightEditorModal };