export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-paper p-4">
      <div className="flex items-center gap-2">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/schoolmate/logo/schoolmate-mark.png" alt="" className="h-10 w-10" />
        <span className="text-2xl font-extrabold tracking-tight">
          School<span className="text-primary">Mate</span>
        </span>
      </div>
      {children}
      <p className="font-hand text-lg text-brand-blue">Some bonds never fade. ♥</p>
    </div>
  );
}
