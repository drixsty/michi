/**
 * Dashboard Screen — KPIs + alertes rapides
 * Persona #3 UI/UX : cards mobile-first, touch targets 44×44px.
 */
import { useQuery } from '@apollo/client';
import { router } from 'expo-router';
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { clearToken } from '../../../graphql/client';
import { GET_ME } from '../../../graphql/queries/getMe';
import { GET_PRODUCTS } from '../../../graphql/queries/getProducts';

export default function DashboardScreen() {
  const { t } = useTranslation();
  const { data: meData, loading: meLoading } = useQuery(GET_ME);
  const {
    data: productsData,
    loading: productsLoading,
    refetch,
  } = useQuery(GET_PRODUCTS, { fetchPolicy: 'cache-and-network' });

  const products = productsData?.products ?? [];
  const user = meData?.me;

  const totalProducts = products.length;
  const stockouts = products.filter((p) => (p.prediction?.daysOfStock ?? Infinity) <= 0).length;
  const urgent = products.filter((p) => {
    const days = p.prediction?.daysOfStock ?? null;
    return days !== null && days !== undefined && days > 0 && days <= 14;
  }).length;

  const handleLogout = async () => {
    await clearToken();
    router.replace('/(auth)/login');
  };

  if (meLoading || productsLoading) {
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
          <RefreshControl refreshing={productsLoading} onRefresh={refetch} tintColor="#7C3AED" />
        }
        contentContainerStyle={styles.scroll}
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

        {/* KPI Cards */}
        <View style={styles.kpiRow}>
          <KpiCard label={t('dashboard.kpi.products')} value={totalProducts} color="#7C3AED" />
          <KpiCard label={t('dashboard.kpi.stockouts')} value={stockouts} color="#EF4444" />
          <KpiCard label={t('dashboard.kpi.urgent')} value={urgent} color="#F59E0B" />
        </View>

        {/* Product List (top 10) */}
        <Text style={styles.sectionTitle}>{t('dashboard.recentProducts')}</Text>
        {products.slice(0, 10).map((product) => {
          const days = product.prediction?.daysOfStock;
          const isRed = days !== null && days !== undefined && days <= 0;
          const isAmber = days !== null && days !== undefined && days > 0 && days <= 14;

          return (
            <View key={product.id} style={styles.productCard}>
              <View style={styles.productInfo}>
                <Text style={styles.productSku} numberOfLines={1}>
                  {product.sku}
                </Text>
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

        {products.length === 0 && (
          <View style={styles.empty}>
            <Text style={styles.emptyText}>{t('dashboard.empty')}</Text>
            <Text style={styles.emptySubText}>{t('dashboard.emptySub')}</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function KpiCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <View style={[styles.kpiCard, { borderLeftColor: color }]}>
      <Text style={[styles.kpiValue, { color }]}>{value}</Text>
      <Text style={styles.kpiLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FAFAFA' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FAFAFA' },
  scroll: { padding: 20, gap: 0 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 },
  greeting: { fontSize: 22, fontWeight: '700', color: '#0F172A' },
  subGreeting: { fontSize: 13, color: '#64748B', marginTop: 2 },
  logoutBtn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8, backgroundColor: '#FEF2F2' },
  logoutText: { fontSize: 12, color: '#EF4444', fontWeight: '600' },
  kpiRow: { flexDirection: 'row', gap: 10, marginBottom: 28 },
  kpiCard: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 14,
    borderLeftWidth: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  kpiValue: { fontSize: 24, fontWeight: '700', lineHeight: 28 },
  kpiLabel: { fontSize: 11, color: '#64748B', marginTop: 4, fontWeight: '500' },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: '#0F172A', marginBottom: 12 },
  productCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 14,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 1,
  },
  productInfo: { flex: 1, marginRight: 12 },
  productSku: { fontSize: 11, color: '#7C3AED', fontWeight: '600', textTransform: 'uppercase', letterSpacing: 0.5 },
  productTitle: { fontSize: 14, color: '#0F172A', fontWeight: '500', marginTop: 2 },
  productMeta: { alignItems: 'flex-end', gap: 6 },
  stockText: { fontSize: 13, fontWeight: '600', color: '#374151' },
  badge: { borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3 },
  badgeRed: { backgroundColor: '#FEE2E2' },
  badgeAmber: { backgroundColor: '#FEF3C7' },
  badgeGreen: { backgroundColor: '#D1FAE5' },
  badgeText: { fontSize: 11, fontWeight: '600', color: '#374151' },
  empty: { alignItems: 'center', paddingVertical: 48 },
  emptyText: { fontSize: 16, fontWeight: '600', color: '#374151' },
  emptySubText: { fontSize: 13, color: '#94A3B8', marginTop: 8, textAlign: 'center' },
});
