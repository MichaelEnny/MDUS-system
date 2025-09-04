import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

export interface Metric {
  name: string;
  value: number;
  delta: number;
  id: string;
}

export function reportWebVitals(onPerfEntry?: (metric: Metric) => void) {
  if (onPerfEntry && onPerfEntry instanceof Function) {
    getCLS(onPerfEntry);
    getFID(onPerfEntry);
    getFCP(onPerfEntry);
    getLCP(onPerfEntry);
    getTTFB(onPerfEntry);
  }
}