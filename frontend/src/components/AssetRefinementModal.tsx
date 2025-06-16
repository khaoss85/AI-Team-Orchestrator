'use client';

import React, { useState } from 'react';

interface AssetRefinementModalProps {
  isOpen: boolean;
  assetName: string;
  onClose: () => void;
  onSubmit: (feedback: string) => void;
  isLoading?: boolean;
  hasSourceTask?: boolean;
}

const AssetRefinementModal: React.FC<AssetRefinementModalProps> = ({
  isOpen,
  assetName,
  onClose,
  onSubmit,
  isLoading = false,
  hasSourceTask = true
}) => {
  const [feedback, setFeedback] = useState('');
  
  // Draft persistence
  const draftKey = `asset-refinement-draft-${assetName}`;
  
  // Load draft when modal opens
  React.useEffect(() => {
    if (isOpen) {
      const savedDraft = localStorage.getItem(draftKey);
      if (savedDraft) {
        setFeedback(savedDraft);
      }
    }
  }, [isOpen, draftKey]);
  
  // Save draft as user types
  React.useEffect(() => {
    if (feedback.trim()) {
      localStorage.setItem(draftKey, feedback);
    }
  }, [feedback, draftKey]);

  const handleSubmit = () => {
    if (feedback.trim()) {
      onSubmit(feedback.trim());
      // Clear draft from localStorage after successful submission
      localStorage.removeItem(draftKey);
      setFeedback(''); // Reset form
    }
  };

  const handleCancel = () => {
    // Clear draft when explicitly canceled
    localStorage.removeItem(draftKey);
    setFeedback(''); // Reset form
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-500 to-red-500 p-6 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="text-3xl">💬</div>
              <div>
                <h2 className="text-xl font-bold">Request Asset Changes</h2>
                <p className="opacity-90 text-sm">Improve "{assetName}"</p>
              </div>
            </div>
            {!isLoading && (
              <button 
                onClick={handleCancel}
                className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              What would you like to improve or change?
            </label>
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              disabled={isLoading}
              placeholder="Describe the improvements you'd like to see. Be as specific as possible. For example:&#10;&#10;• Add more detailed information&#10;• Include additional data fields&#10;• Improve content quality&#10;• Expand the scope&#10;• Change the format or structure"
              className="w-full h-40 px-4 py-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all disabled:bg-gray-100 disabled:cursor-not-allowed"
              rows={8}
            />
            <div className="flex justify-between items-center mt-2">
              <div className="text-xs text-gray-500">
                Be specific to get better results
              </div>
              <div className="text-xs text-gray-400">
                {feedback.length}/1000
              </div>
            </div>
          </div>

          {/* Warning for missing source task */}
          {!hasSourceTask && (
            <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
              <h4 className="font-medium text-yellow-800 mb-2">⚠️ Limited Enhancement Mode</h4>
              <p className="text-sm text-yellow-700">
                This asset doesn't have complete tracking information. Enhancement will create a new improved version but may not be perfectly linked to the original.
              </p>
            </div>
          )}

          {/* Examples/Tips */}
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <h4 className="font-medium text-blue-800 mb-2">💡 Tips for better results:</h4>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• Be specific about what data or information to add</li>
              <li>• Mention quality improvements you want to see</li>
              <li>• Specify if you want more items/entries</li>
              <li>• Describe the format or structure changes needed</li>
            </ul>
          </div>

          {isLoading && (
            <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
              <div className="flex items-center space-x-3">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-orange-500"></div>
                <div>
                  <div className="font-medium text-yellow-800">Processing your request...</div>
                  <div className="text-sm text-yellow-600">The AI team is working on your enhancement</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 p-6 bg-gray-50">
          <div className="flex space-x-3">
            <button
              onClick={handleCancel}
              disabled={isLoading}
              className="flex-1 px-4 py-3 text-gray-700 bg-white border border-gray-300 rounded-lg font-medium hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={isLoading || !feedback.trim()}
              className="flex-1 px-4 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg font-medium hover:from-orange-600 hover:to-red-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <span>🚀</span>
                  <span>Submit Request</span>
                </>
              )}
            </button>
          </div>
          
          <div className="mt-3 text-center">
            <div className="text-xs text-gray-500">
              ⏱️ Expected processing time: 5-10 minutes
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssetRefinementModal;