import { ReactNode } from 'react';

export type Tile = {
  id: string;
  title: string;
  component: ReactNode;
};

export type Measure = {
  id: string;
  name: string;
  description?: string;
  tiles: Tile[];
};

export type Dimension = {
  id: string;
  name: string;
  description?: string;
  measures: Measure[];
};
