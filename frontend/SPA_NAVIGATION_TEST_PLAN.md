# SPA Navigation Test Plan

## Automated Tests Completed ✅

### 1. **Architecture Validation**
- ✅ Removed duplicate goal page route (`/conversation/goal/[goalId]`)
- ✅ No remaining hardcoded references to old routes
- ✅ Single unified page handles all conversation views
- ✅ Hook initialization stability implemented
- ✅ URL parameter-based navigation in place

### 2. **Code Integration**  
- ✅ ConversationPage with stable hook initialization
- ✅ ChatSidebar pure state-based navigation  
- ✅ ConversationalWorkspace enhanced chat selection
- ✅ useConversationalWorkspace state preservation
- ✅ Next.js compilation successful

## Manual Testing Required

### 3. **Core Navigation Flow**
Test these scenarios in the browser:

#### Test 1: Basic Goal Switching
1. Navigate to `/projects/[id]/conversation` 
2. Click on a goal in sidebar
3. **Expected**: URL changes to `?goalId=xxx`, no page reload
4. **Verify**: Thinking data preserved, chat messages persist

#### Test 2: Direct Goal URL Access  
1. Navigate directly to `/projects/[id]/conversation?goalId=xxx`
2. **Expected**: Loads goal-specific view immediately
3. **Verify**: Correct goal is active, artifacts load correctly

#### Test 3: Browser History Navigation
1. Switch between several goals
2. Use browser back/forward buttons  
3. **Expected**: Correct goal restoration, no page reloads
4. **Verify**: State consistency maintained

#### Test 4: Tab Switching with Goals
1. Navigate to a goal
2. Switch to "thinking" tab
3. **Expected**: URL becomes `?goalId=xxx&tab=thinking`
4. Switch to different goal
5. **Expected**: Thinking tab preserved for new goal

#### Test 5: State Preservation
1. Navigate to goal, send messages, view thinking steps
2. Switch to different goal
3. Switch back to original goal  
4. **Expected**: All data preserved (messages, thinking, artifacts)

## Success Criteria

### 🎯 **Primary Goals**
- [ ] Zero page reloads when switching goals
- [ ] Thinking data (30 steps) visible and preserved  
- [ ] URL reflects current state correctly
- [ ] Browser back/forward works seamlessly

### 🚀 **Performance Targets**
- [ ] Goal switch response time < 100ms
- [ ] No network requests for cached data
- [ ] Smooth visual transitions
- [ ] No console errors during navigation

### 🔧 **Technical Validation**
- [ ] `useConversationalWorkspace` initializes once per workspace
- [ ] No duplicate API calls during navigation
- [ ] State consistency across all components
- [ ] URL synchronization without side effects

## Debugging Tools

### Browser Console Logging
Look for these log messages:
```
🎯 ChatSidebar: Chat selection: goal-xxx
🎯 ConversationalWorkspace: Processing chat selection  
🎯 SPA Navigation: Switching to goal chat
🔄 SPA Tab Navigation: /projects/xxx/conversation?goalId=xxx
```

### Network Tab Verification
- Should see NO new page requests during goal switches
- Only API calls for chat-specific data if needed
- WebSocket connections maintained

### React DevTools  
- Verify components don't unmount during navigation
- State preservation in useConversationalWorkspace hook
- No unnecessary re-renders on URL changes

## Known Issues to Verify Fixed

### ❌ **Before (Problematic Behavior)**
- Page reload flash when clicking goals
- Thinking steps disappear (30 steps lost)
- Chat history reloads from server
- URL inconsistencies between goals

### ✅ **After (Expected Behavior)**  
- Instant goal switching with preserved state
- Thinking steps remain visible across switches
- Chat messages cached and restored
- Clean URL structure with proper browser history

## Rollback Plan

If major issues are found:

1. **Immediate Fix**: Restore single goal page
   ```bash
   git revert [commit-hash]
   ```

2. **Incremental Approach**: 
   - Keep unified page but add fallback logic
   - Implement progressive enhancement
   - Add feature flag for SPA navigation

3. **Debug Approach**:
   - Add extensive logging to navigation flow
   - Implement error boundaries for navigation failures  
   - Monitor performance metrics

## Success Metrics

### User Experience  
- **Navigation Speed**: < 100ms goal switches
- **State Consistency**: 100% thinking data preservation  
- **URL Reliability**: Direct links work 100% of time
- **Browser Compatibility**: Works on Chrome, Firefox, Safari

### Technical Performance
- **Memory Usage**: No memory leaks during navigation
- **Bundle Size**: No increase in JavaScript bundle
- **SEO Impact**: URLs remain crawlable and bookmarkable
- **Accessibility**: Screen reader navigation works correctly

---

**Next Steps**: Manual testing in browser to validate the implementation works as designed.