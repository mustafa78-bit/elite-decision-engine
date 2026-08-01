import { cn } from "../../lib/utils";

interface AvatarProps {
  src?: string;
  alt?: string;
  fallback?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeMap = {
  sm: "w-6 h-6 text-[9px]",
  md: "w-8 h-8 text-[11px]",
  lg: "w-10 h-10 text-xs",
};

export function Avatar({ src, alt, fallback, size = "md", className }: AvatarProps) {
  if (src) {
    return (
      <img
        src={src}
        alt={alt || ""}
        className={cn("rounded-full object-cover shrink-0", sizeMap[size], className)}
      />
    );
  }

  return (
    <div
      className={cn(
        "rounded-full shrink-0 bg-[var(--bg-elevated)] border border-[var(--border-subtle)] flex items-center justify-center font-medium text-[var(--text-muted)]",
        sizeMap[size],
        className,
      )}
    >
      {fallback ? fallback.charAt(0).toUpperCase() : "?"}
    </div>
  );
}
