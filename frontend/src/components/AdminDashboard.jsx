import React, { useState, useEffect } from 'react';
import { Users, Shield, Activity, Settings, TrendingUp, AlertTriangle, Database, Clock } from 'lucide-react';
import { useTranslation } from 'react-i18n';
import api from '../services/api';

const AdminDashboard = () => {
  const { t } = useTranslation();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [systemHealth, setSystemHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    try {
      setLoading(true);

      // Load admin statistics
      const [statsRes, usersRes, healthRes] = await Promise.all([
        api.get('/admin/stats'),
        api.get('/admin/users'),
        api.get('/health/system')
      ]);

      setStats(statsRes.data);
      setUsers(usersRes.data);
      setSystemHealth(healthRes.data);
    } catch (error) {
      console.error('Failed to load admin data:', error);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ icon: Icon, title, value, change, color }) => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-2xl font-bold mt-2">{value}</p>
          {change && (
            <p className={`text-sm mt-1 ${change > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {change > 0 ? '+' : ''}{change}% from last week
            </p>
          )}
        </div>
        <div className={`p-3 rounded-full ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  );

  const UserRow = ({ user }) => (
    <tr className="border-b hover:bg-gray-50">
      <td className="px-6 py-4">{user.username}</td>
      <td className="px-6 py-4">{user.email}</td>
      <td className="px-6 py-4">
        <span className={`px-2 py-1 rounded text-sm ${
          user.role === 'ADMIN' ? 'bg-purple-100 text-purple-800' :
          user.role === 'ANALYST' ? 'bg-blue-100 text-blue-800' :
          'bg-gray-100 text-gray-800'
        }`}>
          {user.role}
        </span>
      </td>
      <td className="px-6 py-4">{user.predictions_count || 0}</td>
      <td className="px-6 py-4">
        {user.last_login_at ? new Date(user.last_login_at).toLocaleDateString() : 'Never'}
      </td>
      <td className="px-6 py-4">
        <button className="text-blue-600 hover:text-blue-800 mr-3">Edit</button>
        <button className="text-red-600 hover:text-red-800">Delete</button>
      </td>
    </tr>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-600 mt-2">Manage users, monitor system, and view analytics</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={Users}
            title="Total Users"
            value={stats?.total_users || 0}
            change={stats?.users_growth || 0}
            color="bg-blue-600"
          />
          <StatCard
            icon={Activity}
            title="Predictions Today"
            value={stats?.predictions_today || 0}
            change={stats?.predictions_growth || 0}
            color="bg-green-600"
          />
          <StatCard
            icon={AlertTriangle}
            title="Fraud Detected"
            value={stats?.fraud_detected || 0}
            change={stats?.fraud_change || 0}
            color="bg-red-600"
          />
          <StatCard
            icon={TrendingUp}
            title="Accuracy"
            value={`${stats?.model_accuracy || 99.5}%`}
            color="bg-purple-600"
          />
        </div>

        {/* System Health */}
        {systemHealth && (
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="text-xl font-bold mb-4 flex items-center">
              <Activity className="w-5 h-5 mr-2" />
              System Health
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded">
                <span>CPU Usage</span>
                <span className="font-bold">{systemHealth.metrics?.cpu_percent?.toFixed(1)}%</span>
              </div>
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded">
                <span>Memory Usage</span>
                <span className="font-bold">{systemHealth.metrics?.memory_percent?.toFixed(1)}%</span>
              </div>
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded">
                <span>Disk Usage</span>
                <span className="font-bold">{systemHealth.metrics?.disk_percent?.toFixed(1)}%</span>
              </div>
            </div>
            {systemHealth.issues?.length > 0 && (
              <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded">
                <p className="font-semibold text-yellow-800">Issues Detected:</p>
                <ul className="list-disc list-inside mt-2">
                  {systemHealth.issues.map((issue, i) => (
                    <li key={i} className="text-yellow-700">{issue}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Users Table */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b flex items-center justify-between">
            <h2 className="text-xl font-bold flex items-center">
              <Users className="w-5 h-5 mr-2" />
              User Management
            </h2>
            <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
              Add User
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Username</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Predictions</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Login</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map(user => (
                  <UserRow key={user.id} user={user} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
