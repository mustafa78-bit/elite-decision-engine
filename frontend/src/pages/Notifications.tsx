import NotificationCenter from "../components/notifications/NotificationCenter";

export default function Notifications() {
  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-gray-500">
        Notification Center
      </h2>
      <NotificationCenter />
    </div>
  );
}
