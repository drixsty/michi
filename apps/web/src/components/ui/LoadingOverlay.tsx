import { useTranslations } from 'next-intl';

interface LoadingOverlayProps {
  message?: string;
}

export function LoadingOverlay({ message }: LoadingOverlayProps) {
  const t = useTranslations('common');
  const displayMessage = message || t('loading');

  return (
    <div className="fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-white/70 backdrop-blur-2xl animate-in fade-in duration-700">
      <div className="relative mb-10">
        {/* Cercles pulsants doux (sans ombre) */}
        <div className="absolute inset-x-0 -top-4 -bottom-4 bg-primary/5 rounded-full blur-3xl animate-[pulse_3s_ease-in-out_infinite]" />
        
        <div className="relative w-16 h-16 bg-white/50 rounded-2xl border border-slate-200/60 flex items-center justify-center overflow-hidden">
          {/* Progress loop discret */}
          <div className="absolute inset-0 bg-gradient-to-tr from-primary/5 via-transparent to-primary/5" />
          <div className="w-8 h-8 border-2 border-primary/10 border-t-primary rounded-full animate-spin transition-all" />
        </div>
      </div>
      
      <div className="space-y-3 text-center px-6">
        <p className="text-[11px] font-bold text-slate-900 tracking-wider leading-loose">
          {displayMessage}
        </p>
        
        {/* Indicateur de progression minimaliste */}
        <div className="flex items-center justify-center gap-1">
          {[0, 1, 2].map((i) => (
            <div 
              key={i}
              className="w-1 h-1 rounded-full bg-primary/40 animate-pulse"
              style={{ animationDelay: `${i * 0.2}s` }}
            />
          ))}
        </div>
      </div>

      <div className="absolute bottom-12 flex items-center gap-2 text-[10px] text-slate-400 font-semibold tracking-wider opacity-60">
        <span className="w-8 h-px bg-slate-200" />
        Michi 道
        <span className="w-8 h-px bg-slate-200" />
      </div>
    </div>
  );
}
