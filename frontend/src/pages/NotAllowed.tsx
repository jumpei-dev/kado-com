export default function NotAllowed() {
  return (
    <div className="p-6 space-y-2">
      <div className="text-lg font-semibold">Access denied</div>
      <p className="text-slate-600">このLINE IDには閲覧権限がありません。</p>
    </div>
  );
}