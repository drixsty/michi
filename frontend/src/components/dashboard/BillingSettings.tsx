import React from 'react';
import { useQuery, useMutation, gql } from '@apollo/client';
import { 
  CreditCard, 
  ExternalLink,
  Zap,
  ArrowRight,
  ShieldCheck
} from 'lucide-react';
import { cn } from '@/lib/utils';

const GET_CURRENT_ORG = gql`
  query GetCurrentOrg {
    currentOrganization {
      id
      name
      plan
      subscriptionStatus
    }
  }
`;

const CREATE_PORTAL_SESSION = gql`
  mutation CreatePortalSession($returnUrl: String!) {
    createBillingPortalSession(returnUrl: $returnUrl)
  }
`;

export function BillingSettings() {
  const { data, loading } = useQuery(GET_CURRENT_ORG);
  const [createPortal, { loading: creatingPortal }] = useMutation(CREATE_PORTAL_SESSION);

  const org = data?.currentOrganization;

  const handleManageSubscription = async () => {
    try {
      const { data: portalData } = await createPortal({
        variables: { returnUrl: window.location.href }
      });
      if (portalData?.createBillingPortalSession) {
        window.location.href = portalData.createBillingPortalSession;
      }
    } catch (err) {
      console.error("Portal error:", err);
      alert("Erreur lors de l'accès au portail Stripe.");
    }
  };

  if (loading) return (
    <div className="h-[120px] flex items-center justify-center bg-muted/5 border border-border rounded-xl border-dashed">
      <div className="h-4 w-4 border-2 border-primary/20 border-t-primary rounded-full animate-spin" />
    </div>
  );

  const isPro = org?.plan === 'PRO' || org?.plan === 'ENTERPRISE';
  const isActive = org?.subscriptionStatus === 'ACTIVE';

  return (
    <div className="animate-in fade-in slide-in-from-bottom-2 duration-500">
      
      <section className="bg-white rounded-lg border border-border overflow-hidden">
        <div className="px-5 py-4 border-b border-border bg-muted/20 flex items-center justify-between">
          <div className="space-y-0.5">
            <h2 className="text-[13px] font-semibold text-foreground">Abonnement & Facturation</h2>
            <p className="text-[11px] text-muted-foreground">Gérez votre plan Michi et vos informations de paiement Stripe.</p>
          </div>
          {isActive && (
            <div className="flex items-center gap-1.5 text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">
              <span className="w-1 h-1 rounded-full bg-emerald-500 animate-pulse" />
              Actif
            </div>
          )}
        </div>
        
        <div className="p-5 space-y-8">
          {/* Main Info Row */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-start gap-4">
              <div className={cn(
                "w-12 h-12 rounded-xl flex items-center justify-center shrink-0 border",
                isPro ? "bg-foreground text-background" : "bg-muted text-muted-foreground shadow-sm"
              )}>
                {isPro ? <Zap className="h-6 w-6 fill-current" /> : <ShieldCheck className="h-6 w-6" />}
              </div>
              
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-foreground">
                  Plan {org?.plan?.charAt(0) + org?.plan?.slice(1).toLowerCase() || 'Basic'}
                </h3>
                <p className="text-[13px] text-muted-foreground leading-relaxed max-w-[400px]">
                  {isPro 
                    ? "Votre organisation bénéficie actuellement du plan Premium pour ses prévisions et alertes IA."
                    : "Le plan gratuit est limité à 100 SKUs et un utilisateur unique. Idéal pour débuter."
                  }
                </p>
              </div>
            </div>

            <button 
              onClick={handleManageSubscription}
              disabled={creatingPortal}
              className="h-9 px-4 bg-foreground text-background rounded-lg text-[13px] font-semibold hover:opacity-90 transition-all flex items-center justify-center gap-2 shadow-sm shrink-0"
            >
              {creatingPortal ? (
                <div className="h-3 w-3 border-2 border-background/30 border-t-background rounded-full animate-spin" />
              ) : (
                <>
                  <CreditCard className="h-3.5 w-3.5" />
                  Accéder au portail sécurisé
                  <ArrowRight className="h-3 w-3 opacity-50 ml-1" />
                </>
              )}
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-border">
            <div className="p-4 rounded-xl border border-border bg-muted/5 space-y-1">
              <p className="text-[11px] font-semibold text-muted-foreground tracking-widest px-0.5">Mode de facturation</p>
              <p className="text-[13px] font-medium text-foreground flex items-center gap-2">
                Externalisé via Stripe 
                <ExternalLink className="h-3 w-3 text-muted-foreground/40" />
              </p>
            </div>
            
            <div className="p-4 rounded-xl border border-border bg-muted/5 space-y-1">
              <p className="text-[11px] font-semibold text-muted-foreground tracking-widest px-0.5">Moyens de paiement</p>
              <button 
                onClick={handleManageSubscription}
                className="text-[13px] font-medium text-primary hover:underline text-left flex items-center gap-1.5"
              >
                Gérer sur Stripe
                <ArrowRight className="h-3 w-3" />
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
