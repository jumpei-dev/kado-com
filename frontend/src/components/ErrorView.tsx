export default function ErrorView({ message = 'Something went wrong.' }: { message?: string }) {
  return <div className="p-4 text-red-600">{message}</div>;
}