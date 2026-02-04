export type ConstructKindFilter = 'all' | 'nodes' | 'edges';

export const constructKindOptions: Array<{ value: ConstructKindFilter; label: string }> = [
  { value: 'all', label: 'Nodes + Edges' },
  { value: 'nodes', label: 'Nodes' },
  { value: 'edges', label: 'Edges' },
];

export const kindFilterLabel = (value: ConstructKindFilter): string => {
  switch (value) {
    case 'nodes':
      return 'Nodes';
    case 'edges':
      return 'Edges';
    default:
      return 'Nodes + Edges';
  }
};

export const kindFilterToKinds = (value: ConstructKindFilter): string[] | null => {
  if (value === 'nodes') {
    return ['node_type'];
  }
  if (value === 'edges') {
    return ['edge_type'];
  }
  return null;
};

export const filterFrequencyDataByKind = <T extends { kind?: string }>(
  data: T[] = [],
  value: ConstructKindFilter
): T[] => {
  const kinds = kindFilterToKinds(value);
  if (!kinds?.length) {
    return data;
  }
  return data.filter((item) => item.kind && kinds.includes(item.kind));
};
