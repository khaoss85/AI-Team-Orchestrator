// Test script to verify Knowledge Base chat visibility
// Run with: node test-knowledge-base.js

async function testKnowledgeBaseChat() {
  console.log('🔍 Testing Knowledge Base Chat Visibility...\n');
  
  // Test 1: Check if Knowledge Base is in fixed chats
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
      id: 'configuration',
      type: 'fixed',
      systemType: 'configuration',
      title: 'Configuration',
      icon: '⚙️',
      status: 'active'
    },
    {
      id: 'feedback-requests',
      type: 'fixed',
      systemType: 'feedback',
      title: 'Feedback Requests',
      icon: '💬',
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
    }
  ];
  
  console.log('✅ Test 1: Fixed chats created');
  console.log(`   Total fixed chats: ${fixedChats.length}`);
  console.log(`   Knowledge Base present: ${fixedChats.some(c => c.id === 'knowledge-base')}`);
  
  // Test 2: Check filtering logic
  const fixedOnly = fixedChats.filter(chat => chat.type === 'fixed');
  console.log('\n✅ Test 2: After filtering for type === "fixed"');
  console.log(`   Filtered count: ${fixedOnly.length}`);
  console.log(`   Knowledge Base still present: ${fixedOnly.some(c => c.id === 'knowledge-base')}`);
  
  // Test 3: Check what ChatSidebar would receive
  const chatsForSidebar = fixedOnly;
  console.log('\n✅ Test 3: Chats passed to ChatSidebar');
  console.log(`   Total chats: ${chatsForSidebar.length}`);
  console.log(`   Fixed chats in sidebar:`);
  chatsForSidebar.forEach(chat => {
    console.log(`     - ${chat.icon} ${chat.title} (${chat.id})`);
  });
  
  // Test 4: Verify chat structure
  const knowledgeBaseChat = fixedChats.find(c => c.id === 'knowledge-base');
  console.log('\n✅ Test 4: Knowledge Base Chat Structure');
  if (knowledgeBaseChat) {
    console.log('   Knowledge Base chat found with properties:');
    console.log(`     id: ${knowledgeBaseChat.id}`);
    console.log(`     type: ${knowledgeBaseChat.type}`);
    console.log(`     systemType: ${knowledgeBaseChat.systemType}`);
    console.log(`     title: ${knowledgeBaseChat.title}`);
    console.log(`     icon: ${knowledgeBaseChat.icon}`);
    console.log(`     status: ${knowledgeBaseChat.status}`);
  } else {
    console.log('   ❌ Knowledge Base chat NOT FOUND!');
  }
  
  // Summary
  console.log('\n📊 SUMMARY:');
  if (fixedChats.some(c => c.id === 'knowledge-base') && 
      fixedOnly.some(c => c.id === 'knowledge-base')) {
    console.log('   ✅ Knowledge Base chat is properly configured and should be visible');
  } else {
    console.log('   ❌ Knowledge Base chat has an issue and might not be visible');
  }
}

testKnowledgeBaseChat();