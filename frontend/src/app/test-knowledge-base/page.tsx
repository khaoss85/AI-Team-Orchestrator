'use client'

import { useState, useEffect } from 'react'

export default function TestKnowledgeBasePage() {
  const [workspaces, setWorkspaces] = useState<any[]>([])
  const [selectedWorkspace, setSelectedWorkspace] = useState<string>('')
  const [chats, setChats] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetch('http://localhost:8000/api/workspaces/')
      .then(res => res.json())
      .then(data => setWorkspaces(data))
      .catch(err => console.error('Failed to fetch workspaces:', err))
  }, [])

  const testWorkspace = async (workspaceId: string) => {
    setLoading(true)
    setSelectedWorkspace(workspaceId)
    
    try {
      // Simulate the same fixed chats creation as in useConversationalWorkspace
      const fixedChats = [
        {
          id: 'team-management',
          type: 'fixed',
          systemType: 'team',
          title: 'Team Management',
          icon: '👥',
          status: 'active'
        },
        {
          id: 'project-configuration',
          type: 'fixed',
          systemType: 'configuration',
          title: 'Project Configuration',
          icon: '⚙️',
          status: 'active'
        },
        {
          id: 'knowledge-base',
          type: 'fixed',
          systemType: 'knowledge',
          title: 'Knowledge Base',
          icon: '📚',
          status: 'active'
        },
        {
          id: 'available-tools',
          type: 'fixed',
          systemType: 'tools',
          title: 'Available Tools',
          icon: '🛠️',
          status: 'active'
        },
        {
          id: 'feedback-requests',
          type: 'fixed',
          systemType: 'feedback',
          title: 'Feedback Requests',
          icon: '💬',
          status: 'active'
        }
      ]
      
      setChats(fixedChats)
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Knowledge Base Chat Visibility Test</h1>
      
      <div className="mb-6">
        <h2 className="text-lg font-semibold mb-2">Select a Workspace:</h2>
        <div className="space-y-2">
          {workspaces.map(ws => (
            <button
              key={ws.id}
              onClick={() => testWorkspace(ws.id)}
              className={`block w-full text-left p-3 rounded border ${
                selectedWorkspace === ws.id ? 'bg-blue-50 border-blue-500' : 'hover:bg-gray-50'
              }`}
            >
              <div className="font-medium">{ws.name}</div>
              <div className="text-sm text-gray-500">{ws.id}</div>
            </button>
          ))}
        </div>
      </div>

      {loading && <div>Loading...</div>}

      {chats.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-2">Fixed Chats Created:</h2>
          <div className="bg-gray-50 p-4 rounded">
            <pre className="text-sm">{JSON.stringify(chats, null, 2)}</pre>
          </div>
          
          <h3 className="text-lg font-semibold mt-4 mb-2">Knowledge Base Chat Status:</h3>
          {chats.find(c => c.id === 'knowledge-base') ? (
            <div className="bg-green-50 p-4 rounded border border-green-500">
              <p className="text-green-800 font-semibold">✅ Knowledge Base chat IS present in the chats array</p>
              <div className="mt-2">
                <p>ID: {chats.find(c => c.id === 'knowledge-base')?.id}</p>
                <p>Type: {chats.find(c => c.id === 'knowledge-base')?.type}</p>
                <p>System Type: {chats.find(c => c.id === 'knowledge-base')?.systemType}</p>
                <p>Title: {chats.find(c => c.id === 'knowledge-base')?.title}</p>
                <p>Icon: {chats.find(c => c.id === 'knowledge-base')?.icon}</p>
                <p>Status: {chats.find(c => c.id === 'knowledge-base')?.status}</p>
              </div>
            </div>
          ) : (
            <div className="bg-red-50 p-4 rounded border border-red-500">
              <p className="text-red-800 font-semibold">❌ Knowledge Base chat is NOT in the chats array!</p>
            </div>
          )}
          
          <h3 className="text-lg font-semibold mt-4 mb-2">All Fixed Chats (type === 'fixed'):</h3>
          <div className="space-y-2">
            {chats.filter(c => c.type === 'fixed').map(chat => (
              <div key={chat.id} className="p-3 bg-white border rounded">
                <div className="flex items-center space-x-2">
                  <span className="text-2xl">{chat.icon}</span>
                  <div>
                    <div className="font-medium">{chat.title}</div>
                    <div className="text-xs text-gray-500">
                      ID: {chat.id} | Type: {chat.type} | SystemType: {chat.systemType}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}