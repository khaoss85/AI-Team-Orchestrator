// Asset Dependency Management Components
export { RelatedAssetsModal } from './RelatedAssetsModal';
export { AssetHistoryPanel } from './AssetHistoryPanel';
export { DependencyGraph } from './DependencyGraph';

// Hooks
export { useAssetDependencies } from '../../hooks/useAssetDependencies';

// Types
export type { 
  AssetDependency, 
  AssetUpdateSuggestion, 
  AssetVersion, 
  AssetHistory 
} from '../../hooks/useAssetDependencies';

export type { 
  AssetNode, 
  AssetEdge 
} from './DependencyGraph';