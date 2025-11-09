import React, { useState, useEffect } from 'react';
import {
  Card,
  Upload,
  Button,
  Form,
  Input,
  message,
  Alert,
  Descriptions,
  Space,
  Progress,
} from 'antd';
import { UploadOutlined, ReloadOutlined, DownloadOutlined } from '@ant-design/icons';
import { uploadScripMaster, getScripMasterVersion } from '../services/api';
import dayjs from 'dayjs';

const ScripMaster = () => {
  const [currentVersion, setCurrentVersion] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [form] = Form.useForm();
  const [fileList, setFileList] = useState([]);

  useEffect(() => {
    fetchCurrentVersion();
  }, []);

  const fetchCurrentVersion = async () => {
    try {
      setLoading(true);
      const response = await getScripMasterVersion();
      if (response.data.has_update) {
        setCurrentVersion(response.data);
      }
    } catch (error) {
      console.error('Error fetching version:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (values) => {
    if (fileList.length === 0) {
      message.error('Please select a CSV file');
      return;
    }

    const file = fileList[0];
    const { version } = values;

    try {
      setUploading(true);
      setUploadProgress(0);

      // Simulate progress (since we can't track actual upload progress easily)
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      await uploadScripMaster(file, version);

      clearInterval(progressInterval);
      setUploadProgress(100);

      message.success('Scrip master uploaded successfully!');
      form.resetFields();
      setFileList([]);
      fetchCurrentVersion();

      setTimeout(() => {
        setUploadProgress(0);
      }, 2000);
    } catch (error) {
      message.error('Failed to upload scrip master');
      console.error(error);
      setUploadProgress(0);
    } finally {
      setUploading(false);
    }
  };

  const uploadProps = {
    accept: '.csv',
    beforeUpload: (file) => {
      const isCSV = file.type === 'text/csv' || file.name.endsWith('.csv');
      if (!isCSV) {
        message.error('You can only upload CSV files!');
        return false;
      }
      setFileList([file]);
      return false; // Prevent auto upload
    },
    fileList,
    onRemove: () => {
      setFileList([]);
    },
    maxCount: 1,
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h1>📄 Scrip Master Management</h1>
        <Button icon={<ReloadOutlined />} onClick={fetchCurrentVersion} loading={loading}>
          Refresh
        </Button>
      </div>

      <Alert
        message="About Scrip Master"
        description="The scrip master CSV file contains all available securities (futures & options) with their security IDs. This file is used by the desktop app to look up contract details. Upload a new version when Dhan releases updates."
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      {/* Current Version */}
      <Card title="Current Version" loading={loading} style={{ marginBottom: 16 }}>
        {currentVersion ? (
          <Descriptions column={2} bordered>
            <Descriptions.Item label="Version">{currentVersion.version}</Descriptions.Item>
            <Descriptions.Item label="Upload Date">
              {dayjs(currentVersion.upload_date).format('MMM D, YYYY HH:mm')}
            </Descriptions.Item>
            <Descriptions.Item label="File Size">
              {(currentVersion.file_size / (1024 * 1024)).toFixed(2)} MB
            </Descriptions.Item>
            <Descriptions.Item label="Checksum">
              <code style={{ fontSize: '0.85em' }}>{currentVersion.checksum}</code>
            </Descriptions.Item>
          </Descriptions>
        ) : (
          <Alert message="No scrip master uploaded yet" type="warning" showIcon />
        )}
      </Card>

      {/* Upload New Version */}
      <Card title="Upload New Version">
        <Form form={form} onFinish={handleUpload} layout="vertical">
          <Form.Item
            name="version"
            label="Version"
            rules={[{ required: true, message: 'Please enter a version identifier' }]}
            extra="Example: 2024-11, v1.5, etc."
          >
            <Input placeholder="2024-11" />
          </Form.Item>

          <Form.Item label="CSV File" required>
            <Upload {...uploadProps}>
              <Button icon={<UploadOutlined />}>Select CSV File</Button>
            </Upload>
          </Form.Item>

          {uploadProgress > 0 && (
            <Form.Item>
              <Progress percent={uploadProgress} status={uploading ? 'active' : 'success'} />
            </Form.Item>
          )}

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={uploading}
                disabled={fileList.length === 0}
              >
                Upload
              </Button>
              <Button
                onClick={() => {
                  form.resetFields();
                  setFileList([]);
                }}
              >
                Reset
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      {/* Instructions */}
      <Card title="📝 How to Get Scrip Master CSV" style={{ marginTop: 16 }}>
        <ol>
          <li>
            Download the latest scrip master from Dhan:
            <br />
            <a
              href="https://images.dhan.co/api-data/api-scrip-master.csv"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button type="link" icon={<DownloadOutlined />}>
                Download from Dhan
              </Button>
            </a>
          </li>
          <li>Enter a version identifier (e.g., current month: "2024-11")</li>
          <li>Select the downloaded CSV file</li>
          <li>Click "Upload" to make it available to all desktop apps</li>
        </ol>
        <Alert
          message="Note"
          description="Desktop apps will automatically check for and download new scrip master versions on startup."
          type="info"
          showIcon
          style={{ marginTop: 16 }}
        />
      </Card>
    </div>
  );
};

export default ScripMaster;
