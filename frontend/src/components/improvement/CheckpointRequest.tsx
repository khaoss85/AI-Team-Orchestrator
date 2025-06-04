import React from 'react';

interface Props {
  taskId: string;
  onApprove: () => void;
  onRequestChanges: () => void;
}

export const CheckpointRequest: React.FC<Props> = ({ taskId, onApprove, onRequestChanges }) => (
  <div className="border p-2 rounded">
    <p>Checkpoint for task {taskId}</p>
    <button className="mr-2" onClick={onApprove}>Approve</button>
    <button onClick={onRequestChanges}>Request changes</button>
  </div>
);
