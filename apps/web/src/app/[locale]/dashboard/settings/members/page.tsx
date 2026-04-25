'use client';

import React, { useState } from 'react';
import { useTranslations } from 'next-intl';
import { 
  Users, UserPlus, Shield, ShieldCheck, 
  MoreVertical, Mail, ShieldAlert, Check, 
  Settings2, UserCog, Filter, Search
} from 'lucide-react';
import { PermissionGuard } from '@/components/auth/PermissionGuard';
import { CanDo } from '@/components/auth/CanDo';
import { Permission } from '@/hooks/usePermissions';
import { cn } from '@/lib/utils';

// Mock data pour la démo UI (à remplacer par des queries Apollo)
const MOCK_MEMBERS = [
  { 
    id: '1', 
    name: 'Kevin TSAGUE', 
    email: 'kevin@michi.app', 
    role: 'OWNER', 
    status: 'active',
    avatar: 'KT',
    permissions: ['all']
  },
  { 
    id: '2', 
    name: 'Sarah Connor', 
    email: 'sarah@skynet.com', 
    role: 'ADMIN', 
    status: 'active',
    avatar: 'SC',
    permissions: ['org:edit', 'inventory:edit']
  },
  { 
    id: '3', 
    name: 'John Doe', 
    email: 'john@example.com', 
    role: 'MANAGER', 
    status: 'active',
    avatar: 'JD',
    permissions: ['inventory:view', 'supplier:view']
  },
  { 
    id: '4', 
    name: 'Alice Smith', 
    email: 'alice@michi.app', 
    role: 'VIEWER', 
    status: 'pending',
    avatar: 'AS',
    permissions: ['org:view']
  },
];

export default function MembersSettingsPage() {
  const t = useTranslations('settings.members');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedMember, setSelectedMember] = useState<any>(null);

  return (
    <div className="max-w-6xl mx-auto space-y-10 animate-in fade-in duration-500">
      
      {/* Header & Actions */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-1.5">
          <div className="flex items-center gap-3 text-primary">
            <Users className="w-5 h-5" />
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Gestion des Membres</h1>
          </div>
          <p className="text-[13px] text-slate-500 font-medium">Contrôlez qui peut accéder et modifier les données de votre organisation.</p>
        </div>

        <PermissionGuard permission={Permission.ORG_MANAGE_MEMBERS}>
          <button className="h-10 bg-slate-900 text-white px-4 rounded-lg text-[13px] font-bold flex items-center gap-2 hover:bg-slate-800 transition-all shadow-lg shadow-slate-200 active:scale-[0.98]">
            <UserPlus className="w-4 h-4" />
            Inviter un membre
          </button>
        </PermissionGuard>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        
        {/* Members List */}
        <div className="lg:col-span-2 space-y-4">
          
          {/* Filters Bar */}
          <div className="flex items-center gap-3 p-2 bg-white border border-slate-200 rounded-lg shadow-sm">
            <div className="relative flex-1 group">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-primary transition-colors" />
              <input 
                type="text" 
                placeholder="Rechercher par nom ou email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full h-9 pl-9 pr-3 bg-transparent text-[13px] font-medium focus:outline-none"
              />
            </div>
            <div className="h-4 w-[1px] bg-slate-200" />
            <button className="h-9 px-3 text-[12px] font-bold text-slate-500 hover:text-slate-900 flex items-center gap-2">
              <Filter className="w-3.5 h-3.5" />
              Filtrer
            </button>
          </div>

          {/* Table */}
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
            <div className="divide-y divide-slate-100">
              {MOCK_MEMBERS.map((member) => (
                <div 
                  key={member.id}
                  onClick={() => setSelectedMember(member)}
                  className={cn(
                    "flex items-center justify-between p-4 hover:bg-slate-50/50 cursor-pointer transition-all border-l-4",
                    selectedMember?.id === member.id ? "border-primary bg-primary/[0.02]" : "border-transparent"
                  )}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-500 font-bold text-xs uppercase shadow-sm">
                      {member.avatar}
                    </div>
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <p className="text-[13px] font-bold text-slate-900">{member.name}</p>
                        {member.status === 'pending' && (
                          <span className="text-[9px] font-bold text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-100 uppercase tracking-wider">Invitation</span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400 font-medium flex items-center gap-1.5">
                        <Mail className="w-3 h-3" />
                        {member.email}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <div className={cn(
                        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider border",
                        member.role === 'OWNER' ? "bg-indigo-50 text-indigo-600 border-indigo-100" :
                        member.role === 'ADMIN' ? "bg-emerald-50 text-emerald-600 border-emerald-100" :
                        "bg-slate-50 text-slate-600 border-slate-100"
                      )}>
                        <Shield className="w-3 h-3" />
                        {member.role}
                      </div>
                    </div>
                    <button className="p-2 text-slate-300 hover:text-slate-600 transition-colors">
                      <MoreVertical className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Permissions Sidebar (Right) */}
        <aside className="space-y-4 sticky top-6">
          {!selectedMember ? (
            <div className="p-8 border border-dashed border-slate-200 rounded-lg flex flex-col items-center justify-center text-center space-y-3 bg-white/50">
              <UserCog className="w-8 h-8 text-slate-300" />
              <p className="text-[12px] text-slate-400 font-medium italic">Sélectionnez un membre pour gérer ses permissions granulaires.</p>
            </div>
          ) : (
            <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden animate-in slide-in-from-right-4 duration-300">
              <div className="p-5 border-b border-slate-100 bg-slate-50/50">
                <div className="flex items-center justify-between mb-1">
                  <h3 className="text-sm font-bold text-slate-900">Permissions Granulaires</h3>
                  <div className="p-1.5 rounded-md bg-white border border-slate-200 shadow-sm">
                    <Settings2 className="w-3.5 h-3.5 text-slate-400" />
                  </div>
                </div>
                <p className="text-[11px] text-slate-500 font-medium">Pour {selectedMember.name}</p>
              </div>

              <div className="p-5 space-y-6">
                
                <CanDo permission={Permission.ORG_MANAGE_MEMBERS}>
                  <div className="space-y-3">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Rôle Global</p>
                    <div className="grid grid-cols-2 gap-2">
                      {['ADMIN', 'MANAGER', 'VIEWER'].map((role) => (
                        <button 
                          key={role}
                          className={cn(
                            "h-9 rounded-lg text-[11px] font-bold border transition-all",
                            selectedMember.role === role 
                              ? "bg-slate-900 text-white border-slate-900" 
                              : "bg-white text-slate-500 border-slate-200 hover:border-slate-300"
                          )}
                        >
                          {role}
                        </button>
                      ))}
                    </div>
                  </div>
                </CanDo>

                {/* Granular Overrides */}
                <div className="space-y-3">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Permissions Spécifiques</p>
                  <div className="space-y-2">
                    <PermissionToggle title="Modifier l'organisation" perms={selectedMember.permissions} code="org:edit" />
                    <PermissionToggle title="Gérer les stocks" perms={selectedMember.permissions} code="inventory:edit" />
                    <PermissionToggle title="Exporter les données" perms={selectedMember.permissions} code="org:export" />
                    <PermissionToggle title="Accès Facturation" perms={selectedMember.permissions} code="org:billing" />
                  </div>
                </div>

                <CanDo permission={Permission.ORG_MANAGE_MEMBERS}>
                  <div className="pt-4 flex flex-col gap-2">
                    <button className="w-full h-10 bg-primary text-white rounded-lg text-[12px] font-bold hover:opacity-90 transition-all flex items-center justify-center gap-2">
                      <Check className="w-4 h-4" />
                      Enregistrer les droits
                    </button>
                    <button className="w-full h-10 border border-red-200 text-red-600 rounded-lg text-[12px] font-bold hover:bg-red-50 transition-all flex items-center justify-center gap-2">
                      <ShieldAlert className="w-4 h-4" />
                      Révoquer l'accès
                    </button>
                  </div>
                </CanDo>
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

function PermissionToggle({ title, perms, code }: any) {
  const isEnabled = perms.includes(code) || perms.includes('all');
  
  return (
    <div className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 hover:border-slate-200 transition-all group">
      <span className="text-[12px] font-medium text-slate-600 group-hover:text-slate-900">{title}</span>
      <div className={cn(
        "w-8 h-4 rounded-full relative transition-all cursor-pointer",
        isEnabled ? "bg-emerald-500" : "bg-slate-200"
      )}>
        <div className={cn(
          "absolute top-0.5 w-3 h-3 rounded-full bg-white transition-all shadow-sm",
          isEnabled ? "left-4.5" : "left-0.5"
        )} />
      </div>
    </div>
  );
}
