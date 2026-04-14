/**
 * Inventory Screen — liste complète des produits avec filtrage
 */
import { useQuery } from '@apollo/client';
import { useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { GET_PRODUCTS } from '../../../graphql/queries/getProducts';

export default function InventoryScreen() {
  const [search, setSearch] = useState('');
  const { data, loading, refetch } = useQuery(GET_PRODUCTS, {
    fetchPolicy: 'cache-and-network',
  });

  const products = (data?.products ?? []).filter((p) =>
    p.title.toLowerCase().includes(search.toLowerCase()) ||
    p.sku.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Inventaire</Text>
        <Text style={styles.count}>{products.length} produit{products.length !== 1 ? 's' : ''}</Text>
      </View>

      <TextInput
        style={styles.searchInput}
        value={search}
        onChangeText={setSearch}
        placeholder="Rechercher par SKU ou titre…"
        placeholderTextColor="#94A3B8"
        clearButtonMode="while-editing"
      />

      {loading ? (
        <ActivityIndicator style={styles.loader} size="large" color="#7C3AED" />
      ) : (
        <FlatList
          data={products}
          keyExtractor={(item) => item.id}
          onRefresh={refetch}
          refreshing={loading}
          contentContainerStyle={styles.list}
          renderItem={({ item }) => {
            const days = item.prediction?.daysOfStock ?? null;
            const isRed = days !== null && days !== undefined && days <= 0;
            const isAmber = days !== null && days !== undefined && days > 0 && days <= 14;
            return (
              <View style={styles.row}>
                <View style={styles.rowLeft}>
                  <Text style={styles.sku}>{item.sku}</Text>
                  <Text style={styles.titleText} numberOfLines={2}>{item.title}</Text>
                </View>
                <View style={styles.rowRight}>
                  <Text style={styles.stock}>{item.currentStock} u.</Text>
                  {days !== null && days !== undefined && (
                    <View style={[styles.pill, isRed ? styles.pillRed : isAmber ? styles.pillAmber : styles.pillGreen]}>
                      <Text style={styles.pillText}>
                        {isRed ? 'Rupture' : `${Math.round(days)}j`}
                      </Text>
                    </View>
                  )}
                </View>
              </View>
            );
          }}
          ListEmptyComponent={
            <View style={styles.empty}>
              <Text style={styles.emptyText}>Aucun produit trouvé</Text>
            </View>
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FAFAFA' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 20, paddingTop: 8, paddingBottom: 12 },
  title: { fontSize: 22, fontWeight: '700', color: '#0F172A' },
  count: { fontSize: 13, color: '#64748B' },
  searchInput: { marginHorizontal: 20, marginBottom: 12, height: 44, backgroundColor: '#fff', borderWidth: 1, borderColor: '#E2E8F0', borderRadius: 10, paddingHorizontal: 14, fontSize: 14, color: '#0F172A' },
  loader: { flex: 1 },
  list: { paddingHorizontal: 20, paddingBottom: 24, gap: 0 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#fff', borderRadius: 10, padding: 14, marginBottom: 8, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.04, shadowRadius: 3, elevation: 1 },
  rowLeft: { flex: 1, marginRight: 12 },
  sku: { fontSize: 11, color: '#7C3AED', fontWeight: '600', textTransform: 'uppercase', letterSpacing: 0.5 },
  titleText: { fontSize: 14, color: '#0F172A', fontWeight: '500', marginTop: 2 },
  rowRight: { alignItems: 'flex-end', gap: 6 },
  stock: { fontSize: 13, fontWeight: '600', color: '#374151' },
  pill: { borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3 },
  pillRed: { backgroundColor: '#FEE2E2' },
  pillAmber: { backgroundColor: '#FEF3C7' },
  pillGreen: { backgroundColor: '#D1FAE5' },
  pillText: { fontSize: 11, fontWeight: '600', color: '#374151' },
  empty: { alignItems: 'center', paddingVertical: 48 },
  emptyText: { fontSize: 15, color: '#94A3B8' },
});
