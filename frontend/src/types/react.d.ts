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

export = React;
export as namespace React;
