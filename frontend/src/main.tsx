import React from 'react';
import ReactDOM from 'react-dom/client';
import { App, ConfigProvider, Empty, List, Table, Tag, Tooltip, Typography, message } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { CheckOutlined, ClearOutlined, SearchOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { Button, Card, Col, Form, Input, Layout, Row, Select, Space } from 'antd';
import { createBatchTransfer, createManualTransferTask, createTransferTask, getBatch, getBatchItems, getTask, searchResources } from './api/client';
import { LogPanel } from './components/LogPanel';
import { TaskStatusCard } from './components/TaskStatusCard';
import { useTaskLogs } from './hooks/useTaskLogs';
import type { BatchDetail, BatchItem, MediaType, ResourceItem, TaskDetail } from './types';
import './styles.css';

type SearchFormValues = { keyword: string; driver: '115'; mediaType: MediaType };
type ManualFormValues = { shareText: string; mediaType: MediaType };

const statusLabel: Record<BatchItem['status'], string> = {
  pending: '等待中',
  running: '处理中',
  success: '已完成',
  skipped: '已跳过',
  failed: '失败',
};

function MainPage() {
  const [form] = Form.useForm<SearchFormValues>();
  const [manualForm] = Form.useForm<ManualFormValues>();
  const [resources, setResources] = React.useState<ResourceItem[]>([]);
  const [searching, setSearching] = React.useState(false);
  const [taskSubmitting, setTaskSubmitting] = React.useState(false);
  const [batchSubmitting, setBatchSubmitting] = React.useState(false);
  const [selectedResourceIds, setSelectedResourceIds] = React.useState<React.Key[]>([]);
  const [taskId, setTaskId] = React.useState<string | null>(null);
  const [task, setTask] = React.useState<TaskDetail | null>(null);
  const [batch, setBatch] = React.useState<BatchDetail | null>(null);
  const [batchItems, setBatchItems] = React.useState<BatchItem[]>([]);
  const [messageApi, contextHolder] = message.useMessage();
  const { logs, connected } = useTaskLogs(taskId);

  const selectedResources = React.useMemo(
    () => resources.filter((item) => selectedResourceIds.includes(item.id)),
    [resources, selectedResourceIds],
  );
  const selectedResource = selectedResources[0] ?? null;

  React.useEffect(() => {
    if (!taskId) return;

    const pollTask = async () => {
      try {
        const detail = await getTask(taskId);
        setTask(detail);
      } catch (error) {
        messageApi.error(error instanceof Error ? error.message : '读取任务状态失败');
      }
    };

    void pollTask();
    const timer = window.setInterval(() => void pollTask(), 1500);
    return () => window.clearInterval(timer);
  }, [taskId, messageApi]);

  React.useEffect(() => {
    if (!batch?.id) {
      setBatchItems([]);
      return;
    }

    const pollBatch = async () => {
      try {
        const detail = await getBatch(batch.id);
        setBatch(detail);
        setBatchItems(await getBatchItems(batch.id));
      } catch (error) {
        messageApi.error(error instanceof Error ? error.message : '读取批次状态失败');
      }
    };

    void pollBatch();
    const timer = window.setInterval(() => void pollBatch(), 1500);
    return () => window.clearInterval(timer);
  }, [batch?.id, messageApi]);

  const clearActivity = () => {
    setTaskId(null);
    setTask(null);
    setBatch(null);
    setBatchItems([]);
  };

  const handleSearch = async () => {
    const values = await form.validateFields();
    setSearching(true);
    setSelectedResourceIds([]);
    clearActivity();
    try {
      const data = await searchResources(values.keyword.trim(), values.driver, values.mediaType);
      setResources(data);
      messageApi.success(`搜索完成，共 ${data.length} 条结果`);
    } catch (error) {
      setResources([]);
      messageApi.error(error instanceof Error ? error.message : '搜索失败');
    } finally {
      setSearching(false);
    }
  };

  const handleRunTask = async () => {
    if (selectedResources.length !== 1) {
      messageApi.warning('单条转存需要只选择一条资源');
      return;
    }

    setTaskSubmitting(true);
    try {
      const result = await createTransferTask(form.getFieldValue('keyword'), selectedResource!);
      setTaskId(result.taskId);
      setTask(null);
      setBatch(null);
      messageApi.success(result.reused ? '已复用已有任务' : '任务已创建');
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '创建任务失败');
    } finally {
      setTaskSubmitting(false);
    }
  };

  const handleRunBatch = async () => {
    if (selectedResources.length === 0) {
      messageApi.warning('请至少选择一条资源');
      return;
    }

    setBatchSubmitting(true);
    try {
      const result = await createBatchTransfer(form.getFieldValue('keyword'), selectedResources);
      setBatch(result);
      setTaskId(null);
      setTask(null);
      messageApi.success(`批次已创建，共 ${result.totalCount} 条`);
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '创建批次失败');
    } finally {
      setBatchSubmitting(false);
    }
  };

  const handleManualRunTask = async () => {
    const values = await manualForm.validateFields();
    setTaskSubmitting(true);
    try {
      const result = await createManualTransferTask(values);
      setTaskId(result.taskId);
      setTask(null);
      setBatch(null);
      messageApi.success(result.reused ? '已复用已有任务' : '手动任务已创建');
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '创建手动任务失败');
    } finally {
      setTaskSubmitting(false);
    }
  };

  const handleViewBatchTask = (item: BatchItem) => {
    if (item.taskId) setTaskId(item.taskId);
  };

  const handleRetryBatchTask = async (item: BatchItem) => {
    try {
      const result = await createTransferTask(batch?.keyword ?? form.getFieldValue('keyword'), item.resource);
      setTaskId(result.taskId);
      messageApi.success('已重新提交任务');
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '重新提交失败');
    }
  };

  const selectionActions = [
    { key: 'all', text: '全选搜索结果', onSelect: () => setSelectedResourceIds(resources.map((item) => item.id)) },
    { key: 'invert', text: '反选搜索结果', onSelect: () => setSelectedResourceIds(resources.filter((item) => !selectedResourceIds.includes(item.id)).map((item) => item.id)) },
    { key: 'clear', text: '清空选择', onSelect: () => setSelectedResourceIds([]) },
  ];

  return (
    <Layout className="app-shell">
      {contextHolder}
      <Layout.Content className="app-content">
        <header className="app-header">
          <div>
            <Typography.Title level={2}>STRM 工作台</Typography.Title>
            <Typography.Text type="secondary">搜索资源、批量转存，并跟踪生成进度</Typography.Text>
          </div>
          <Tag className="header-status">115 · STRM</Tag>
        </header>

        <Row gutter={[20, 20]} align="top">
          <Col xs={24} xl={16}>
            <Card title="搜索资源" className="panel-card search-card">
              <Form form={form} layout="vertical" initialValues={{ keyword: '', driver: '115', mediaType: 'movie' }}>
                <Row gutter={16}>
                  <Col xs={24} md={12}>
                    <Form.Item name="keyword" label="关键词" rules={[{ required: true, whitespace: true, message: '请输入关键词' }]}>
                      <Input size="large" placeholder="例如：流浪地球" allowClear onPressEnter={() => void handleSearch()} />
                    </Form.Item>
                  </Col>
                  <Col xs={12} md={6}><Form.Item name="mediaType" label="资源类型"><Select size="large" options={[{ label: '电影', value: 'movie' }, { label: '电视', value: 'tv' }]} /></Form.Item></Col>
                  <Col xs={12} md={6}><Form.Item name="driver" label="驱动"><Select size="large" options={[{ label: '115', value: '115' }]} disabled /></Form.Item></Col>
                </Row>
                <Space wrap>
                  <Button type="primary" icon={<SearchOutlined />} loading={searching} onClick={() => void handleSearch()}>搜索</Button>
                  <Button icon={<ThunderboltOutlined />} loading={taskSubmitting} disabled={selectedResources.length !== 1 || searching} onClick={() => void handleRunTask()}>单条转存</Button>
                  <Button icon={<ThunderboltOutlined />} loading={batchSubmitting} disabled={selectedResources.length === 0 || searching} onClick={() => void handleRunBatch()}>批量转存{selectedResources.length > 0 ? `（${selectedResources.length}）` : ''}</Button>
                </Space>
              </Form>
            </Card>

            <Card
              title={<div className="section-title"><span>搜索结果</span><Typography.Text type="secondary">{resources.length ? `共 ${resources.length} 条` : '等待搜索'}</Typography.Text></div>}
              className="panel-card result-card"
              extra={selectedResources.length > 0 ? <Typography.Text className="selection-count">已选 {selectedResources.length} 条</Typography.Text> : null}
            >
              {resources.length === 0 ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="输入关键词后开始搜索" /> : (
                <Table<ResourceItem>
                  rowKey="id"
                  dataSource={resources}
                  tableLayout="fixed"
                  scroll={{ x: 620 }}
                  pagination={{ defaultPageSize: 20, pageSizeOptions: ['20', '50', '100', '200'], showSizeChanger: true, showTotal: (total) => `共 ${total} 条` }}
                  rowSelection={{ selectedRowKeys: selectedResourceIds, selections: selectionActions, onChange: (selectedRowKeys) => setSelectedResourceIds(selectedRowKeys) }}
                  columns={[
                    { title: '标题', dataIndex: 'title', width: '46%', ellipsis: true, render: (value: string) => <Tooltip title={value}><Typography.Text strong ellipsis className="result-title">{value}</Typography.Text></Tooltip> },
                    { title: '类型', dataIndex: 'mediaType', width: 80, render: (value: MediaType) => value === 'tv' ? '电视' : '电影' },
                    { title: '大小', dataIndex: 'size', width: 100 },
                    { title: '来源', dataIndex: 'provider', width: 80 },
                    { title: '链接', dataIndex: 'shareUrl', width: 90, render: (value: string) => <Typography.Link href={value} target="_blank" rel="noreferrer">打开</Typography.Link> },
                  ]}
                />
              )}
              {selectedResources.length > 0 && <div className="selection-bar"><CheckOutlined /><span>已选 {selectedResources.length} 条资源</span><Button type="link" size="small" icon={<ClearOutlined />} onClick={() => setSelectedResourceIds([])}>清空</Button></div>}
            </Card>

            <Card title="手动 115 转存" className="panel-card manual-card">
              <Form form={manualForm} layout="vertical" initialValues={{ shareText: '', mediaType: 'movie' }}>
                <Form.Item name="shareText" label="分享文本" rules={[{ required: true, whitespace: true, message: '请粘贴 115 分享文本' }]}>
                  <Input.TextArea rows={3} placeholder="粘贴包含 115 链接和提取码的完整文本" allowClear />
                </Form.Item>
                <Row gutter={16} align="bottom">
                  <Col xs={24} md={8}><Form.Item name="mediaType" label="转存路径"><Select size="large" options={[{ label: '电影', value: 'movie' }, { label: '电视', value: 'tv' }]} /></Form.Item></Col>
                  <Col xs={24} md={16}><Form.Item label=" "><Button type="primary" block loading={taskSubmitting} icon={<ThunderboltOutlined />} onClick={() => void handleManualRunTask()}>手动转存并生成 STRM</Button></Form.Item></Col>
                </Row>
              </Form>
            </Card>
          </Col>

          <Col xs={24} xl={8}>
            <TaskStatusCard task={task} batch={batch} />
            {batchItems.some((item) => item.status === 'failed') && (
              <Card title="失败项" className="panel-card batch-card">
                <List size="small" dataSource={batchItems.filter((item) => item.status === 'failed')} renderItem={(item) => <List.Item actions={[<Button key="view" size="small" onClick={() => handleViewBatchTask(item)} disabled={!item.taskId}>查看</Button>, <Button key="retry" size="small" type="link" onClick={() => void handleRetryBatchTask(item)}>重试</Button>]}><Typography.Text ellipsis>{item.resource.title}</Typography.Text><Typography.Text type="secondary">{statusLabel[item.status]}</Typography.Text></List.Item>} />
              </Card>
            )}
            <LogPanel logs={logs} connected={connected} />
          </Col>
        </Row>
      </Layout.Content>
    </Layout>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider locale={zhCN} theme={{ token: { colorPrimary: '#a13b2f', colorLink: '#8e342b', colorText: '#262421', colorBgLayout: '#f5f2ed', borderRadius: 8, fontFamily: 'Avenir Next, PingFang SC, Hiragino Sans GB, sans-serif' } }}>
      <App><MainPage /></App>
    </ConfigProvider>
  </React.StrictMode>,
);
