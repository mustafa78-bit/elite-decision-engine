interface PageContainerProps {
  children: React.ReactNode;
  className?: string;
}

export function PageContainer({ children, className = "" }: PageContainerProps) {
  return (
    <div className={`max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 space-y-6 ${className}`}>
      {children}
    </div>
  );
}
