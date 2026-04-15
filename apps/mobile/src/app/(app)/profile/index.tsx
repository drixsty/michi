/**
 * Profile Screen — infos utilisateur + déconnexion
 */
import { useQuery } from '@apollo/client';
import { router } from 'expo-router';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { clearToken } from '../../../graphql/client';
import { GET_ME } from '../../../graphql/queries/getMe';

export default function ProfileScreen() {
  const { t } = useTranslation();
  const { data, loading } = useQuery(GET_ME);
  const user = data?.me;

  const handleLogout = async () => {
    await clearToken();
    router.replace('/(auth)/login');
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.center}>
        <ActivityIndicator size="large" color="#7C3AED" />
      </SafeAreaView>
    );
  }

  const orgCount = user?.organizations?.length ?? 0;
  const orgLabel = orgCount !== 1 ? t('profile.organisations') : t('profile.organisation');

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.title}>{t('profile.title')}</Text>

        {/* Avatar */}
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>
            {(user?.firstName?.[0] ?? user?.email?.[0] ?? '?').toUpperCase()}
          </Text>
        </View>

        <Text style={styles.name}>
          {user?.firstName && user?.lastName
            ? `${user.firstName} ${user.lastName}`
            : user?.email ?? '—'}
        </Text>
        <Text style={styles.email}>{user?.email ?? '—'}</Text>

        {/* Info rows */}
        <View style={styles.section}>
          <InfoRow label={t('profile.email')} value={user?.email ?? '—'} />
          <InfoRow
            label={t('profile.organizations')}
            value={`${orgCount} ${orgLabel}`}
          />
          <InfoRow
            label={t('profile.createdAt')}
            value={
              user?.createdAt
                ? new Date(user.createdAt).toLocaleDateString('fr-FR')
                : '—'
            }
          />
        </View>

        {/* Logout */}
        <Pressable
          onPress={handleLogout}
          style={({ pressed }) => [styles.logoutBtn, pressed && styles.logoutBtnPressed]}
        >
          <Text style={styles.logoutText}>{t('profile.logout')}</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FAFAFA' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FAFAFA' },
  scroll: { padding: 24, alignItems: 'center' },
  title: { fontSize: 22, fontWeight: '700', color: '#0F172A', alignSelf: 'flex-start', marginBottom: 24 },
  avatar: { width: 72, height: 72, borderRadius: 36, backgroundColor: '#EDE9FE', alignItems: 'center', justifyContent: 'center', marginBottom: 16 },
  avatarText: { fontSize: 28, fontWeight: '700', color: '#7C3AED' },
  name: { fontSize: 20, fontWeight: '700', color: '#0F172A' },
  email: { fontSize: 14, color: '#64748B', marginTop: 4 },
  section: { width: '100%', backgroundColor: '#fff', borderRadius: 12, padding: 4, marginTop: 28, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.06, shadowRadius: 4, elevation: 2 },
  infoRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: '#F1F5F9' },
  infoLabel: { fontSize: 14, color: '#64748B' },
  infoValue: { fontSize: 14, fontWeight: '500', color: '#0F172A', textAlign: 'right', flex: 1, marginLeft: 16 },
  logoutBtn: { marginTop: 32, width: '100%', height: 50, backgroundColor: '#FEF2F2', borderRadius: 12, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#FEE2E2' },
  logoutBtnPressed: { opacity: 0.7 },
  logoutText: { fontSize: 16, fontWeight: '600', color: '#EF4444' },
});
