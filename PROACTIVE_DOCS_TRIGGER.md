# Proactive Documentation Trigger System

> Sistema per rilevare automaticamente modifiche che richiedono aggiornamento della memoria di Claude Code

## 🤖 Trigger Conditions (Auto-Activation)

### **High-Priority Triggers** (Score 80+)
- ✅ **NEW_COMPONENT_CREATED**: Nuovo componente React/UI (come MarkdownRenderer)
- ✅ **PERFORMANCE_BREAKTHROUGH**: Miglioramenti >50% performance (90s→3-5s)
- ✅ **UX_ENHANCEMENT**: Soluzioni per "not user-friendly" problems
- ✅ **API_PATTERN_ESTABLISHED**: Nuovi pattern API endpoint
- ✅ **DATABASE_SCHEMA_CHANGES**: Constraint, migrations, data fixes

### **Medium-Priority Triggers** (Score 60-79)
- 🔶 **BUG_PATTERN_SOLVED**: Fix per bug ricorrenti con prevention
- 🔶 **CONFIG_OPTIMIZATION**: Environment vars, deployment improvements
- 🔶 **INTEGRATION_PATTERNS**: Sub-agent usage patterns
- 🔶 **TOOL_ENHANCEMENT**: Nuovi tools o workflow improvements

### **Low-Priority Triggers** (Score 40-59)
- 🟡 **CODE_REFACTORING**: Miglioramenti architetturali minori
- 🟡 **DOCUMENTATION_UPDATES**: Aggiornamenti README/guides
- 🟡 **TESTING_PATTERNS**: Nuovi test patterns o utilities

## 🎯 Current Session Analysis

### **Implemented Enhancement: MarkdownRenderer**
**Score: 85 (HIGH-PRIORITY)**

**Trigger Conditions Met:**
- ✅ NEW_COMPONENT_CREATED: `/components/conversational/MarkdownRenderer.tsx`
- ✅ UX_ENHANCEMENT: Risolve "content not user-friendly" per tabelle markdown
- ✅ REUSABLE_PATTERN: Template per content rendering in altri componenti

**Auto-Suggestion:**
```
🤖 DOCS-SCRIBE PROACTIVE ALERT:
New memory-worthy pattern detected! This UX enhancement should be documented 
in TROUBLESHOOTING_MEMORY.md to prevent future re-implementation.

Pattern Type: UX_IMPROVEMENT
Impact Level: HIGH (Score: 85)
Reusability: CROSS-COMPONENT

Suggested Action: Add Section 6 to TROUBLESHOOTING_MEMORY.md
Template: UX_IMPROVEMENT (auto-populated ready)
```

## 🔄 Activation Commands

### **For Users:**
```bash
# Manual trigger della documentazione proattiva
/docs-scribe-suggest

# Accetta suggestion
/docs-accept-memory-update

# Skip suggestion per questa sessione
/docs-skip-session
```

### **For Claude Code:**
```typescript
// Auto-trigger dopo commit significativi
if (commitScore >= 60) {
  await docs_scribe.suggestMemoryUpdate({
    changes: commitChanges,
    score: commitScore,
    template: detectTemplate(commitChanges)
  })
}
```

## 📋 Success Metrics

- **Prevention Rate**: % di problemi risolti che non vengono ri-implementati
- **Coverage Rate**: % di significant changes documentati
- **Usage Rate**: % di suggestions accettate dagli utenti
- **Time Savings**: Tempo risparmiato non ri-risolvendo problemi esistenti

---
*Sistema attivato: 2025-08-28*
*Sessione corrente: MarkdownRenderer UX Enhancement (Score: 85)*