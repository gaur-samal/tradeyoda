import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Select, Tag, Space, message, Card } from 'antd';
import { PlusOutlined, ReloadOutlined, KeyOutlined } from '@ant-design/icons';
import { getOpenAIKeys, addOpenAIKey } from '../services/api';
import dayjs from 'dayjs';

const { Option } = Select;

const OpenAIKeys = () => {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchKeys();
  }, []);

  const fetchKeys = async () => {
    try {
      setLoading(true);
      const response = await getOpenAIKeys();
      setKeys(response.data.keys || []);
    } catch (error) {
      message.error('Failed to fetch OpenAI keys');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddKey = async (values) => {
    try {
      await addOpenAIKey(values);
      message.success('OpenAI key added/updated successfully');
      setModalVisible(false);
      form.resetFields();
      fetchKeys();
    } catch (error) {
      message.error('Failed to add/update OpenAI key');
      console.error(error);
    }
  };

  const columns = [
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
      title: 'Model',
      dataIndex: 'model',
      key: 'model',
      render: (model) => <code>{model}</code>,
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive) => (
        <Tag color={isActive ? 'success' : 'error'}>{isActive ? 'Active' : 'Inactive'}</Tag>
      ),
    },
    {
      title: 'Last Updated',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (date) => (date ? dayjs(date).format('MMM D, YYYY HH:mm') : '-'),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h1>🔑 OpenAI Key Management</h1>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={fetchKeys}>
            Refresh
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
            Add/Update Key
          </Button>
        </Space>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <p>
          ⚠️ <strong>Security Note:</strong> OpenAI API keys are encrypted in the database. The
          actual keys are never displayed here.
        </p>
        <p>
          Each tier can have one OpenAI key. Adding a key for an existing tier will update it.
        </p>
      </Card>

      <Card>
        <h3 style={{ marginBottom: 16 }}>Configured Keys</h3>
        <Table
          dataSource={keys}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={false}
        />
      </Card>

      {/* Feature Matrix */}
      <Card title="Tier OpenAI Model Matrix" style={{ marginTop: 16 }}>
        <Table
          dataSource={[
            { tier: 'TRIAL', model: 'gpt-4o-mini', description: '14-day trial period' },
            { tier: 'BASIC', model: 'gpt-4o-mini', description: 'Analysis only' },
            { tier: 'ADVANCED', model: 'gpt-4o', description: 'Analysis + Manual Trading' },
            { tier: 'PRO', model: 'gpt-4.1', description: 'Full automation' },
          ]}
          columns={[
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
              title: 'Recommended Model',
              dataIndex: 'model',
              key: 'model',
              render: (model) => <code>{model}</code>,
            },
            {
              title: 'Description',
              dataIndex: 'description',
              key: 'description',
            },
          ]}
          pagination={false}
          size="small"
        />
      </Card>

      {/* Add/Update Key Modal */}
      <Modal
        title="Add/Update OpenAI Key"
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        footer={null}
      >
        <Form form={form} onFinish={handleAddKey} layout="vertical">
          <Form.Item
            name="tier"
            label="Tier"
            rules={[{ required: true, message: 'Please select a tier' }]}
          >
            <Select placeholder="Select tier">
              <Option value="TRIAL">Trial</Option>
              <Option value="BASIC">Basic</Option>
              <Option value="ADVANCED">Advanced</Option>
              <Option value="PRO">Pro</Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="api_key"
            label="OpenAI API Key"
            rules={[
              { required: true, message: 'Please enter the API key' },
              { pattern: /^sk-/, message: 'OpenAI keys start with "sk-"' },
            ]}
          >
            <Input.Password
              prefix={<KeyOutlined />}
              placeholder="sk-..."
              autoComplete="off"
            />
          </Form.Item>
          <Form.Item
            name="model"
            label="Model"
            rules={[{ required: true, message: 'Please enter the model name' }]}
          >
            <Select placeholder="Select or enter model name">
              <Option value="gpt-4o-mini">gpt-4o-mini</Option>
              <Option value="gpt-4o">gpt-4o</Option>
              <Option value="gpt-4.1">gpt-4.1</Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setModalVisible(false)}>Cancel</Button>
              <Button type="primary" htmlType="submit">
                Save Key
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default OpenAIKeys;
