/// <reference types="vite/client" />

declare namespace JSX {
  interface Element extends React.ReactElement<any, any> {}
  interface ElementClass extends React.Component<any> {
    render(): React.ReactNode;
  }
  interface ElementAttributesProperty {
    props: {};
  }
  interface ElementChildrenAttribute {
    children: {};
  }
  interface IntrinsicElements {
    [elemName: string]: any;
  }
}

declare module 'react' {
  export type ReactNode = any;
  export type ReactElement<P = any, T extends string | any = any> = any;
  export type FC<P = {}> = (props: P) => ReactElement | null;
  export type ComponentType<P = {}> = FC<P>;
  export type Dispatch<A> = (value: A) => void;
  export type SetStateAction<S> = S | ((prevState: S) => S);
  
  export function useState<T>(initialState: T | (() => T)): [T, Dispatch<SetStateAction<T>>];
  export function useEffect(effect: () => void | (() => void), deps?: readonly any[]): void;
  export function useCallback<T extends (...args: any[]) => any>(callback: T, deps: readonly any[]): T;
  export function useMemo<T>(factory: () => T, deps: readonly any[] | undefined): T;
  export function useRef<T>(initialValue: T): { current: T };
  export function createContext<T>(defaultValue: T): any;
  export function useContext<T>(context: any): T;
  
  export interface CSSProperties {
    [key: string]: any;
  }

  export interface HTMLAttributes<T> {
    [key: string]: any;
  }

  export interface ButtonHTMLAttributes<T> extends HTMLAttributes<T> {
    [key: string]: any;
  }

  const React: any;
  export default React;
}

declare module 'react/jsx-runtime' {
  export const jsx: any;
  export const jsxs: any;
  export const Fragment: any;
}

declare module 'react/jsx-dev-runtime' {
  export const jsxDEV: any;
  export const Fragment: any;
}

declare module 'react-dom' {
  export function createRoot(container: Element | DocumentFragment): any;
  export function render(element: any, container: any): void;
}

declare module 'react-dom/client' {
  export function createRoot(container: Element | DocumentFragment): {
    render(children: any): void;
    unmount(): void;
  };
}

declare module 'lucide-react' {
  export const [key: string]: any;
}

declare module 'recharts' {
  export const ResponsiveContainer: any;
  export const AreaChart: any;
  export const Area: any;
  export const LineChart: any;
  export const Line: any;
  export const BarChart: any;
  export const Bar: any;
  export const XAxis: any;
  export const YAxis: any;
  export const CartesianGrid: any;
  export const Tooltip: any;
  export const Legend: any;
  export const PieChart: any;
  export const Pie: any;
  export const Cell: any;
}

declare module 'leaflet' {
  export const [key: string]: any;
}

declare module 'clsx' {
  export default function clsx(...args: any[]): string;
}

declare module 'tailwind-merge' {
  export function twMerge(...args: any[]): string;
}
