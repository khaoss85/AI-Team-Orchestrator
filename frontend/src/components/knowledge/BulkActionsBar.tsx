import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Trash2, Tag, X, Lightbulb, Award, BookOpen, Flag } from 'lucide-react';

interface BulkActionsBarProps {
  selectedCount: number;
  onBulkDelete: () => void;
  onBulkCategorize: (ids: string[], category: string) => void;
  selectedIds: string[];
  onClearSelection: () => void;
  onBulkFlag?: (ids: string[], flag: 'verified' | 'important') => void;
}

const BulkActionsBar: React.FC<BulkActionsBarProps> = ({
  selectedCount,
  onBulkDelete,
  onBulkCategorize,
  selectedIds,
  onClearSelection,
  onBulkFlag,
}) => {
  const [bulkCategory, setBulkCategory] = useState<string>('');

  const handleBulkCategorize = () => {
    if (bulkCategory && selectedIds.length > 0) {
      onBulkCategorize(selectedIds, bulkCategory);
      setBulkCategory('');
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
        return <Tag className="w-4 h-4" />;
    }
  };

  return (
    <Card className="p-4 border-blue-200 bg-blue-50">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Badge variant="secondary" className="bg-blue-100 text-blue-800">
              {selectedCount} selected
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClearSelection}
              className="text-gray-500 hover:text-gray-700"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>

          <div className="h-6 w-px bg-gray-300" />

          {/* Bulk Categorize */}
          <div className="flex items-center space-x-2">
            <Select value={bulkCategory} onValueChange={setBulkCategory}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Change category...">
                  {bulkCategory && (
                    <div className="flex items-center space-x-2">
                      {getCategoryIcon(bulkCategory)}
                      <span className="capitalize">
                        {bulkCategory.replace('_', ' ')}
                      </span>
                    </div>
                  )}
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
            <Button
              variant="outline"
              size="sm"
              onClick={handleBulkCategorize}
              disabled={!bulkCategory}
            >
              <Tag className="w-4 h-4 mr-1" />
              Categorize
            </Button>
          </div>

          <div className="h-6 w-px bg-gray-300" />

          {/* Bulk Flag Actions */}
          <div className="flex items-center space-x-1">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onBulkFlag?.(selectedIds, 'verified')}
              className="text-green-600 border-green-200 hover:bg-green-50"
            >
              <Flag className="w-4 h-4 mr-1" />
              Mark Verified
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onBulkFlag?.(selectedIds, 'important')}
              className="text-yellow-600 border-yellow-200 hover:bg-yellow-50"
            >
              <Flag className="w-4 h-4 mr-1" />
              Mark Important
            </Button>
          </div>
        </div>

        {/* Bulk Delete */}
        <Dialog>
          <DialogTrigger asChild>
            <button
              className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors border border-input bg-background hover:bg-accent hover:text-accent-foreground h-9 px-3 text-red-600 border-red-200 hover:bg-red-50"
            >
              <Trash2 className="w-4 h-4 mr-1" />
              Delete Selected
            </button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Multiple Insights</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete {selectedCount} selected insight{selectedCount !== 1 ? 's' : ''}? 
                This action can be undone within 10 seconds.
              </DialogDescription>
            </DialogHeader>
            <div className="flex justify-end gap-2 mt-4">
              <Button variant="outline" onClick={() => {}}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={onBulkDelete}>
                Delete {selectedCount} Insight{selectedCount !== 1 ? 's' : ''}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Quick Help */}
      <div className="mt-3 pt-3 border-t border-blue-200">
        <div className="text-xs text-blue-700">
          💡 <strong>Quick actions:</strong> Select insights by clicking the checkboxes, then use the tools above to categorize, flag, or delete multiple items at once.
        </div>
      </div>
    </Card>
  );
};

export { BulkActionsBar };