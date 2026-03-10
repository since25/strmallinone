import React from 'react';
import ReactDOM from 'react-dom/client';
import { App, ConfigProvider, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { SearchOutlined, ThunderboltOutlined } from '@ant-design/icons';
import {
  Button,
  Card,
  Col,
  Form,
  Input,
  Layout,
  Radio,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
  Tooltip,
} from 'antd';
import { createTransferTask, getTask, searchResources } from './api/client';
import { LogPanel } from './components/LogPanel';
import { TaskStatusCard } from './components/TaskStatusCard';
import { useTaskLogs } from './hooks/useTaskLogs';
import type { MediaType, ResourceItem, TaskDetail } from './types';
import './styles.css';

function MainPage() {
  const [form] = Form.useForm<{ keyword: string; driver: '115'; mediaType: MediaType }>();
  const [resources, setResources] = React.useState<ResourceItem[]>([]);
  const [searching, setSearching] = React.useState(false);
  const [running, setRunning] = React.useState(false);
  const [selectedResourceId, setSelectedResourceId] = React.useState<string | null>(null);
  const [taskId, setTaskId] = React.useState<string | null>(null);
  const [task, setTask] = React.useState<TaskDetail | null>(null);
  const [messageApi, contextHolder] = message.useMessage();
  const { logs, connected } = useTaskLogs(taskId);

  const selectedResource = React.useMemo(
    () => resources.find((item) => item.id === selectedResourceId) ?? null,
    [resources, selectedResourceId],
  );

  React.useEffect(() => {
    if (!taskId) {
      return;
    }

    const pollTask = async () => {
      try {
        const detail = await getTask(taskId);
        setTask(detail);
        if (detail.status === 'success' || detail.status === 'failed') {
          setRunning(false);
        }
      } catch (error) {
        setRunning(false);
        messageApi.error(error instanceof Error ? error.message : '读取任务状态失败');
      }
    };

    void pollTask();
    const timer = window.setInterval(() => {
      void pollTask();
    }, 1500);

    return () => window.clearInterval(timer);
  }, [taskId, messageApi]);

  const handleSearch = async () => {
    const values = await form.validateFields();
    setSearching(true);
    setSelectedResourceId(null);
    setTaskId(null);
    setTask(null);
    try {
      const data = await searchResources(values.keyword, values.driver, values.mediaType);
      setResources(data);
      messageApi.success(`搜索完成，共 ${data.length} 条结果`);
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '搜索失败');
      setResources([]);
    } finally {
      setSearching(false);
    }
  };

  const handleRunTask = async () => {
    if (!selectedResource) {
      messageApi.warning('请先选择一条资源');
      return;
    }

    const keyword = form.getFieldValue('keyword');
    setRunning(true);
    try {
      const result = await createTransferTask(keyword, selectedResource);
      setTaskId(result.taskId);
      messageApi.success(`任务已创建: ${result.taskId}`);
    } catch (error) {
      setRunning(false);
      messageApi.error(error instanceof Error ? error.message : '创建任务失败');
    }
  };

  return (
    <Layout className="app-shell">
      {contextHolder}
      <Layout.Content className="app-content">
        <div className="hero-block">
          <Tag color="geekblue">search → transfer → strm</Tag>
          <Typography.Title>STRM Workflow Console</Typography.Title>
          <Typography.Paragraph>
            针对 CloudSaver 搜索、115 转存与 STRM 生成的一体化任务面板。
          </Typography.Paragraph>
        </div>

        <Row gutter={[20, 20]}>
          <Col xs={24} xl={16}>
            <Card title="搜索资源" className="panel-card">
              <Form form={form} layout="vertical" initialValues={{ keyword: '', driver: '115', mediaType: 'movie' }}>
                <Row gutter={16}>
                  <Col xs={24} md={12}>
                    <Form.Item name="keyword" label="关键词" rules={[{ required: true, message: '请输入关键词' }]}>
                      <Input size="large" placeholder="例如：流浪地球" allowClear />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={6}>
                    <Form.Item name="mediaType" label="资源类型">
                      <Select
                        size="large"
                        options={[
                          { label: '电影', value: 'movie' },
                          { label: '电视', value: 'tv' },
                        ]}
                      />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={6}>
                    <Form.Item name="driver" label="驱动">
                      <Select
                        size="large"
                        options={[{ label: '115', value: '115' }]}
                        disabled
                      />
                    </Form.Item>
                  </Col>
                </Row>
                <Space>
                  <Button type="primary" icon={<SearchOutlined />} loading={searching} onClick={() => void handleSearch()}>
                    搜索
                  </Button>
                  <Button
                    type="default"
                    icon={<ThunderboltOutlined />}
                    loading={running}
                    onClick={() => void handleRunTask()}
                    disabled={!selectedResource || searching}
                  >
                    转存并生成 STRM
                  </Button>
                </Space>
              </Form>
            </Card>

            <Card title="搜索结果" className="panel-card result-card">
              <Table<ResourceItem>
                rowKey="id"
                dataSource={resources}
                pagination={{ pageSize: 6 }}
                tableLayout="fixed"
                rowSelection={{
                  type: 'radio',
                  selectedRowKeys: selectedResourceId ? [selectedResourceId] : [],
                  onChange: (selectedRowKeys) => setSelectedResourceId(String(selectedRowKeys[0] ?? '')),
                }}
                columns={[
                  {
                    title: '标题',
                    dataIndex: 'title',
                    width: '46%',
                    ellipsis: true,
                    render: (value: string) => (
                      <Tooltip title={value}>
                        <Typography.Text strong ellipsis className="result-title">
                          {value}
                        </Typography.Text>
                      </Tooltip>
                    ),
                  },
                  {
                    title: '类型',
                    dataIndex: 'mediaType',
                    width: 100,
                    render: (value: MediaType) => (value === 'tv' ? '电视' : '电影'),
                  },
                  { title: '大小', dataIndex: 'size', width: 100 },
                  {
                    title: '来源',
                    dataIndex: 'provider',
                    width: 90,
                    render: (value: string) => <Tag color="blue">{value}</Tag>,
                  },
                  {
                    title: '分享链接',
                    dataIndex: 'shareUrl',
                    width: 120,
                    render: (value: string) => (
                      <Typography.Link href={value} target="_blank">
                        打开链接
                      </Typography.Link>
                    ),
                  },
                ]}
              />
              <div className="selection-hint">
                <Radio checked={Boolean(selectedResource)} />
                <Typography.Text>
                  当前选择：{selectedResource ? selectedResource.title : '未选择'}
                </Typography.Text>
              </div>
            </Card>
          </Col>

          <Col xs={24} xl={8}>
            <TaskStatusCard task={task} />
            <LogPanel logs={logs} connected={connected} />
          </Col>
        </Row>
      </Layout.Content>
    </Layout>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#b03a2e',
          borderRadius: 18,
          fontFamily: 'Avenir Next, PingFang SC, Hiragino Sans GB, sans-serif',
        },
      }}
    >
      <App>
        <MainPage />
      </App>
    </ConfigProvider>
  </React.StrictMode>,
);
