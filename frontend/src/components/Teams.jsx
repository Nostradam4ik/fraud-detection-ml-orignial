import { useState, useEffect } from 'react';
import {
  Users,
  Plus,
  Settings,
  Trash2,
  UserPlus,
  Crown,
  Shield,
  Eye,
  X,
  Check,
  Mail,
  MoreVertical,
  ChevronRight,
  Building2,
  AlertTriangle
} from 'lucide-react';
import {
  getTeams,
  createTeam,
  getTeamDetails,
  inviteToTeam,
  removeTeamMember,
  updateMemberRole,
  leaveTeam,
  deleteTeam
} from '../services/api';

export default function Teams({ user }) {
  const [teams, setTeams] = useState([]);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState(null);

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showMemberMenu, setShowMemberMenu] = useState(null);

  // Forms
  const [newTeamName, setNewTeamName] = useState('');
  const [newTeamDesc, setNewTeamDesc] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('viewer');

  useEffect(() => {
    loadTeams();
  }, []);

  const showMsg = (text, type = 'success') => {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 5000);
  };

  const loadTeams = async () => {
    setLoading(true);
    try {
      const data = await getTeams();
      setTeams(data);
      if (data.length > 0 && !selectedTeam) {
        loadTeamDetails(data[0].id);
      }
    } catch (error) {
      console.error('Failed to load teams:', error);
    }
    setLoading(false);
  };

  const loadTeamDetails = async (teamId) => {
    try {
      const data = await getTeamDetails(teamId);
      setSelectedTeam(data);
    } catch (error) {
      console.error('Failed to load team details:', error);
    }
  };

  const handleCreateTeam = async (e) => {
    e.preventDefault();
    try {
      const team = await createTeam({ name: newTeamName, description: newTeamDesc });
      showMsg('Team created successfully');
      setShowCreateModal(false);
      setNewTeamName('');
      setNewTeamDesc('');
      loadTeams();
      loadTeamDetails(team.id);
    } catch (error) {
      showMsg(error.response?.data?.detail || 'Failed to create team', 'error');
    }
  };

  const handleInvite = async (e) => {
    e.preventDefault();
    if (!selectedTeam) return;
    try {
      await inviteToTeam(selectedTeam.id, { email: inviteEmail, role: inviteRole });
      showMsg('Invitation sent successfully');
      setShowInviteModal(false);
      setInviteEmail('');
      setInviteRole('viewer');
      loadTeamDetails(selectedTeam.id);
    } catch (error) {
      showMsg(error.response?.data?.detail || 'Failed to send invitation', 'error');
    }
  };

  const handleRemoveMember = async (memberId) => {
    if (!selectedTeam) return;
    if (!confirm('Are you sure you want to remove this member?')) return;
    try {
      await removeTeamMember(selectedTeam.id, memberId);
      showMsg('Member removed');
      loadTeamDetails(selectedTeam.id);
    } catch (error) {
      showMsg(error.response?.data?.detail || 'Failed to remove member', 'error');
    }
    setShowMemberMenu(null);
  };

  const handleUpdateRole = async (memberId, newRole) => {
    if (!selectedTeam) return;
    try {
      await updateMemberRole(selectedTeam.id, memberId, newRole);
      showMsg('Role updated');
      loadTeamDetails(selectedTeam.id);
    } catch (error) {
      showMsg(error.response?.data?.detail || 'Failed to update role', 'error');
    }
    setShowMemberMenu(null);
  };

  const handleLeaveTeam = async () => {
    if (!selectedTeam) return;
    if (!confirm('Are you sure you want to leave this team?')) return;
    try {
      await leaveTeam(selectedTeam.id);
      showMsg('You left the team');
      setSelectedTeam(null);
      loadTeams();
    } catch (error) {
      showMsg(error.response?.data?.detail || 'Failed to leave team', 'error');
    }
  };

  const handleDeleteTeam = async () => {
    if (!selectedTeam) return;
    if (!confirm('Are you sure you want to delete this team? This action cannot be undone.')) return;
    try {
      await deleteTeam(selectedTeam.id);
      showMsg('Team deleted');
      setSelectedTeam(null);
      loadTeams();
    } catch (error) {
      showMsg(error.response?.data?.detail || 'Failed to delete team', 'error');
    }
  };

  const getRoleIcon = (role) => {
    switch (role) {
      case 'owner': return <Crown className="w-4 h-4 text-yellow-500" />;
      case 'admin': return <Shield className="w-4 h-4 text-purple-500" />;
      default: return <Eye className="w-4 h-4 text-gray-400" />;
    }
  };

  const getRoleBadge = (role) => {
    const styles = {
      owner: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
      admin: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400',
      analyst: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
      viewer: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-400'
    };
    return styles[role] || styles.viewer;
  };

  const isTeamOwner = selectedTeam?.members?.find(m => m.user_id === user?.id)?.role === 'owner';
  const isTeamAdmin = ['owner', 'admin'].includes(selectedTeam?.members?.find(m => m.user_id === user?.id)?.role);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Teams</h1>
          <p className="text-gray-600 dark:text-gray-400">Collaborate with your team members</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Create Team
        </button>
      </div>

      {/* Message */}
      {message && (
        <div className={`p-4 rounded-lg flex items-center gap-2 ${
          message.type === 'error'
            ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
            : 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
        }`}>
          {message.type === 'error' ? <AlertTriangle className="w-5 h-5" /> : <Check className="w-5 h-5" />}
          {message.text}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Teams List */}
        <div className="lg:col-span-1 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="font-semibold text-gray-900 dark:text-white">Your Teams</h2>
          </div>

          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            </div>
          ) : teams.length === 0 ? (
            <div className="p-8 text-center text-gray-500 dark:text-gray-400">
              <Building2 className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>You're not part of any team yet</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="mt-4 text-blue-600 dark:text-blue-400 hover:underline"
              >
                Create your first team
              </button>
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {teams.map(team => (
                <button
                  key={team.id}
                  onClick={() => loadTeamDetails(team.id)}
                  className={`w-full p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors flex items-center justify-between ${
                    selectedTeam?.id === team.id ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold">
                      {team.name[0].toUpperCase()}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{team.name}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {team.member_count} member{team.member_count !== 1 ? 's' : ''}
                      </p>
                    </div>
                  </div>
                  <ChevronRight className={`w-5 h-5 text-gray-400 ${selectedTeam?.id === team.id ? 'text-blue-600' : ''}`} />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Team Details */}
        <div className="lg:col-span-2">
          {selectedTeam ? (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
              {/* Team Header */}
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-4">
                    <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center text-white text-2xl font-bold">
                      {selectedTeam.name[0].toUpperCase()}
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-gray-900 dark:text-white">{selectedTeam.name}</h2>
                      <p className="text-gray-600 dark:text-gray-400">{selectedTeam.description || 'No description'}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
                        Created {new Date(selectedTeam.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {isTeamAdmin && (
                      <button
                        onClick={() => setShowInviteModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        <UserPlus className="w-4 h-4" />
                        Invite
                      </button>
                    )}
                    {isTeamOwner ? (
                      <button
                        onClick={handleDeleteTeam}
                        className="p-2 text-red-600 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-colors"
                        title="Delete team"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    ) : (
                      <button
                        onClick={handleLeaveTeam}
                        className="px-4 py-2 text-red-600 border border-red-300 dark:border-red-700 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                      >
                        Leave Team
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Members List */}
              <div className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Members ({selectedTeam.members?.length || 0})
                </h3>
                <div className="space-y-3">
                  {selectedTeam.members?.map(member => (
                    <div
                      key={member.user_id}
                      className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-medium">
                          {member.username[0].toUpperCase()}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-gray-900 dark:text-white">{member.username}</span>
                            {member.user_id === user?.id && (
                              <span className="text-xs text-gray-500 dark:text-gray-400">(You)</span>
                            )}
                          </div>
                          <span className="text-sm text-gray-500 dark:text-gray-400">{member.email}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getRoleBadge(member.role)}`}>
                          {getRoleIcon(member.role)}
                          {member.role}
                        </span>

                        {isTeamAdmin && member.user_id !== user?.id && member.role !== 'owner' && (
                          <div className="relative">
                            <button
                              onClick={() => setShowMemberMenu(showMemberMenu === member.user_id ? null : member.user_id)}
                              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
                            >
                              <MoreVertical className="w-4 h-4" />
                            </button>

                            {showMemberMenu === member.user_id && (
                              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-10">
                                <button
                                  onClick={() => handleUpdateRole(member.user_id, 'admin')}
                                  className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                                >
                                  <Shield className="w-4 h-4" />
                                  Make Admin
                                </button>
                                <button
                                  onClick={() => handleUpdateRole(member.user_id, 'analyst')}
                                  className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                                >
                                  <Users className="w-4 h-4" />
                                  Make Analyst
                                </button>
                                <button
                                  onClick={() => handleUpdateRole(member.user_id, 'viewer')}
                                  className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                                >
                                  <Eye className="w-4 h-4" />
                                  Make Viewer
                                </button>
                                <hr className="my-1 border-gray-200 dark:border-gray-700" />
                                <button
                                  onClick={() => handleRemoveMember(member.user_id)}
                                  className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2"
                                >
                                  <Trash2 className="w-4 h-4" />
                                  Remove
                                </button>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-12 text-center">
              <Users className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Select a team</h3>
              <p className="text-gray-500 dark:text-gray-400">Choose a team from the list to view details</p>
            </div>
          )}
        </div>
      </div>

      {/* Create Team Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md mx-4">
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Create New Team</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreateTeam} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Team Name *
                </label>
                <input
                  type="text"
                  value={newTeamName}
                  onChange={(e) => setNewTeamName(e.target.value)}
                  required
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                  placeholder="Engineering Team"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Description
                </label>
                <textarea
                  value={newTeamDesc}
                  onChange={(e) => setNewTeamDesc(e.target.value)}
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                  placeholder="Team description..."
                />
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Create Team
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Invite Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md mx-4">
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Invite Member</h3>
              <button
                onClick={() => setShowInviteModal(false)}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleInvite} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Email Address *
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    required
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                    placeholder="colleague@example.com"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Role
                </label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                >
                  <option value="viewer">Viewer - Can view team data</option>
                  <option value="analyst">Analyst - Can make predictions</option>
                  <option value="admin">Admin - Can manage members</option>
                </select>
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowInviteModal(false)}
                  className="px-4 py-2 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                >
                  <UserPlus className="w-4 h-4" />
                  Send Invite
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
