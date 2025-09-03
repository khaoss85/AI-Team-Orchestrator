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
import { KnowledgeInsight } from '@/types';


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
    category: 'general',
    domain_type: 'general',
    // Note: tags field removed as API doesn't support it
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
          category: insight.category || 'general',
          domain_type: insight.domain_type || 'general',
        });
      } else {
        // Creating new insight
        setFormData({
          title: '',
          content: '',
          category: 'general',
          domain_type: 'general',
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

  // Tag functionality removed as API doesn't support tags

  const applyAiSuggestion = (type: 'category') => {
    if (type === 'category' && aiSuggestions.suggestedCategory) {
      setFormData(prev => ({
        ...prev,
        category: aiSuggestions.suggestedCategory as any,
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
      domain_type: formData.domain_type,
      is_user_created: true,
    };

    onSave(saveData);
  };

  const getCategoryIcon = (category: string) => {
    return <Lightbulb className="w-4 h-4" />;
  };

  const getCategoryColor = (category: string) => {
    return 'bg-blue-50 text-blue-700 border-blue-200';
  };

  return (
    <Dialog open={open} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <span>{insight ? 'Edit Insight' : 'Create New Insight'}</span>
            {!insight?.is_user_created && (
              <Badge variant="secondary" className="text-xs">
                🤖 System Generated
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

                  {/* Tags suggestions removed as API doesn't support tags */}
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
                <SelectItem value="general">
                  <div className="flex items-center space-x-2">
                    <Lightbulb className="w-4 h-4" />
                    <span>General</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Tags section removed as API doesn't support tags */}

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