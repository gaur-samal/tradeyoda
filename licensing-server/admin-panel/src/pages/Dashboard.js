import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Alert } from 'antd';
import {
  LicenseOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  StopOutlined,
  RiseOutlined,
} from '@ant-design/icons';
import { Column } from '@ant-design/plots';
import { getStatistics, getAllLicenses } from '../services/api';
import dayjs from 'dayjs';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [recentLicenses, setRecentLicenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [statsRes, licensesRes] = await Promise.all([
        getStatistics(),
        getAllLicenses(0, 10),
      ]);
      
      setStats(statsRes.data);
      setRecentLicenses(licensesRes.data.licenses || []);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const tierData = stats ? [
    { tier: 'Trial', count: stats.by_tier.trial },
    { tier: 'Basic', count: stats.by_tier.basic },
    { tier: 'Advanced', count: stats.by_tier.advanced },
    { tier: 'Pro', count: stats.by_tier.pro },
  ] : [];

  const columns = [
    {
      title: 'License Key',
      dataIndex: 'license_key',
      key: 'license_key',
      render: (text) => <code>{text}</code>,
    },
    {
      title: 'Tier',
      dataIndex: 'tier',
      key: 'tier',
      render: (tier) => {
        const colors = {
          TRIAL: 'orange',
          BASIC: 'blue',
          ADVANCED: 'purple',
          PRO: 'gold',
        };
        return <Tag color={colors[tier]}>{tier}</Tag>;
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const colors = {
          ACTIVE: 'success',
          EXPIRED: 'warning',
          REVOKED: 'error',
        };
        return <Tag color={colors[status]}>{status}</Tag>;
      },
    },
    {
      title: 'User Email',
      dataIndex: 'user_email',
      key: 'user_email',
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => date ? dayjs(date).format('MMM D, YYYY') : '-',
    },
  ];

  if (error) {
    return (
      <Alert
        message="Error Loading Dashboard"
        description={error}
        type="error"
        showIcon
      />
    );
  }

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>📊 Dashboard</h1>
      
      {/* Statistics Cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Licenses"
              value={stats?.total_licenses || 0}
              prefix={<LicenseOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Active Licenses"
              value={stats?.active_licenses || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#3f8600' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Expired Licenses"
              value={stats?.expired_licenses || 0}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: '#cf1322' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Revoked Licenses"
              value={stats?.revoked_licenses || 0}
              prefix={<StopOutlined />}
              valueStyle={{ color: '#8c8c8c' }}
              loading={loading}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Validations Today"
              value={stats?.validations_today || 0}
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#1890ff' }}
              loading={loading}
            />
          </Card>
        </Col>
      </Row>

      {/* Tier Distribution Chart */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card title="License Distribution by Tier" loading={loading}>
            {tierData.length > 0 && (
              <Column
                data={tierData}
                xField="tier"
                yField="count"
                label={{
                  position: 'top',
                }}
                color={(datum) => {
                  const colors = {
                    Trial: '#fa8c16',
                    Basic: '#1890ff',
                    Advanced: '#722ed1',
                    Pro: '#faad14',
                  };
                  return colors[datum.tier] || '#1890ff';
                }}
                meta={{
                  tier: { alias: 'Tier' },
                  count: { alias: 'Count' },
                }}
              />
            )}
          </Card>
        </Col>
      </Row>

      {/* Recent Licenses */}
      <Card title="Recent Licenses" loading={loading}>
        <Table
          dataSource={recentLicenses}
          columns={columns}
          rowKey="id"
          pagination={false}
        />
      </Card>
    </div>
  );
};

export default Dashboard;
