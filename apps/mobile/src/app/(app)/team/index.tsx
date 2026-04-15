/**
 * Team Management Screen — Membres + Invitations
 * Persona #3 UI/UX : design épuré, actions rapides, feedback visuel.
 */
import { useQuery, useMutation } from '@apollo/client';
import { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { UserPlus, UserMinus, Shield, Mail, Clock, X, ChevronRight } from 'lucide-react-native';
import { 
  GET_TEAM_DATA, 
  INVITE_MEMBER, 
  REMOVE_MEMBER, 
  UPDATE_MEMBER_ROLE, 
  DELETE_INVITATION 
} from '../../../graphql/queries/getTeamData';

export default function TeamScreen() {
  const { t } = useTranslation();
  const [isInviteModalVisible, setInviteModalVisible] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('viewer');

  const { data, loading, refetch } = useQuery(GET_TEAM_DATA, {
    fetchPolicy: 'cache-and-network',
  });

  const [inviteMutation, { loading: inviting }] = useMutation(INVITE_MEMBER, {
    onCompleted: () => {
      setInviteModalVisible(false);
      setInviteEmail('');
      refetch();
    },
    onError: (err) => Alert.alert('Erreur', err.message),
  });

  const [removeMutation] = useMutation(REMOVE_MEMBER, {
    onCompleted: () => refetch(),
    onError: (err) => Alert.alert('Erreur', err.message),
  });

  const [deleteInviteMutation] = useMutation(DELETE_INVITATION, {
    onCompleted: () => refetch(),
    onError: (err) => Alert.alert('Erreur', err.message),
  });

  const members = data?.organizationMembers ?? [];
  const invitations = data?.pendingInvitations ?? [];
  const isAdmin = data?.me?.isAdmin;

  const handleInvite = () => {
    if (!inviteEmail) return;
    inviteMutation({ variables: { email: inviteEmail, role: inviteRole } });
  };

  const confirmRemove = (userId: string, name: string) => {
    Alert.alert(
      'Supprimer le membre',
      `Êtes-vous sûr de vouloir retirer ${name} de l'organisation ?`,
      [
        { text: 'Annuler', style: 'cancel' },
        { 
          text: 'Retirer', 
          style: 'destructive', 
          onPress: () => removeMutation({ variables: { userId } }) 
        },
      ]
    );
  };

  const renderMember = ({ item }: { item: any }) => {
    const isMe = item.userId === data?.me?.id;
    const roleKey = item.role.toLowerCase();
    
    return (
      <Pressable 
        onPress={() => openMemberDetail(item)} 
        style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
      >
        <View style={styles.memberInfo}>
          <View style={[styles.avatar, isMe && styles.avatarMe]}>
            <Text style={[styles.avatarText, isMe && styles.avatarTextMe]}>
              {(item.user.firstName?.[0] || item.user.email[0]).toUpperCase()}
            </Text>
          </View>
          <View style={styles.nameContainer}>
            <View style={styles.nameRow}>
              <Text style={styles.memberName} numberOfLines={1}>
                {item.user.firstName ? `${item.user.firstName} ${item.user.lastName || ''}` : item.user.email}
              </Text>
              {isMe && (
                <View style={styles.meBadge}>
                  <Text style={styles.meBadgeText}>{t('common.me') || 'Moi'}</Text>
                </View>
              )}
            </View>
            <Text style={styles.memberEmail} numberOfLines={1}>{item.user.email}</Text>
          </View>
        </View>
        
        <View style={styles.cardActions}>
          <View style={[
            styles.roleBadge, 
            roleKey === 'admin' ? styles.roleAdmin : 
            roleKey === 'manager' ? styles.roleManager : 
            styles.roleViewer
          ]}>
            <Shield size={10} color={
              roleKey === 'admin' ? '#7C3AED' : 
              roleKey === 'manager' ? '#F59E0B' : 
              '#64748B'
            } />
            <Text style={[
              styles.roleText, 
              roleKey === 'admin' ? styles.roleTextAdmin : 
              roleKey === 'manager' ? styles.roleTextManager : 
              styles.roleTextViewer
            ]}>
              {item.role.toUpperCase()}
            </Text>
          </View>
          <ChevronRight size={16} color="#CBD5E1" />
        </View>
      </Pressable>
    );
  };

  const renderInvitation = ({ item }: { item: any }) => (
    <View style={[styles.card, styles.invitationCard]}>
      <View style={styles.memberInfo}>
        <View style={[styles.avatar, styles.invitationAvatar]}>
          <Mail size={16} color="#7C3AED" />
        </View>
        <View style={styles.nameContainer}>
          <Text style={styles.memberName} numberOfLines={1}>{item.email}</Text>
          <View style={styles.invitationStatus}>
            <View style={styles.pendingDot} />
            <Text style={styles.invitationDate}>
              {t('team.invitedOn') || 'Invité le'} {new Date(item.createdAt).toLocaleDateString()}
            </Text>
          </View>
        </View>
      </View>
      <View style={styles.cardActions}>
        {isAdmin && (
          <Pressable 
            onPress={() => deleteInviteMutation({ variables: { invitationId: item.id } })} 
            style={styles.deleteActionBtn}
          >
            <X size={16} color="#EF4444" />
          </Pressable>
        )}
      </View>
    </View>
  );

  const openMemberDetail = (member: any) => {
    // Dans une version future, on pourrait ouvrir un panel détail
    // Pour l'instant on utilise l'alerte de suppression si admin
    if (isAdmin && member.userId !== data?.me?.id) {
       confirmRemove(member.userId, member.user.firstName || member.user.email);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Équipe</Text>
          <Text style={styles.subtitle}>{members.length} membres actifs</Text>
        </View>
        {isAdmin && (
          <Pressable onPress={() => setInviteModalVisible(true)} style={styles.inviteBtn}>
            <UserPlus size={20} color="#fff" />
          </Pressable>
        )}
      </View>

      <FlatList
        data={members}
        keyExtractor={(item) => item.userId}
        renderItem={renderMember}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={refetch} tintColor="#7C3AED" />}
        contentContainerStyle={styles.list}
        ListHeaderComponent={() => (
          invitations.length > 0 ? (
            <View style={styles.invitationSection}>
              <Text style={styles.sectionTitle}>Invitations en attente ({invitations.length})</Text>
              {invitations.map((inv: any) => (
                <View key={inv.id}>{renderInvitation({ item: inv })}</View>
              ))}
              <Text style={[styles.sectionTitle, { marginTop: 16 }]}>Membres de l'organisation</Text>
            </View>
          ) : null
        )}
        ListEmptyComponent={
          !loading ? (
            <View style={styles.empty}>
              <Text style={styles.emptyText}>Aucun membre trouvé</Text>
            </View>
          ) : null
        }
      />

      {/* Invite Modal */}
      <Modal animationType="slide" transparent={true} visible={isInviteModalVisible}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Inviter un collaborateur</Text>
              <Pressable onPress={() => setInviteModalVisible(false)}>
                <X size={24} color="#0F172A" />
              </Pressable>
            </View>

            <Text style={styles.label}>Email professionnel</Text>
            <TextInput
              style={styles.input}
              value={inviteEmail}
              onChangeText={setInviteEmail}
              placeholder="camille@michi.app"
              autoCapitalize="none"
              keyboardType="email-address"
            />

            <Text style={styles.label}>Rôle</Text>
            <View style={styles.rolePicker}>
              <Pressable 
                onPress={() => setInviteRole('viewer')}
                style={[styles.roleOption, inviteRole === 'viewer' && styles.roleOptionActive]}
              >
                <Text style={[styles.roleOptionText, inviteRole === 'viewer' && styles.roleOptionTextActive]}>Viewer</Text>
              </Pressable>
              <Pressable 
                onPress={() => setInviteRole('admin')}
                style={[styles.roleOption, inviteRole === 'admin' && styles.roleOptionActive]}
              >
                <Text style={[styles.roleOptionText, inviteRole === 'admin' && styles.roleOptionTextActive]}>Admin</Text>
              </Pressable>
            </View>

            <Pressable 
              onPress={handleInvite} 
              disabled={!inviteEmail || inviting} 
              style={[styles.submitBtn, (!inviteEmail || inviting) && styles.submitBtnDisabled]}
            >
              {inviting ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.submitBtnText}>Envoyer l'invitation</Text>
              )}
            </Pressable>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FAFAFA' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 20, paddingTop: 8, marginBottom: 20 },
  title: { fontSize: 24, fontWeight: '800', color: '#0F172A', letterSpacing: -0.5 },
  subtitle: { fontSize: 13, color: '#64748B', marginTop: 2, fontWeight: '500' },
  inviteBtn: { width: 44, height: 44, borderRadius: 12, backgroundColor: '#7C3AED', alignItems: 'center', justifyContent: 'center', shadowColor: '#7C3AED', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.2, shadowRadius: 8, elevation: 4 },
  list: { paddingHorizontal: 20, paddingBottom: 40 },
  invitationSection: { marginBottom: 12 },
  sectionTitle: { fontSize: 14, fontWeight: '700', color: '#64748B', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 0.5 },
  card: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#fff', borderRadius: 16, padding: 12, marginBottom: 8, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.04, shadowRadius: 4, elevation: 2, borderWidth: 1, borderColor: '#F1F5F9' },
  cardPressed: { backgroundColor: '#F8FAFC', borderColor: '#E2E8F0', transform: [{ scale: 0.98 }] },
  invitationCard: { backgroundColor: '#F8FAFC', borderStyle: 'dashed', borderWidth: 1, borderColor: '#E2E8F0' },
  memberInfo: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  avatar: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#F1F5F9', alignItems: 'center', justifyContent: 'center' },
  avatarMe: { backgroundColor: '#F5F3FF', borderWidth: 1, borderColor: '#DDD6FE' },
  invitationAvatar: { backgroundColor: '#fff' },
  avatarText: { fontSize: 16, fontWeight: '700', color: '#475569' },
  avatarTextMe: { color: '#7C3AED' },
  nameContainer: { marginLeft: 12, flex: 1 },
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  memberName: { fontSize: 14, fontWeight: '700', color: '#0F172A' },
  meBadge: { paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4, backgroundColor: '#7C3AED' },
  meBadgeText: { fontSize: 8, fontWeight: '800', color: '#fff' },
  memberEmail: { fontSize: 12, color: '#64748B', marginTop: 1 },
  invitationStatus: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 4 },
  pendingDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: '#F59E0B' },
  invitationDate: { fontSize: 11, color: '#94A3B8', fontWeight: '500' },
  cardActions: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  roleBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6, backgroundColor: '#F1F5F9' },
  roleAdmin: { backgroundColor: '#F5F3FF' },
  roleManager: { backgroundColor: '#FFFBEB' },
  roleViewer: { backgroundColor: '#F8FAFC' },
  roleText: { fontSize: 10, fontWeight: '700', color: '#64748B' },
  roleTextAdmin: { color: '#7C3AED' },
  roleTextManager: { color: '#B45309' },
  roleTextViewer: { color: '#64748B' },
  actionBtn: { padding: 4 },
  deleteActionBtn: { width: 28, height: 28, borderRadius: 14, backgroundColor: '#FEF2F2', alignItems: 'center', justifyContent: 'center' },
  empty: { alignItems: 'center', paddingVertical: 60 },
  emptyText: { fontSize: 15, color: '#94A3B8', fontWeight: '500' },
  
  // Modal Styles
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
  modalContent: { backgroundColor: '#fff', borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 24, paddingBottom: 40 },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 },
  modalTitle: { fontSize: 20, fontWeight: '800', color: '#0F172A', letterSpacing: -0.5 },
  label: { fontSize: 14, fontWeight: '700', color: '#475569', marginBottom: 8, marginTop: 16 },
  input: { height: 48, backgroundColor: '#F8FAFC', borderRadius: 12, paddingHorizontal: 16, fontSize: 15, color: '#0F172A', borderWidth: 1, borderColor: '#E2E8F0' },
  rolePicker: { flexDirection: 'row', gap: 10, marginTop: 8 },
  roleOption: { flex: 1, height: 44, borderRadius: 12, backgroundColor: '#F8FAFC', alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#E2E8F0' },
  roleOptionActive: { backgroundColor: '#7C3AED', borderColor: '#7C3AED' },
  roleOptionText: { fontSize: 14, fontWeight: '600', color: '#64748B' },
  roleOptionTextActive: { color: '#fff' },
  submitBtn: { height: 52, backgroundColor: '#7C3AED', borderRadius: 16, alignItems: 'center', justifyContent: 'center', marginTop: 32, shadowColor: '#7C3AED', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.2, shadowRadius: 8, elevation: 4 },
  submitBtnDisabled: { backgroundColor: '#C4B5FD', shadowOpacity: 0 },
  submitBtnText: { fontSize: 16, fontWeight: '700', color: '#fff' },
});
