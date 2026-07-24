interface Props {
  count: number;
}

export default function NotificationBadge({ count }: Props) {
  if (count === 0) return null;
  return (
    <span className="inline-flex items-center justify-center w-4 h-4 text-[11px] font-bold text-white bg-blue-600 rounded-full">
      {count > 9 ? "9+" : count}
    </span>
  );
}
