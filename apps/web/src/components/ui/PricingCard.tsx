import React from 'react';
import { Check, ArrowRight, LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PricingCardProps {
  title: string;
  price: string;
  description: string;
  features: string[];
  icon: LucideIcon;
  isCurrent?: boolean;
  isPopular?: boolean;
  onUpgrade?: () => void;
  loading?: boolean;
}

export function PricingCard({
  title,
  price,
  description,
  features,
  icon: Icon,
  isCurrent = false,
  isPopular = false,
  onUpgrade,
  loading = false
}: PricingCardProps) {
  return (
    <div className={cn(
      "relative flex flex-col p-6 bg-white rounded-lg border transition-all duration-300",
      isPopular ? "border-primary scale-[1.02] z-10" : "border-border hover:border-primary/40",
      isCurrent && "bg-muted/5 border-emerald-500/50"
    )}>
      {isCurrent ? (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-emerald-500 text-white text-[10px] font-bold rounded-full uppercase tracking-wider flex items-center gap-1">
          <Check className="h-2.5 w-2.5" />
          Plan actuel
        </div>
      ) : isPopular && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-primary text-white text-[10px] font-bold rounded-full uppercase tracking-wider">
          Le plus populaire
        </div>
      )}

      <div className="mb-6">
        <div className={cn(
          "w-10 h-10 rounded-lg flex items-center justify-center mb-4 border",
          isPopular ? "bg-primary/10 border-primary/20 text-primary" : "bg-muted border-border text-muted-foreground"
        )}>
          <Icon className="h-5 w-5" />
        </div>
        <h3 className="text-lg font-bold text-foreground mb-1">{title}</h3>
        <div className="flex items-baseline gap-1 mb-2">
          <span className="text-2xl font-bold text-foreground">{price}</span>
          <span className="text-sm text-muted-foreground">/ mois</span>
        </div>
        <p className="text-[13px] text-muted-foreground line-height-relaxed">{description}</p>
      </div>

      <div className="flex-1 space-y-3 mb-8">
        {features.map((feature, idx) => (
          <div key={idx} className="flex items-start gap-3">
            <div className="mt-1 w-4 h-4 rounded-full bg-emerald-500/10 flex items-center justify-center shrink-0">
              <Check className="h-2.5 w-2.5 text-emerald-600" />
            </div>
            <span className="text-[13px] text-foreground/80">{feature}</span>
          </div>
        ))}
      </div>

      <button
        onClick={onUpgrade}
        disabled={isCurrent || loading}
        className={cn(
          "w-full h-11 rounded-lg text-[13px] font-bold transition-all flex items-center justify-center gap-2 group",
          isCurrent 
            ? "bg-muted text-muted-foreground cursor-default border border-border"
            : isPopular
              ? "bg-primary text-white hover:opacity-90"
              : "bg-white text-foreground border border-border hover:bg-accent"
        )}
      >
        {isCurrent ? (
          "Plan actif"
        ) : loading ? (
          <div className="h-4 w-4 border-2 border-current/30 border-t-current rounded-full animate-spin" />
        ) : (
          <>
            Continuer avec {title}
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </>
        )}
      </button>
    </div>
  );
}
