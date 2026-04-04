/**
 * Dashboard Page
 */
'use client';

import { useQuery } from '@apollo/client';
import { useRouter } from 'next/navigation';
import { GET_ME } from '@/graphql/queries/getMe';
import { useEffect } from 'react';

export default function DashboardPage() {
  const router = useRouter();
  const { data, loading, error } = useQuery(GET_ME);
  
  useEffect(() => {
    // Si pas de token, rediriger vers login
    if (typeof window !== 'undefined' && !localStorage.getItem('michi_token')) {
      router.push('/login');
    }
  }, [router]);
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600">Erreur : {error.message}</p>
          <button
            onClick={() => router.push('/login')}
            className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg"
          >
            Retour au login
          </button>
        </div>
      </div>
    );
  }
  
  const user = data?.me;
  
  const handleLogout = () => {
    localStorage.removeItem('michi_token');
    router.push('/login');
  };
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-light">
                <span className="font-serif text-purple-600">道</span> MICHI
              </h1>
            </div>
            
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Déconnexion
              </button>
            </div>
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-semibold text-gray-900">📊 Dashboard</h2>
          <p className="mt-1 text-sm text-gray-600">
            Bienvenue sur votre tableau de bord Michi
          </p>
        </div>
        
        {/* Coming Soon Card */}
        <div className="bg-white rounded-xl shadow-sm p-8 text-center">
          <div className="max-w-md mx-auto">
            <div className="text-6xl mb-4">🚧</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Dashboard en construction
            </h3>
            <p className="text-gray-600 mb-6">
              Le tableau de bord complet avec KPIs et liste de produits arrive bientôt !
            </p>
            
            <div className="bg-purple-50 rounded-lg p-4 text-left">
              <p className="text-sm font-medium text-purple-900 mb-2">✅ Fonctionnalités actuelles :</p>
              <ul className="text-sm text-purple-700 space-y-1">
                <li>• Authentification JWT</li>
                <li>• GraphQL API fonctionnel</li>
                <li>• Base de données PostgreSQL</li>
              </ul>
              
              <p className="text-sm font-medium text-purple-900 mt-4 mb-2">🔜 Prochainement :</p>
              <ul className="text-sm text-purple-700 space-y-1">
                <li>• Liste des produits</li>
                <li>• Prédictions de rupture</li>
                <li>• Recommandations de commande</li>
              </ul>
            </div>
          </div>
        </div>
        
        {/* User Info Card */}
        <div className="mt-6 bg-white rounded-xl shadow-sm p-6">
          <h4 className="font-semibold text-gray-900 mb-4">Informations utilisateur</h4>
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">Email</dt>
              <dd className="mt-1 text-sm text-gray-900">{user?.email}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">User ID</dt>
              <dd className="mt-1 text-sm text-gray-900 font-mono">{user?.id}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Shop ID</dt>
              <dd className="mt-1 text-sm text-gray-900 font-mono">{user?.shopId}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Créé le</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {new Date(user?.createdAt).toLocaleDateString('fr-FR')}
              </dd>
            </div>
          </dl>
        </div>
      </main>
    </div>
  );
}
