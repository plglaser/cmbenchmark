import { useState, useEffect, useMemo } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import { Label } from './ui/label';
import { ScrollArea } from './ui/scroll-area';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { apiService } from '../services/api';
import type { IRData } from '../types/api';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  ConnectionMode,
} from 'reactflow';
import 'reactflow/dist/style.css';

interface IRVisualizationProps {
  irId: string;
  outputDir: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface GraphConfig {
  layout: 'grid' | 'hierarchical';
  edgeType: 'default' | 'smoothstep' | 'step' | 'straight' | 'bezier';
  showMinimap: boolean;
  showControls: boolean;
  nodeColor: string;
}

export function IRVisualization({ irId, outputDir, open, onOpenChange }: IRVisualizationProps) {
  const [irData, setIrData] = useState<IRData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [graphConfig, setGraphConfig] = useState<GraphConfig>({
    layout: 'grid',
    edgeType: 'default',
    showMinimap: true,
    showControls: true,
    nodeColor: '#ffffff',
  });

  useEffect(() => {
    if (open && irId && outputDir) {
      loadIRData();
    } else {
      setIrData(null);
      setError(null);
    }
  }, [open, irId, outputDir]);

  const loadIRData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.getIR(irId, outputDir);
      setIrData(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load IR data');
    } finally {
      setLoading(false);
    }
  };

  // Calculate hierarchical layout levels
  const calculateHierarchicalLayout = (nodes: IRData['nodes'], edges: IRData['edges']) => {
    // Build adjacency lists
    const incomingEdges = new Map<string, string[]>();
    const outgoingEdges = new Map<string, string[]>();
    
    edges.forEach(edge => {
      if (!incomingEdges.has(edge.targetId)) {
        incomingEdges.set(edge.targetId, []);
      }
      incomingEdges.get(edge.targetId)!.push(edge.sourceId);
      
      if (!outgoingEdges.has(edge.sourceId)) {
        outgoingEdges.set(edge.sourceId, []);
      }
      outgoingEdges.get(edge.sourceId)!.push(edge.targetId);
    });

    // Find root nodes (nodes with no incoming edges)
    const rootNodes = nodes.filter(node => !incomingEdges.has(node.id));
    
    // If no root nodes found, use nodes with fewest incoming edges
    if (rootNodes.length === 0) {
      const incomingCounts = nodes.map(node => ({
        node,
        count: incomingEdges.get(node.id)?.length || 0,
      }));
      incomingCounts.sort((a, b) => a.count - b.count);
      rootNodes.push(...incomingCounts.slice(0, Math.min(3, incomingCounts.length)).map(x => x.node));
    }

    // Assign levels using BFS from root nodes
    const levelMap = new Map<string, number>();
    const visited = new Set<string>();
    const queue: Array<{ id: string; level: number }> = [];

    rootNodes.forEach(node => {
      levelMap.set(node.id, 0);
      visited.add(node.id);
      queue.push({ id: node.id, level: 0 });
    });

    while (queue.length > 0) {
      const { id, level } = queue.shift()!;
      const children = outgoingEdges.get(id) || [];
      
      children.forEach(childId => {
        if (!visited.has(childId)) {
          levelMap.set(childId, level + 1);
          visited.add(childId);
          queue.push({ id: childId, level: level + 1 });
        } else {
          // Update level if we found a shorter path
          const currentLevel = levelMap.get(childId) || 0;
          if (level + 1 < currentLevel) {
            levelMap.set(childId, level + 1);
          }
        }
      });
    }

    // Assign levels to nodes without incoming edges (isolated nodes)
    nodes.forEach(node => {
      if (!levelMap.has(node.id)) {
        levelMap.set(node.id, 0);
      }
    });

    return levelMap;
  };

  // Convert IR nodes/edges to ReactFlow format
  const { nodes, edges } = useMemo(() => {
    if (!irData) return { nodes: [], edges: [] };

    let flowNodes: Node[];

    if (graphConfig.layout === 'hierarchical') {
      // Hierarchical layout
      const levelMap = calculateHierarchicalLayout(irData.nodes, irData.edges);
      const nodesByLevel = new Map<number, IRData['nodes']>();
      
      irData.nodes.forEach(node => {
        const level = levelMap.get(node.id) || 0;
        if (!nodesByLevel.has(level)) {
          nodesByLevel.set(level, []);
        }
        nodesByLevel.get(level)!.push(node);
      });

      const levelHeight = 200;
      const nodeWidth = 180;
      const horizontalSpacing = 20;

      flowNodes = irData.nodes.map((node) => {
        const level = levelMap.get(node.id) || 0;
        const nodesInLevel = nodesByLevel.get(level) || [];
        const indexInLevel = nodesInLevel.findIndex(n => n.id === node.id);
        const totalWidth = nodesInLevel.length * (nodeWidth + horizontalSpacing) - horizontalSpacing;
        const startX = -totalWidth / 2;
        
        return {
          id: node.id,
          type: 'default',
          position: {
            x: startX + indexInLevel * (nodeWidth + horizontalSpacing),
            y: level * levelHeight,
          },
          data: {
            label: (
              <div className="text-xs">
                <div className="font-semibold">{node.name}</div>
                <div className="text-muted-foreground text-[10px]">{node.type}</div>
              </div>
            ),
          },
          style: {
            background: graphConfig.nodeColor,
            border: '1px solid #e2e8f0',
            borderRadius: '4px',
            padding: '8px',
            minWidth: '120px',
          },
        };
      });
    } else {
      // Grid layout
      const cols = Math.ceil(Math.sqrt(irData.nodes.length));
      flowNodes = irData.nodes.map((node, index) => {
        const row = Math.floor(index / cols);
        const col = index % cols;
        return {
          id: node.id,
          type: 'default',
          position: { x: col * 200, y: row * 150 },
          data: {
            label: (
              <div className="text-xs">
                <div className="font-semibold">{node.name}</div>
                <div className="text-muted-foreground text-[10px]">{node.type}</div>
              </div>
            ),
          },
          style: {
            background: graphConfig.nodeColor,
            border: '1px solid #e2e8f0',
            borderRadius: '4px',
            padding: '8px',
            minWidth: '120px',
          },
        };
      });
    }

    const flowEdges: Edge[] = irData.edges.map((edge) => ({
      id: edge.id,
      source: edge.sourceId,
      target: edge.targetId,
      type: graphConfig.edgeType,
      label: edge.type,
      style: { stroke: '#64748b' },
      labelStyle: { fill: '#64748b', fontWeight: 600, fontSize: '10px' },
    }));

    return { nodes: flowNodes, edges: flowEdges };
  }, [irData, graphConfig.edgeType, graphConfig.layout, graphConfig.nodeColor]);

  const keyStats = useMemo(() => {
    if (!irData) return null;
    return {
      nodes: irData.nodes.length,
      edges: irData.edges.length,
      language: irData.language,
      modelName: irData.data.name || 'Unnamed',
      version: irData.data.version || 'N/A',
    };
  }, [irData]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="text-2xl">
                {keyStats?.modelName || 'IR Visualization'}
              </DialogTitle>
              <DialogDescription className="mt-2">
                {keyStats && (
                  <div className="flex gap-2 items-center flex-wrap">
                    <Badge variant="secondary">{keyStats.language}</Badge>
                    <span className="text-sm text-muted-foreground">
                      {keyStats.nodes} nodes • {keyStats.edges} edges
                    </span>
                    {keyStats.version !== 'N/A' && (
                      <span className="text-sm text-muted-foreground">
                        Version: {keyStats.version}
                      </span>
                    )}
                  </div>
                )}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {loading && (
          <div className="flex items-center justify-center py-8">
            <p className="text-muted-foreground">Loading IR data...</p>
          </div>
        )}

        {error && (
          <div className="p-4 bg-destructive/10 text-destructive rounded-md">
            {error}
          </div>
        )}

        {irData && !loading && (
          <Tabs defaultValue="graph" className="flex-1 flex flex-col min-h-0">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="graph">Graph</TabsTrigger>
              <TabsTrigger value="json">Raw IR JSON</TabsTrigger>
            </TabsList>

            <TabsContent value="graph" className="flex-1 flex gap-4 min-h-0 mt-4">
              <div className="flex-1 border rounded-lg overflow-hidden relative" style={{ minHeight: '500px' }}>
                <ReactFlow
                  nodes={nodes}
                  edges={edges}
                  connectionMode={ConnectionMode.Loose}
                  fitView
                  className="bg-background"
                >
                  {graphConfig.showControls && <Controls />}
                  {graphConfig.showMinimap && <MiniMap />}
                  <Background />
                </ReactFlow>
              </div>

              <Card className="w-64 flex-shrink-0">
                <CardHeader>
                  <CardTitle className="text-sm">Graph Configuration</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="layout">Layout</Label>
                    <select
                      id="layout"
                      value={graphConfig.layout}
                      onChange={(e) =>
                        setGraphConfig({ ...graphConfig, layout: e.target.value as GraphConfig['layout'] })
                      }
                      className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm"
                    >
                      <option value="grid">Grid</option>
                      <option value="hierarchical">Hierarchical</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edgeType">Edge Type</Label>
                    <select
                      id="edgeType"
                      value={graphConfig.edgeType}
                      onChange={(e) =>
                        setGraphConfig({ ...graphConfig, edgeType: e.target.value as GraphConfig['edgeType'] })
                      }
                      className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm"
                    >
                      <option value="default">Default</option>
                      <option value="smoothstep">Smoothstep</option>
                      <option value="step">Step</option>
                      <option value="straight">Straight</option>
                      <option value="bezier">Bezier</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="nodeColor">Node Background</Label>
                    <input
                      id="nodeColor"
                      type="color"
                      value={graphConfig.nodeColor}
                      onChange={(e) =>
                        setGraphConfig({ ...graphConfig, nodeColor: e.target.value })
                      }
                      className="flex h-9 w-full rounded-md border border-input bg-background"
                    />
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id="showMinimap"
                        checked={graphConfig.showMinimap}
                        onChange={(e) =>
                          setGraphConfig({ ...graphConfig, showMinimap: e.target.checked })
                        }
                        className="rounded border-gray-300"
                      />
                      <Label htmlFor="showMinimap" className="text-sm font-normal">
                        Show Minimap
                      </Label>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id="showControls"
                        checked={graphConfig.showControls}
                        onChange={(e) =>
                          setGraphConfig({ ...graphConfig, showControls: e.target.checked })
                        }
                        className="rounded border-gray-300"
                      />
                      <Label htmlFor="showControls" className="text-sm font-normal">
                        Show Controls
                      </Label>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="json" className="flex-1 min-h-0 mt-4">
              <div className="h-full border rounded-lg overflow-hidden">
                <ScrollArea className="h-full">
                  <div className="p-4">
                    <pre className="text-xs font-mono whitespace-pre-wrap break-words">
                      {JSON.stringify(irData, null, 2)}
                    </pre>
                  </div>
                </ScrollArea>
              </div>
            </TabsContent>
          </Tabs>
        )}
      </DialogContent>
    </Dialog>
  );
}

