import { useParams } from 'react-router-dom';
import { useStoreDetail } from '../hooks/useStoreDetail';

export default function StoreDetail() {
  const { id = '' } = useParams();
  const { data, isLoading, isError } = useStoreDetail(id);

  if (isLoading) return <div className="p-4">Loading…</div>;
  if (isError || !data) return <div className="p-4 text-red-600">Failed to load.</div>;

  return (
    <div className="p-4 space-y-4">
      <header className="text-xl font-semibold">{data.name}</header>
      <div className="text-slate-500">{data.area} / {data.genre}</div>
      <section className="space-y-2">
        <div className="font-medium">今日のタイムライン</div>
        <div className="grid grid-cols-12 gap-1">
          {data.timeline.map((t, i) => (
            <div key={i} className={`h-8 rounded ${t.active ? 'bg-emerald-500' : 'bg-slate-300'}`} title={t.slot}/>
          ))}
        </div>
      </section>
      <div className="text-sm text-slate-500">
        利用率: {data.util_today}%（前日: {data.util_yesterday ?? '-'}% / 7日平均: {data.util_7d ?? '-'}%）
      </div>
    </div>
  );
}