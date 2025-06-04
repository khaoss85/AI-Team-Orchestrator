import assert from 'node:assert/strict'
import { test } from 'node:test'


test('sample addition', () => {
  assert.equal(1 + 1, 2)
})

test('feedback API call includes task id', async () => {
  let received = null
  const api = {
    monitoring: {
      submitDeliverableFeedback: async (_id, data) => {
        received = data
      }
    }
  }

  const handleQuickFeedback = async (type, taskId) => {
    await api.monitoring.submitDeliverableFeedback('ws1', {
      feedback_type: type,
      message: '',
      priority: 'medium',
      specific_tasks: [taskId]
    })
  }

  await handleQuickFeedback('approve', 'task123')

  assert.deepEqual(received, {
    feedback_type: 'approve',
    message: '',
    priority: 'medium',
    specific_tasks: ['task123']
  })
})
