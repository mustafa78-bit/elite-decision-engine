import { memo } from "react";
import { Card, CardContent } from "../ui/card";

interface MemoizedWidgetProps {
  title: string;
  children: React.ReactNode;
  className?: string;
}

export const MemoizedWidget = memo(function MemoizedWidget({
  title,
  children,
  className,
}: MemoizedWidgetProps) {
  return (
    <Card className={className}>
      <CardContent className="p-4">
        <div className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em] mb-3">
          {title}
        </div>
        {children}
      </CardContent>
    </Card>
  );
});
