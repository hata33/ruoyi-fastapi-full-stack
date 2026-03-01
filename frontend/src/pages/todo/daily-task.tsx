import { FC, useEffect, useState } from "react";
import {
  Button,
  Form,
  Input,
  Select,
  Table,
  TableColumnsType,
  Space,
  Switch,
  InputNumber,
  Modal
} from "antd";
import { useContentHeight } from "@/hooks/useContentHeight.ts";
import { useTable } from "@/hooks/useTable.ts";
import { useAction } from "@/hooks/useAction.ts";
import TableNav from "@/components/TableNav/TableNav.tsx";
import TablePagination from "@/components/TablePagination/TablePagination.tsx";
import PermissionWrap from "@/components/PermissionWrap/PermissionWrap.tsx";
import ActionFrom from "@/components/ActionFrom/ActionFrom.tsx";
import { useHttp } from "@/hooks/useHttp.ts";
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  StopOutlined,
  PushpinOutlined,
  FolderOutlined,
  CalendarOutlined,
  StarOutlined
} from "@ant-design/icons";
import dayjs from "dayjs";

const { TextArea } = Input;

// 时间格式化
const formatTime = (time: string | null | undefined) => {
  if (!time) return '-';
  return dayjs(time).format('MM-DD HH:mm');
};

const DailyTaskPage: FC = () => {
  useContentHeight();
  const [form] = Form.useForm();
  const { httpGet, httpPut, httpPatch } = useHttp();
  const [categories, setCategories] = useState<DailyTaskCategory[]>([]);

  const { list, getList, filter, pagination, paginationChange, tableLoading, total } = useTable<DailyTask>(
    form,
    '/daily-task/list'
  );
  const { remove, actionData, close, add, edit } = useAction<DailyTask>({
    url: '/daily-task',
    update: getList
  });

  // 加载分类列表
  useEffect(() => {
    httpGet<{ rows: DailyTaskCategory[] }>('/daily-task-category/list', { pageNum: 1, pageSize: 100 })
      .then(res => setCategories(res.rows || []));
  }, [httpGet]);

  useEffect(() => {
    getList();
  }, [getList]);

  // 完成任务
  const completeTask = async (taskId: number) => {
    await httpPatch(`/daily-task/${taskId}/complete`);
    getList();
  };

  // 重开任务
  const reopenTask = async (taskId: number) => {
    await httpPatch(`/daily-task/${taskId}/reopen`);
    getList();
  };

  // 禁用任务
  const disableTask = async (taskId: number) => {
    await httpPatch(`/daily-task/${taskId}/disable`);
    getList();
  };

  // 启用任务
  const enableTask = async (taskId: number) => {
    await httpPatch(`/daily-task/${taskId}/enable`);
    getList();
  };

  // 置顶/取消置顶
  const togglePin = async (taskId: number, isPinned: boolean) => {
    await httpPut(`/daily-task/${taskId}/pin`, { isPinned: !isPinned });
    getList();
  };

  const columns: TableColumnsType<DailyTask> = [
    {
      dataIndex: 'taskId',
      title: 'ID',
      width: 60,
      className: 'text-gray-400 font-mono text-xs',
    },
    {
      dataIndex: 'title',
      title: '任务标题',
      ellipsis: true,
      width: 200,
      render: (title: string, record: DailyTask) => (
        <div className="flex items-center gap-2">
          {record.isPinned && <PushpinOutlined className="text-gray-400 text-xs" />}
          <span className={record.status === 'completed' ? 'line-through text-gray-300' : ''}>{title}</span>
        </div>
      ),
    },
    {
      dataIndex: 'taskType',
      title: '类型',
      width: 80,
      render: (type: 'daily' | 'once' | 'long') => {
        const text = { daily: '每日', once: '一次性', long: '长期' }[type];
        return <span className="text-xs text-gray-500">{text}</span>;
      }
    },
    {
      dataIndex: 'status',
      title: '状态',
      width: 80,
      render: (status: 'pending' | 'completed' | 'disabled') => {
        const text = { pending: '待完成', completed: '已完成', disabled: '已禁用' }[status];
        const color = { pending: 'text-gray-600', completed: 'text-gray-400', disabled: 'text-gray-300' }[status];
        return <span className={`text-xs ${color}`}>{text}</span>;
      }
    },
    {
      dataIndex: 'completionCount',
      title: '完成',
      width: 60,
      render: (count: number) => (
        <span className="text-xs text-gray-500">{count || 0}</span>
      ),
    },
    {
      dataIndex: 'categoryId',
      title: '分类',
      width: 100,
      render: (categoryId: number) => {
        const category = categories.find(c => c.categoryId === categoryId);
        return category ? (
          <span className="text-xs text-gray-500">{category.categoryName}</span>
        ) : '-';
      }
    },
    {
      dataIndex: 'lastCompletedAt',
      title: '最后完成',
      width: 120,
      render: (time: string) => (
        <span className="text-xs text-gray-400">{formatTime(time)}</span>
      ),
    },
    {
      title: "操作",
      key: "operation",
      fixed: "right",
      width: 200,
      render: (_, record) => {
        return (
          <Space size={4} className="flex-wrap">
            <PermissionWrap perm="daily:task:edit">
              {record.status === 'pending' && (
                <Button size="small" type="link" onClick={() => completeTask(record.taskId)}>
                  完成
                </Button>
              )}
              {record.status === 'completed' && (
                <Button size="small" type="link" onClick={() => reopenTask(record.taskId)}>
                  重开
                </Button>
              )}
              {record.status === 'disabled' && (
                <Button size="small" type="link" onClick={() => enableTask(record.taskId)}>
                  启用
                </Button>
              )}
              {record.status !== 'disabled' && (
                <Button size="small" type="link" onClick={() => disableTask(record.taskId)}>
                  禁用
                </Button>
              )}
              <Button size="small" type="link" onClick={() => togglePin(record.taskId, record.isPinned)}>
                {record.isPinned ? '取消置顶' : '置顶'}
              </Button>
              <Button size="small" type="link" onClick={() => edit(record)}>
                编辑
              </Button>
            </PermissionWrap>
            <PermissionWrap perm="daily:task:remove">
              <Button size="small" type="link" danger onClick={() => remove([record.taskId])}>
                删除
              </Button>
            </PermissionWrap>
          </Space>
        );
      },
    },
  ];

  return (
    <div className="p-4">
      {/* 筛选表单 */}
      <div className="mb-4">
        <Form layout="inline" form={form} onFinish={filter} onReset={filter} className="flex flex-wrap gap-3">
          <Form.Item label="标题" name="title" className="mb-0">
            <Input placeholder="请输入" className="w-36" allowClear />
          </Form.Item>
          <Form.Item label="类型" name="taskType" className="mb-0">
            <Select placeholder="请选择" allowClear className="w-28">
              <Select.Option value="daily">每日</Select.Option>
              <Select.Option value="once">一次性</Select.Option>
              <Select.Option value="long">长期</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="状态" name="status" className="mb-0">
            <Select placeholder="请选择" allowClear className="w-28">
              <Select.Option value="pending">待完成</Select.Option>
              <Select.Option value="completed">已完成</Select.Option>
              <Select.Option value="disabled">已禁用</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="分类" name="categoryId" className="mb-0">
            <Select placeholder="请选择" allowClear className="w-28">
              {categories.map(c => (
                <Select.Option key={c.categoryId} value={c.categoryId}>{c.categoryName}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item className="mb-0">
            <Button type="primary" htmlType="submit">搜索</Button>
          </Form.Item>
          <Form.Item className="mb-0">
            <Button htmlType="reset">重置</Button>
          </Form.Item>
        </Form>
      </div>

      {/* 任务列表 */}
      <div className="py-3">
        <div className="flex items-center justify-between mb-3">
          <span className="text-base font-medium">每日任务</span>
          <div className="flex gap-2">
            <PermissionWrap perm="daily:task:add">
              <Button size="small" type="primary" onClick={() => add({
                taskType: 'daily',
                status: 'pending',
                isPinned: false,
                sortOrder: 0,
                completionCount: 0,
                iconType: 'calendar'
              })}>
                新增
              </Button>
            </PermissionWrap>
            <Button size="small" type="primary" onClick={() => {
              form.setFieldsValue({ taskType: 'daily', status: 'pending' });
              filter();
            }}>
              待完成
            </Button>
          </div>
        </div>

        <Table
          loading={tableLoading}
          rowKey="taskId"
          tableLayout="auto"
          pagination={false}
          dataSource={list}
          columns={columns}
          size="small"
          scroll={{ x: true, y: `calc(var(--table-wrapper-height) - 120px)` }}
          className="mt-3"
        />

        <TablePagination pagination={pagination} total={total} paginationChange={paginationChange} />
      </div>

      {/* 编辑表单 */}
      <ActionFrom actionData={actionData} url="/daily-task" close={close} update={getList}>
        <DailyTaskForm categories={categories} />
      </ActionFrom>
    </div>
  );
};

function DailyTaskForm({ categories }: { categories: DailyTaskCategory[] }) {
  return (
    <div className="space-y-3">
      <Form.Item
        label="任务标题"
        name="title"
        rules={[{ required: true, message: '请输入任务标题' }]}
      >
        <Input placeholder="请输入任务标题" />
      </Form.Item>

      <Form.Item
        label="任务类型"
        name="taskType"
        rules={[{ required: true, message: '请选择任务类型' }]}
      >
        <Select placeholder="请选择" className="w-full">
          <Select.Option value="daily">每日任务</Select.Option>
          <Select.Option value="once">一次性任务</Select.Option>
          <Select.Option value="long">长期任务</Select.Option>
        </Select>
      </Form.Item>

      <Form.Item label="任务描述" name="description">
        <TextArea placeholder="请输入任务描述" rows={3} />
      </Form.Item>

      <Form.Item label="分类" name="categoryId">
        <Select placeholder="请选择" allowClear className="w-full">
          {categories.map(c => (
            <Select.Option key={c.categoryId} value={c.categoryId}>{c.categoryName}</Select.Option>
          ))}
        </Select>
      </Form.Item>

      <Form.Item label="状态" name="status" rules={[{ required: true, message: '请选择状态' }]}>
        <Select placeholder="请选择" className="w-full">
          <Select.Option value="pending">待完成</Select.Option>
          <Select.Option value="completed">已完成</Select.Option>
          <Select.Option value="disabled">已禁用</Select.Option>
        </Select>
      </Form.Item>

      <div className="flex gap-4">
        <Form.Item label="置顶" name="isPinned" valuePropName="checked" className="flex-1 mb-0">
          <Switch checkedChildren={<PushpinOutlined />} unCheckedChildren={<PushpinOutlined />} />
        </Form.Item>

        <Form.Item label="排序" name="sortOrder" rules={[{ required: true, message: '请输入排序' }]} className="flex-1 mb-0">
          <InputNumber placeholder="数值越小越靠前" min={0} className="w-full" />
        </Form.Item>
      </div>

      <Form.Item label="图标" name="iconType" initialValue="calendar">
        <Input placeholder="图标类型（如：calendar、star等）" />
      </Form.Item>

      <Form.Item label="备注" name="remark">
        <TextArea placeholder="请输入备注" rows={2} />
      </Form.Item>
    </div>
  );
}

export default DailyTaskPage;
