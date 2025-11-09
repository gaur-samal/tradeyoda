import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Tag,
  Space,
  message,
  Popconfirm,
  Drawer,
  Descriptions,
  Card,
  Alert,
} from 'antd';
import {
  PlusOutlined,
  ReloadOutlined,
  EyeOutlined,
  StopOutlined,
  CopyOutlined,
} from '@ant-design/icons';
import {
  getAllLicenses,
  createLicense,
  getLicenseDetails,
  revokeLicense,
  deleteLicense,
  bulkDeleteLicenses,
} from '../services/api';
import dayjs from 'dayjs';

const { Option } = Select;
const { Search } = Input;

const Licenses = () => {
  const [licenses, setLicenses] = useState([]);
  const [filteredLicenses, setFilteredLicenses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [detailsDrawerVisible, setDetailsDrawerVisible] = useState(false);
  const [selectedLicense, setSelectedLicense] = useState(null);
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchLicenses();
  }, []);

  const fetchLicenses = async () => {
    try {
      setLoading(true);
      const response = await getAllLicenses(0, 1000);
      const data = response.data.licenses || [];
      setLicenses(data);
      setFilteredLicenses(data);
    } catch (error) {
      message.error('Failed to fetch licenses');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateLicense = async (values) => {
    try {
      const response = await createLicense(values);
      message.success(
        <span>
          License created: <code>{response.data.license_key}</code>
          <Button
            type="link"
            icon={<CopyOutlined />}
            onClick={() => {
              navigator.clipboard.writeText(response.data.license_key);
              message.success('License key copied!');
            }}
          >
            Copy
          </Button>
        </span>,
        10
      );
      setModalVisible(false);
      form.resetFields();
      fetchLicenses();
    } catch (error) {
      message.error('Failed to create license');
      console.error(error);
    }
  };

  const handleViewDetails = async (licenseKey) => {
    try {
      const response = await getLicenseDetails(licenseKey);
      setSelectedLicense(response.data);
      setDetailsDrawerVisible(true);
    } catch (error) {
      message.error('Failed to fetch license details');
      console.error(error);
    }
  };

  const handleRevoke = async (licenseKey) => {
    try {
      await revokeLicense(licenseKey);
      message.success('License revoked successfully');
      fetchLicenses();
    } catch (error) {
      message.error('Failed to revoke license');
      console.error(error);
    }
  };

  const handleDelete = async (licenseKey) => {
    try {
      await deleteLicense(licenseKey);
      message.success('License deleted successfully');
      fetchLicenses();
      setSelectedRowKeys(selectedRowKeys.filter(key => key !== licenseKey));
    } catch (error) {
      message.error('Failed to delete license');
      console.error(error);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Please select licenses to delete');
      return;
    }

    try {
      const response = await bulkDeleteLicenses(selectedRowKeys);
      message.success(`${response.data.deleted_count} license(s) deleted successfully`);
      setSelectedRowKeys([]);
      fetchLicenses();
    } catch (error) {
      message.error('Failed to delete licenses');
      console.error(error);
    }
  };

  const handleSearch = (value) => {
    const filtered = licenses.filter(
      (license) =>
        license.license_key.toLowerCase().includes(value.toLowerCase()) ||
        (license.user_email && license.user_email.toLowerCase().includes(value.toLowerCase())) ||
        (license.user_name && license.user_name.toLowerCase().includes(value.toLowerCase()))
    );
    setFilteredLicenses(filtered);
  };

  const columns = [
    {
      title: 'License Key',
      dataIndex: 'license_key',
      key: 'license_key',
      fixed: 'left',
      render: (text) => (
        <Space>
          <code>{text}</code>
          <Button
            type="text"
            size="small"
            icon={<CopyOutlined />}
            onClick={() => {
              navigator.clipboard.writeText(text);
              message.success('Copied!');
            }}
          />
        </Space>
      ),
    },
    {
      title: 'Tier',
      dataIndex: 'tier',
      key: 'tier',
      filters: [
        { text: 'Trial', value: 'TRIAL' },
        { text: 'Basic', value: 'BASIC' },
        { text: 'Advanced', value: 'ADVANCED' },
        { text: 'Pro', value: 'PRO' },
      ],
      onFilter: (value, record) => record.tier === value,
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
      filters: [
        { text: 'Active', value: 'ACTIVE' },
        { text: 'Expired', value: 'EXPIRED' },
        { text: 'Revoked', value: 'REVOKED' },
      ],
      onFilter: (value, record) => record.status === value,
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
      title: 'User Name',
      dataIndex: 'user_name',
      key: 'user_name',
    },
    {
      title: 'Validations',
      dataIndex: 'validation_count',
      key: 'validation_count',
      sorter: (a, b) => (a.validation_count || 0) - (b.validation_count || 0),
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      sorter: (a, b) => new Date(a.created_at) - new Date(b.created_at),
      render: (date) => (date ? dayjs(date).format('MMM D, YYYY HH:mm') : '-'),
    },
    {
      title: 'Expires',
      dataIndex: 'expires_at',
      key: 'expires_at',
      render: (date) => (date ? dayjs(date).format('MMM D, YYYY') : 'Never'),
    },
    {
      title: 'Actions',
      key: 'actions',
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetails(record.license_key)}
          >
            Details
          </Button>
          {record.status === 'ACTIVE' && (
            <Popconfirm
              title="Are you sure you want to revoke this license?"
              onConfirm={() => handleRevoke(record.license_key)}
              okText="Yes"
              cancelText="No"
            >
              <Button type="link" danger icon={<StopOutlined />}>
                Revoke
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h1>📋 License Management</h1>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={fetchLicenses}>
            Refresh
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
            Create License
          </Button>
        </Space>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Search
          placeholder="Search by license key, email, or name"
          onSearch={handleSearch}
          onChange={(e) => handleSearch(e.target.value)}
          style={{ width: 400 }}
        />
      </Card>

      <Table
        dataSource={filteredLicenses}
        columns={columns}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1500 }}
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
          showTotal: (total) => `Total ${total} licenses`,
        }}
      />

      {/* Create License Modal */}
      <Modal
        title="Create New License"
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        footer={null}
      >
        <Form form={form} onFinish={handleCreateLicense} layout="vertical">
          <Form.Item
            name="tier"
            label="Tier"
            rules={[{ required: true, message: 'Please select a tier' }]}
          >
            <Select placeholder="Select tier">
              <Option value="TRIAL">Trial (14 days)</Option>
              <Option value="BASIC">Basic</Option>
              <Option value="ADVANCED">Advanced</Option>
              <Option value="PRO">Pro</Option>
            </Select>
          </Form.Item>
          <Form.Item name="user_email" label="User Email">
            <Input type="email" placeholder="user@example.com" />
          </Form.Item>
          <Form.Item name="user_name" label="User Name">
            <Input placeholder="John Doe" />
          </Form.Item>
          <Form.Item name="notes" label="Notes">
            <Input.TextArea rows={3} placeholder="Optional notes about this license" />
          </Form.Item>
          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setModalVisible(false)}>Cancel</Button>
              <Button type="primary" htmlType="submit">
                Create License
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* License Details Drawer */}
      <Drawer
        title="License Details"
        placement="right"
        width={600}
        onClose={() => setDetailsDrawerVisible(false)}
        open={detailsDrawerVisible}
      >
        {selectedLicense && (
          <div>
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="License Key">
                <code>{selectedLicense.license?.license_key}</code>
                <Button
                  type="link"
                  size="small"
                  icon={<CopyOutlined />}
                  onClick={() => {
                    navigator.clipboard.writeText(selectedLicense.license?.license_key);
                    message.success('Copied!');
                  }}
                />
              </Descriptions.Item>
              <Descriptions.Item label="Tier">
                <Tag
                  color={
                    {
                      TRIAL: 'orange',
                      BASIC: 'blue',
                      ADVANCED: 'purple',
                      PRO: 'gold',
                    }[selectedLicense.license?.tier]
                  }
                >
                  {selectedLicense.license?.tier}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Status">
                <Tag
                  color={
                    {
                      ACTIVE: 'success',
                      EXPIRED: 'warning',
                      REVOKED: 'error',
                    }[selectedLicense.license?.status]
                  }
                >
                  {selectedLicense.license?.status}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="User Email">
                {selectedLicense.license?.user_email || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="User Name">
                {selectedLicense.license?.user_name || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Validation Count">
                {selectedLicense.license?.validation_count || 0}
              </Descriptions.Item>
              <Descriptions.Item label="Last IP">
                {selectedLicense.license?.last_ip || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Device ID">
                {selectedLicense.license?.device_id || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Created">
                {selectedLicense.license?.created_at
                  ? dayjs(selectedLicense.license.created_at).format('MMM D, YYYY HH:mm:ss')
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Activated">
                {selectedLicense.license?.activated_at
                  ? dayjs(selectedLicense.license.activated_at).format('MMM D, YYYY HH:mm:ss')
                  : 'Not yet'}
              </Descriptions.Item>
              <Descriptions.Item label="Last Validated">
                {selectedLicense.license?.last_validated
                  ? dayjs(selectedLicense.license.last_validated).format('MMM D, YYYY HH:mm:ss')
                  : 'Never'}
              </Descriptions.Item>
              <Descriptions.Item label="Expires">
                {selectedLicense.license?.expires_at
                  ? dayjs(selectedLicense.license.expires_at).format('MMM D, YYYY')
                  : 'Never'}
              </Descriptions.Item>
              <Descriptions.Item label="Notes">
                {selectedLicense.license?.notes || '-'}
              </Descriptions.Item>
            </Descriptions>

            <h3 style={{ marginTop: 24, marginBottom: 16 }}>Recent Validations</h3>
            {selectedLicense.recent_validations && selectedLicense.recent_validations.length > 0 ? (
              <Table
                dataSource={selectedLicense.recent_validations}
                columns={[
                  {
                    title: 'Timestamp',
                    dataIndex: 'timestamp',
                    key: 'timestamp',
                    render: (date) => dayjs(date).format('MMM D, YYYY HH:mm:ss'),
                  },
                  {
                    title: 'IP Address',
                    dataIndex: 'ip_address',
                    key: 'ip_address',
                  },
                  {
                    title: 'Status',
                    dataIndex: 'status',
                    key: 'status',
                    render: (status) => (
                      <Tag color={status === 'SUCCESS' ? 'success' : 'error'}>{status}</Tag>
                    ),
                  },
                ]}
                rowKey="id"
                size="small"
                pagination={false}
              />
            ) : (
              <Alert message="No validation history" type="info" />
            )}
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default Licenses;
