import { lazy, Suspense, type ComponentType } from "react";
import { Skeleton } from "../ui/skeleton";

function DefaultFallback() {
  return (
    <div className="min-h-screen bg-[var(--bg-base)] p-6 space-y-4">
      <Skeleton className="h-6 w-48 rounded-lg" />
      <div className="grid grid-cols-4 gap-3">
        <Skeleton className="h-24 rounded-xl" />
        <Skeleton className="h-24 rounded-xl" />
        <Skeleton className="h-24 rounded-xl" />
        <Skeleton className="h-24 rounded-xl" />
      </div>
      <Skeleton className="h-64 rounded-xl" />
    </div>
  );
}

export function lazyLoad(
  importFn: () => Promise<{ default: ComponentType<any> }>,
  fallback?: React.ReactNode,
) {
  const Component = lazy(importFn);

  return function LazyLoaded(props: any) {
    return (
      <Suspense fallback={fallback || <DefaultFallback />}>
        <Component {...props} />
      </Suspense>
    );
  };
}
