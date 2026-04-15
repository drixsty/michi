/**
 * Dashboard Screen — KPIs + alertes rapides
 * Persona #3 UI/UX : cards mobile-first, touch targets 44×44px.
 */
import { useQuery } from '@apollo/client';
import { router } from 'expo-router';
import { useState, useMemo } from 'react';
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { clearToken } from '../../../graphql/client';
import { GET_ME } from '../../../graphql/queries/getMe';
import { GET_PRODUCTS } from '../../../graphql/queries/getProducts';
import { FINANCIAL_OVERVIEW } from '../../../graphql/queries/financialOverview';
import { GET_TEAM_DATA } from '../../../graphql/queries/getTeamData';
import { TrendingDown, Wallet, Box, AlertCircle } from 'lucide-react-native';

const { width } = Dimensions.get('window');

interface Product {
  id: string;
  sku: string;
  title: string;
  currentStock: number;
  stockWeight?: number;
  prediction?: {
    daysOfStock?: number;
    runRate?: number;
  };
}

export default function DashboardScreen() {
  const { t } = useTranslation();
  const [selectedStoreId, setSelectedStoreId] = useState<string | null>(null);

  const { data: meData, loading: meLoading } = useQuery(GET_ME);
  const { data: teamData } = useQuery(GET_TEAM_DATA);
  
  const {
    data: productsData,
    loading: productsLoading,
    refetch: refetchProducts,
  } = useQuery(GET_PRODUCTS, { 
    variables: { storeId: selectedStoreId },
    fetchPolicy: 'cache-and-network' 
  });

  const {
    data: financialData,
    loading: financialLoading,
    refetch: refetchFinancial,
  } = useQuery(FINANCIAL_OVERVIEW, {
    variables: { storeId: selectedStoreId },
    fetchPolicy: 'cache-and-network'
  });

  const products = (productsData?.products ?? []) as Product[];
  const user = meData?.me;
  const stores = teamData?.currentOrganization?.stores ?? [];
  const finance = financialData?.financialOverview;

  const totalProducts = products.length;
  const stockouts = products.filter((p: Product) => (p.prediction?.daysOfStock ?? Infinity) <= 0).length;
  const urgent = products.filter((p: Product) => {
    const days = p.prediction?.daysOfStock ?? null;
    return days !== null && days !== undefined && days > 0 && days <= 14;
  }).length;

  const onRefresh = () => {
    refetchProducts();
    refetchFinancial();
  };

  const formatCurrency = (val: number) => {
    const currency = finance?.currency || '€';
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: currency === '€' ? 'EUR' : currency === '$' ? 'USD' : 'EUR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  const handleLogout = async () => {
    await clearToken();
    router.replace('/(auth)/login');
  };

  if (meLoading && !user) {
    return (
      <SafeAreaView style={styles.center}>
        <ActivityIndicator size="large" color="#7C3AED" />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        refreshControl={
          <RefreshControl refreshing={productsLoading || financialLoading} onRefresh={onRefresh} tintColor="#7C3AED" />
        }
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>
              {t('dashboard.greeting')}{user?.firstName ? `, ${user.firstName}` : ''} 👋
            </Text>
            <Text style={styles.subGreeting}>{t('dashboard.subtitle')}</Text>
          </View>
          <Pressable onPress={handleLogout} style={styles.logoutBtn}>
            <Text style={styles.logoutText}>{t('dashboard.logout')}</Text>
          </Pressable>
        </View>

        {/* Store Selector */}
        <View style={styles.storeSelectorContainer}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.storeScroll}>
            <Pressable 
              onPress={() => setSelectedStoreId(null)}
              style={({ pressed }) => [
                styles.storeChip, 
                !selectedStoreId && styles.storeChipActive,
                pressed && { opacity: 0.7 }
              ]}
            >
              <Text style={[styles.storeChipText, !selectedStoreId && styles.storeChipTextActive]}>
                {t('common.allChannels') || 'Omnicanal'}
              </Text>
            </Pressable>
            {stores.map((store: any) => (
              <Pressable
                key={store.id}
                onPress={() => setSelectedStoreId(store.id)}
                style={({ pressed }) => [
                  styles.storeChip, 
                  selectedStoreId === store.id && styles.storeChipActive,
                  pressed && { opacity: 0.7 }
                ]}
              >
                <Text style={[styles.storeChipText, selectedStoreId === store.id && styles.storeChipTextActive]}>
                  {store.name}
                </Text>
              </Pressable>
            ))}
          </ScrollView>
        </View>

        {/* Primary KPIs (Financials) */}
        <View style={styles.financialRow}>
          <FinancialCard 
            label={t('dashboard.financials.inventoryValue') || 'Valeur Stock'} 
            value={formatCurrency(finance?.inventoryValue || 0)} 
            icon={<Wallet size={20} color="#7C3AED" />}
            color="#7C3AED"
            loading={financialLoading}
          />
          <FinancialCard 
            label={t('dashboard.financials.revenueAtRisk') || 'Risque Revenu'} 
            value={formatCurrency(finance?.revenueAtRisk || 0)} 
            icon={<TrendingDown size={20} color="#EF4444" />}
            color="#EF4444"
            loading={financialLoading}
          />
        </View>

        {/* Secondary KPIs (Volumes) */}
        <View style={styles.kpiRow}>
          <KpiCard label={t('dashboard.kpi.products')} value={totalProducts} color="#64748B" icon={<Box size={14} color="#64748B" />} />
          <KpiCard label={t('dashboard.kpi.stockouts')} value={stockouts} color="#EF4444" icon={<AlertCircle size={14} color="#EF4444" />} />
          <KpiCard label={t('dashboard.kpi.urgent')} value={urgent} color="#F59E0B" icon={<ActivityIndicator size={10} color="#F59E0B" />} />
        </View>

        {/* Product List (top 10) */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>{t('dashboard.recentProducts')}</Text>
          <Pressable onPress={() => router.push('/inventory/index')}>
            <Text style={styles.viewAllText}>{t('common.viewAll') || 'Voir tout'}</Text>
          </Pressable>
        </View>

        {products.slice(0, 10).map((product: Product) => {
          const days = product.prediction?.daysOfStock;
          const isRed = days !== null && days !== undefined && days <= 0;
          const isAmber = days !== null && days !== undefined && days > 0 && days <= 14;
          const importance = product.stockWeight || 0;

          return (
            <View key={product.id} style={styles.productCard}>
              <View style={styles.productInfo}>
                <View style={styles.skuRow}>
                  <Text style={styles.productSku}>{product.sku}</Text>
                  {importance > 0.5 && (
                    <View style={styles.impactBadge}>
                      <Text style={styles.impactBadgeText}>Top Impact</Text>
                    </View>
                  )}
                </View>
                <Text style={styles.productTitle} numberOfLines={1}>
                  {product.title}
                </Text>
              </View>
              <View style={styles.productMeta}>
                <Text style={styles.stockText}>{product.currentStock} u.</Text>
                {days !== null && days !== undefined && (
                  <View style={[styles.badge, isRed ? styles.badgeRed : isAmber ? styles.badgeAmber : styles.badgeGreen]}>
                    <Text style={styles.badgeText}>
                      {isRed ? t('dashboard.stockout') : `${Math.round(days)}j`}
                    </Text>
                  </View>
                )}
              </View>
            </View>
          );
        })}

        {products.length === 0 && !productsLoading && (
          <View style={styles.empty}>
            <Text style={styles.emptyText}>{t('dashboard.empty')}</Text>
            <Text style={styles.emptySubText}>{t('dashboard.emptySub')}</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function FinancialCard({ label, value, icon, color, loading }: { label: string; value: string; icon: React.ReactNode; color: string; loading?: boolean }) {
  return (
    <View style={styles.finCard}>
      <View style={[styles.finIconContainer, { backgroundColor: `${color}10` }]}>
        {icon}
      </View>
      <Text style={styles.finLabel}>{label}</Text>
      {loading ? (
        <ActivityIndicator size="small" color={color} style={{ height: 26, alignSelf: 'flex-start' }} />
      ) : (
        <Text style={[styles.finValue, { color }]}>{value}</Text>
      )}
    </View>
  );
}

function KpiCard({ label, value, color, icon }: { label: string; value: number; color: string; icon: React.ReactNode }) {
  return (
    <View style={styles.kpiCard}>
      <View style={styles.kpiHeader}>
        {icon}
        <Text style={[styles.kpiValue, { color }]}>{value}</Text>
      </View>
      <Text style={styles.kpiLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FAFAFA' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FAFAFA' },
  scroll: { padding: 20, paddingBottom: 40 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 },
  greeting: { fontSize: 24, fontWeight: '800', color: '#0F172A', letterSpacing: -0.5 },
  subGreeting: { fontSize: 13, color: '#64748B', marginTop: 2, fontWeight: '500' },
  logoutBtn: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 8, backgroundColor: '#FEF2F2' },
  logoutText: { fontSize: 11, color: '#EF4444', fontWeight: '700' },
  
  storeSelectorContainer: { marginBottom: 24, marginHorizontal: -20 },
  storeScroll: { paddingHorizontal: 20, gap: 8 },
  storeChip: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20, backgroundColor: '#fff', borderWidth: 1, borderColor: '#E2E8F0' },
  storeChipActive: { backgroundColor: '#7C3AED', borderColor: '#7C3AED' },
  storeChipText: { fontSize: 13, color: '#64748B', fontWeight: '600' },
  storeChipTextActive: { color: '#fff' },

  financialRow: { flexDirection: 'row', gap: 12, marginBottom: 20 },
  finCard: { flex: 1, backgroundColor: '#fff', borderRadius: 16, padding: 16, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.05, shadowRadius: 8, elevation: 3 },
  finIconContainer: { width: 36, height: 36, borderRadius: 10, alignItems: 'center', justifyContent: 'center', marginBottom: 12 },
  finLabel: { fontSize: 11, color: '#64748B', fontWeight: '600', marginBottom: 4 },
  finValue: { fontSize: 18, fontWeight: '800', letterSpacing: -0.5 },

  kpiRow: { flexDirection: 'row', gap: 10, marginBottom: 28 },
  kpiCard: { flex: 1, backgroundColor: '#F8FAFC', borderRadius: 12, padding: 12, borderWidth: 1, borderColor: '#F1F5F9' },
  kpiHeader: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 4 },
  kpiValue: { fontSize: 16, fontWeight: '700' },
  kpiLabel: { fontSize: 10, color: '#64748B', fontWeight: '600' },

  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  sectionTitle: { fontSize: 18, fontWeight: '700', color: '#0F172A' },
  viewAllText: { fontSize: 13, color: '#7C3AED', fontWeight: '600' },

  productCard: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#fff', borderRadius: 16, padding: 16, marginBottom: 10, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.04, shadowRadius: 4, elevation: 2 },
  productInfo: { flex: 1, marginRight: 12 },
  skuRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 4 },
  productSku: { fontSize: 10, color: '#7C3AED', fontWeight: '700', textTransform: 'uppercase', letterSpacing: 1 },
  impactBadge: { paddingHorizontal: 6, paddingVertical: 2, backgroundColor: '#F59E0B', borderRadius: 4 },
  impactBadgeText: { fontSize: 8, color: '#fff', fontWeight: '900', textTransform: 'uppercase' },
  productTitle: { fontSize: 14, color: '#0F172A', fontWeight: '600' },
  productMeta: { alignItems: 'flex-end', gap: 6 },
  stockText: { fontSize: 13, fontWeight: '700', color: '#1E293B' },
  badge: { borderRadius: 8, paddingHorizontal: 10, paddingVertical: 4 },
  badgeRed: { backgroundColor: '#FEE2E2' },
  badgeAmber: { backgroundColor: '#FEF3C7' },
  badgeGreen: { backgroundColor: '#D1FAE5' },
  badgeText: { fontSize: 10, fontWeight: '700', color: '#1E293B' },
  
  empty: { alignItems: 'center', paddingVertical: 60 },
  emptyText: { fontSize: 16, fontWeight: '700', color: '#1E293B' },
  emptySubText: { fontSize: 13, color: '#94A3B8', marginTop: 8, textAlign: 'center', paddingHorizontal: 40 },
});
