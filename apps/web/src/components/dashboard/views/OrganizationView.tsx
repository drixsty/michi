import React, { useState } from 'react';
import { useQuery, useMutation, gql } from '@apollo/client';
import { 
  Users, 
  UserPlus, 
  ShieldAlert, 
  ShieldCheck, 
  Eye, 
  Search, 
  MoreVertical, 
  Shield,
  Mail,
  Save,
  CheckCircle2,
  Settings2,
  ChevronRight,
  CreditCard
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { LoadingState } from '../../ui/LoadingState';
import { CustomSelect } from '../../ui/CustomSelect';
import { InviteMemberPanel } from '../InviteMemberPanel';
import { MemberDetailPanel } from '../MemberDetailPanel';
import { BillingSettings } from '../BillingSettings';

const GET_ORG_DATA = gql`
  query GetOrgData {
    organizationMembers {
      organizationId
      userId
      role
      permissions
      user {
        id
        email
        firstName
        lastName
        createdAt
      }
    }
    pendingInvitations {
      id
      email
      role
      status
      code
      createdAt
      expiresAt
    }
    currentOrganization {
      id
      name
      settings
      plan
      subscriptionStatus
    }
    me {
      id
    }
  }
`;

const UPDATE_ORGANIZATION = gql`
  mutation UpdateOrganization($input: UpdateOrganizationInput!) {
    updateOrganization(input: $input) {
      id
      name
      settings
    }
  }
`;

const CREATE_PORTAL_SESSION = gql`
  mutation CreatePortalSession($returnUrl: String!) {
    createBillingPortalSession(returnUrl: $returnUrl)
  }
`;

const ROLE_ICONS: Record<string, any> = {
  admin: ShieldAlert,
  manager: ShieldCheck,
  viewer: Eye,
};

const ROLE_LABELS: Record<string, string> = {
  admin: 'Administrateur',
  manager: 'Gestionnaire',
  viewer: 'Lecteur',
  ADMIN: 'Administrateur',
  MANAGER: 'Gestionnaire',
  VIEWER: 'Lecteur',
};

type OrgTabType = 'team' | 'settings' | 'billing';

export function OrganizationView() {
  const [activeTab, setActiveTab] = useState<OrgTabType>('team');
  const [showInvitePanel, setShowInvitePanel] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [currency, setCurrency] = useState('€');
  const [isMutualized, setIsMutualized] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  // State for detail panel
  const [selectedMember, setSelectedMember] = useState<any>(null);
  const [selectedInvitation, setSelectedInvitation] = useState<any>(null);
  const [showDetailPanel, setShowDetailPanel] = useState(false);

  const { data, loading, refetch } = useQuery(GET_ORG_DATA, {
    errorPolicy: 'all',
    fetchPolicy: 'cache-and-network',
    onCompleted: (data) => {
      if (data?.currentOrganization?.settings) {
        try {
          const settings = JSON.parse(data.currentOrganization.settings);
          if (settings.currency) setCurrency(settings.currency);
          if (settings.is_mutualized !== undefined) setIsMutualized(settings.is_mutualized);
        } catch (e) {
          console.error("Failed to parse organization settings", e);
        }
      }
    }
  });

  const [updateOrganization, { loading: updatingSettings }] = useMutation(UPDATE_ORGANIZATION, {
    onCompleted: () => {
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
      refetch();
    }
  });

  const [createPortal] = useMutation(CREATE_PORTAL_SESSION);


  const handleUpdateSettings = async () => {
    await updateOrganization({
      variables: {
        input: {
          currency,
          isMutualized
        }
      }
    });
  };

  if (loading && !data) return <LoadingState size="lg" message="Chargement de l'organisation..." />;

  const members = data?.organizationMembers ?? [];
  const invitations = data?.pendingInvitations ?? [];
  const currentUserId = data?.me?.id;
  
  const currentUserRole = members.find((m: any) => m.user?.id === currentUserId)?.role?.toLowerCase() || 'viewer';
  const isAdmin = currentUserRole === 'admin';

  const filteredMembers = members.filter((m: any) => {
    const email = m.user?.email || '';
    const name = `${m.user?.firstName || ''} ${m.user?.lastName || ''}`;
    return email.toLowerCase().includes(searchTerm.toLowerCase()) || 
           name.toLowerCase().includes(searchTerm.toLowerCase());
  });

  const tabs = [
    { id: 'team', label: 'Équipe', icon: Users },
    ...(isAdmin ? [
      { id: 'settings', label: 'Paramètres', icon: Settings2 },
      { id: 'billing', label: 'Facturation', icon: CreditCard }
    ] : [])
  ] as const;

  const openMemberDetail = (m: any) => {
    setSelectedMember(m);
    setSelectedInvitation(null);
    setShowDetailPanel(true);
  };

  const openInvitationDetail = (inv: any) => {
    setSelectedInvitation(inv);
    setSelectedMember(null);
    setShowDetailPanel(true);
  };

  return (
    <div className="animate-in fade-in duration-500 max-w-7xl mx-auto">
      
      {showSuccess && (
        <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-[100] px-4 py-2.5 bg-foreground text-background rounded-lg flex items-center gap-3 animate-in fade-in slide-in-from-bottom-4 duration-300 border border-white/10 shadow-lg">
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          <span className="text-[13px] font-medium">Paramètres enregistrés</span>
        </div>
      )}

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-border mb-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-primary/5 flex items-center justify-center text-primary border border-primary/10">
            <Users className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <span className="text-[13px] text-muted-foreground flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                {members.length} membres actifs
              </span>
              {invitations.length > 0 && (
                <span className="text-[13px] text-muted-foreground flex items-center gap-1.5 border-l border-border pl-3">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                  {invitations.length} en attente
                </span>
              )}
            </div>
          </div>
        </div>

        {activeTab === 'team' && isAdmin && (
          <button 
            onClick={() => setShowInvitePanel(true)}
            className="h-9 px-4 bg-foreground text-background rounded-lg text-[13px] font-semibold hover:opacity-90 transition-all flex items-center justify-center gap-2 shadow-sm shrink-0"
          >
            <UserPlus className="h-4 w-4" />
            Inviter un membre
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-[200px_1fr] gap-8">
        <aside className="space-y-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as OrgTabType)}
              className={cn(
                "w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] transition-all",
                activeTab === tab.id 
                  ? "bg-primary/5 text-primary font-semibold" 
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <tab.icon className={cn("h-4 w-4", activeTab === tab.id ? "text-primary" : "text-muted-foreground/60")} />
              {tab.label}
              {activeTab === tab.id && <ChevronRight className="h-3 w-3 ml-auto opacity-50" />}
            </button>
          ))}
        </aside>

        <main className="space-y-6">
          {activeTab === 'team' && (
            <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-8 animate-in fade-in duration-300">
              <section className="bg-white rounded-lg border border-border overflow-hidden self-start">
                <div className="px-5 py-4 border-b border-border flex items-center justify-between bg-muted/20">
                  <h2 className="text-[13px] font-semibold text-foreground">Équipe</h2>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/50" />
                    <input 
                      type="text" 
                      placeholder="Filtrer..." 
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-9 pr-4 h-8 bg-background border border-border rounded-lg text-[13px] focus:ring-2 focus:ring-primary/10 focus:border-primary/20 outline-none w-64 transition-all"
                    />
                  </div>
                </div>

                <div className="divide-y divide-border">
                  {filteredMembers.length > 0 ? filteredMembers.map((member: any) => {
                    const roleKey = member.role || 'viewer';
                    const RoleIcon = ROLE_ICONS[roleKey.toLowerCase()] || Shield;
                    const email = member.user?.email ?? '—';
                    const name = member.user?.firstName || member.user?.lastName 
                      ? `${member.user.firstName || ''} ${member.user.lastName || ''}`.trim()
                      : email.split('@')[0];

                    return (
                      <div 
                        key={member.userId} 
                        onClick={() => openMemberDetail(member)}
                        className="p-4 hover:bg-muted/30 transition-colors flex items-center justify-between group cursor-pointer"
                      >
                        <div className="flex items-center gap-4">
                          <div className="w-9 h-9 rounded-lg bg-muted flex items-center justify-center text-muted-foreground font-semibold text-xs border border-border">
                            {name.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <p className="text-sm font-semibold text-foreground leading-tight">{name}</p>
                              <div className="flex items-center gap-1 px-1.5 py-0.5 bg-muted/50 border border-border rounded-md text-muted-foreground">
                                <RoleIcon className="h-2.5 w-2.5" />
                                <span className="text-[10px] font-medium">{ROLE_LABELS[roleKey] || roleKey}</span>
                              </div>
                            </div>
                            <p className="text-[12px] text-muted-foreground">{email}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {isAdmin && member.user?.id !== currentUserId && (
                            <button 
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedMember(member);
                                setShowDetailPanel(true);
                              }}
                              className="p-2 hover:bg-muted rounded-lg transition-all text-muted-foreground hover:text-foreground opacity-0 group-hover:opacity-100"
                            >
                              <MoreVertical className="h-4 w-4" />
                            </button>
                          )}
                          <ChevronRight className="h-4 w-4 text-muted-foreground/20 group-hover:text-muted-foreground/50 transition-all" />
                        </div>
                      </div>
                    );
                  }) : (
                    <div className="p-10 text-center text-muted-foreground bg-muted/5">
                      <p className="text-[13px]">Aucun membre trouvé</p>
                    </div>
                  )}
                </div>
              </section>

              <aside className="space-y-6">
                <div className="bg-muted/20 border border-border rounded-lg p-5 space-y-4">
                  <h2 className="text-[13px] font-semibold text-foreground flex items-center justify-between">
                    Invitations
                    <span className="px-2 py-0.5 bg-amber-100 text-amber-700 rounded-md text-[11px] font-bold">{invitations.length}</span>
                  </h2>
                  
                  <div className="space-y-3">
                    {invitations.length === 0 ? (
                      <div className="py-8 text-center bg-white/50 rounded-lg border border-dashed border-border flex flex-col items-center">
                        <Mail className="h-5 w-5 text-muted-foreground/30 mb-2" />
                        <p className="text-[12px] text-muted-foreground">Aucune attente</p>
                      </div>
                    ) : (
                      invitations.map((invite: any) => (
                        <div 
                          key={invite.id} 
                          onClick={() => openInvitationDetail(invite)}
                          className="bg-white p-3.5 rounded-lg border border-border space-y-3 cursor-pointer hover:border-amber-200 hover:shadow-sm transition-all group"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex items-center gap-3 min-w-0">
                              <div className="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center text-amber-600 border border-amber-100 shrink-0">
                                <Mail className="h-4 w-4" />
                              </div>
                              <div className="min-w-0">
                                <p className="text-[12px] font-semibold text-foreground truncate">{invite.email}</p>
                                <p className="text-[10px] text-muted-foreground font-medium">{ROLE_LABELS[invite.role] || invite.role}</p>
                              </div>
                            </div>
                            <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/20 group-hover:text-amber-500 transition-all" />
                          </div>
                          <div className="flex items-center justify-between text-[10px] pt-1">
                            <span className="font-semibold text-amber-600">En attente</span>
                            <span className="text-muted-foreground/60">{new Date(invite.expiresAt).toLocaleDateString()}</span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </aside>
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="space-y-6 animate-in fade-in duration-300">
              <section className="bg-white rounded-lg border border-border overflow-hidden">
                <div className="px-5 py-4 border-b border-border bg-muted/20">
                  <h2 className="text-[13px] font-semibold text-foreground flex items-center gap-2">
                    Configuration stratégique
                  </h2>
                </div>
                <div className="p-5 space-y-6">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
                    <div className="space-y-0.5">
                      <p className="text-sm font-semibold text-foreground">Devise de l'organisation</p>
                      <p className="text-[13px] text-muted-foreground">Utilisée pour les calculs consolidés.</p>
                    </div>
                    <CustomSelect 
                      options={[
                        { value: '€', label: 'Euro (€)' },
                        { value: '$', label: 'US Dollar ($)' },
                        { value: '£', label: 'British Pound (£)' },
                        { value: 'CHF', label: 'Swiss Franc (CHF)' }
                      ]}
                      value={currency}
                      onChange={setCurrency}
                      className="w-full sm:w-48"
                    />
                  </div>

                  <div className="flex items-center justify-between gap-4">
                    <div className="space-y-0.5">
                      <p className="text-sm font-semibold text-foreground">Mutualisation des stocks</p>
                      <p className="text-[13px] text-muted-foreground">Fusionner les stocks pour tout SKU identique.</p>
                    </div>
                    <button 
                      type="button"
                      onClick={() => setIsMutualized(!isMutualized)}
                      className={cn(
                        "w-9 h-5 rounded-full transition-all relative flex items-center px-0.5 border border-border",
                        isMutualized ? "bg-primary border-primary" : "bg-muted"
                      )}
                    >
                      <div className={cn(
                        "w-3.5 h-3.5 bg-white rounded-full transition-transform duration-200 shadow-sm",
                        isMutualized ? "translate-x-4" : "translate-x-0"
                      )} />
                    </button>
                  </div>

                  <div className="pt-2 flex justify-end">
                    <button 
                      onClick={handleUpdateSettings}
                      disabled={updatingSettings}
                      className="h-9 px-6 bg-foreground text-background rounded-lg text-[13px] font-semibold hover:opacity-90 transition-all flex items-center gap-2"
                    >
                      {updatingSettings ? (
                        <div className="h-3.5 w-3.5 border-2 border-background/30 border-t-background rounded-full animate-spin" />
                      ) : (
                        <>
                          <Save className="h-3.5 w-3.5" />
                          Sauvegarder les paramètres
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </section>
            </div>
          )}
          {activeTab === 'billing' && (
            <div className="animate-in fade-in slide-in-from-bottom-2 duration-400">
              <BillingSettings />
            </div>
          )}
        </main>
      </div>

      <InviteMemberPanel
        isOpen={showInvitePanel}
        onClose={() => setShowInvitePanel(false)}
        onSuccess={refetch}
        existingMembers={members}
        pendingInvitations={invitations}
      />

      <MemberDetailPanel
        isOpen={showDetailPanel}
        member={selectedMember}
        invitation={selectedInvitation}
        onClose={() => setShowDetailPanel(false)}
        onSuccess={refetch}
        currentUserId={currentUserId}
        currentUserRole={currentUserRole}
      />
    </div>
  );
}
