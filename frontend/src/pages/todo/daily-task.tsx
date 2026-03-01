import {FC, useEffect, useState} from "react";
import {
  Button,
  Form,
  Input,
  Select,
  Table,
  TableColumnsType,
  Tag,
  Space,
  Switch,
  InputNumber,
  Modal
} from "antd";
import {useContentHeight} from "@/hooks/useContentHeight.ts";
import {useTable} from "@/hooks/useTable.ts";
import {useAction} from "@/hooks/useAction.ts";
import TableNav from "@/components/TableNav/TableNav.tsx";
import TablePagination from "@/components/TablePagination/TablePagination.tsx";
import PermissionWrap from "@/components/PermissionWrap/PermissionWrap.tsx";
import ActionFrom from "@/components/ActionFrom/ActionFrom.tsx";
import {useHttp} from "@/hooks/useHttp.ts";
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  StopOutlined,
  PushpinOutlined,
  FolderOutlined,
  CalendarOutlined,
  StarOutlined
} from "@ant-design/icons";

const { TextArea } = Input;

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

  // 获取任务类型样式
  const getTaskTypeStyle = (type: 'daily' | 'once' | 'long') => {
    const config = {
      daily: { color: 'bg-blue-100 text-blue-700 border-blue-200', text: '每日' },
      once: { color: 'bg-green-100 text-green-700 border-green-200', text: '一次性' },
      long: { color: 'bg-purple-100 text-purple-700 border-purple-200', text: '长期' },
    };
    return config[type] || config.daily;
  };

  // 获取状态样式
  const getStatusStyle = (status: 'pending' | 'completed' | 'disabled') => {
    const config = {
      pending: { color: 'bg-orange-100 text-orange-700 border-orange-200', text: '待完成' },
      completed: { color: 'bg-emerald-100 text-emerald-700 border-emerald-200', text: '已完成' },
      disabled: { color: 'bg-gray-100 text-gray-500 border-gray-200', text: '已禁用' },
    };
    return config[status] || config.pending;
  };

  const columns: TableColumnsType<DailyTask> = [
    {
      dataIndex: 'taskId',
      title: 'ID',
      width: 80,
      className: 'text-gray-500 font-mono text-sm',
    },
    {
      dataIndex: 'title',
      title: '任务标题',
      ellipsis: true,
      width: 200,
      render: (title: string, record: DailyTask) => (
        <div className="flex items-center gap-2">
          {record.isPinned && <PushpinOutlined className="text-red-500 text-xs" />}
          <span className={record.status === 'completed' ? 'line-through text-gray-400' : ''}>{title}</span>
        </div>
      ),
    },
    {
      dataIndex: 'taskType',
      title: '类型',
      width: 100,
      render: (type: 'daily' | 'once' | 'long') => {
        const style = getTaskTypeStyle(type);
        return (
          <span className={`px-2 py-1 rounded-full text-xs font-medium border ${style.color}`}>
            {style.text}
          </span>
        );
      }
    },
    {
      dataIndex: 'status',
      title: '状态',
      width: 100,
      render: (status: 'pending' | 'completed' | 'disabled') => {
        const style = getStatusStyle(status);
        return (
          <span className={`px-2 py-1 rounded-full text-xs font-medium border ${style.color}`}>
            {style.text}
          </span>
        );
      }
    },
    {
      dataIndex: 'completionCount',
      title: '完成次数',
      width: 100,
      render: (count: number) => (
        <span className="inline-flex items-center gap-1">
          <CheckCircleOutlined className="text-emerald-500 text-xs" />
          <span className="font-medium text-gray-700">{count || 0}</span>
        </span>
      ),
    },
    {
      dataIndex: 'categoryId',
      title: '分类',
      width: 120,
      render: (categoryId: number) => {
        const category = categories.find(c => c.categoryId === categoryId);
        return category ? (
          <span className="inline-flex items-center gap-1 text-gray-600">
            <FolderOutlined className="text-xs" />
            {category.categoryName}
          </span>
        ) : '-';
      }
    },
    {
      dataIndex: 'sortOrder',
      title: '排序',
      width: 80,
      render: (order: number) => (
        <span className="text-gray-500 font-mono text-sm">{order}</span>
      ),
    },
    {
      dataIndex: 'lastCompletedAt',
      title: '最后完成',
      width: 180,
      render: (time: string) => time ? (
        <span className="text-gray-500 text-sm">{time}</span>
      ) : (
        <span className="text-gray-400 text-sm">从未完成</span>
      ),
    },
    {
      title: "操作",
      key: "operation",
      fixed: "right",
      width: 280,
      render: (_, record) => {
        return (
          <Space size="small" className="flex-wrap">
            <PermissionWrap perm="daily:task:edit">
              {record.status === 'pending' && (
                <Button
                  size="small"
                  type="link"
                  onClick={() => completeTask(record.taskId)}
                  className="text-emerald-600 hover:text-emerald-700"
                >
                  <CheckCircleOutlined className="text-xs mr-1" />
                  完成
                </Button>
              )}
              {record.status === 'completed' && (
                <Button
                  size="small"
                  type="link"
                  onClick={() => reopenTask(record.taskId)}
                  className="text-orange-600 hover:text-orange-700"
                >
                  <ClockCircleOutlined className="text-xs mr-1" />
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
              <Button
                size="small"
                type="link"
                onClick={() => togglePin(record.taskId, record.isPinned)}
                className={record.isPinned ? 'text-red-500' : ''}
              >
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
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      {/* 筛选表单 */}
      <div className="bg-white rounded-xl shadow-soft mb-6 p-6">
        <Form layout="inline" form={form} onFinish={filter} onReset={filter} className="flex flex-wrap gap-4">
          <Form.Item label="任务标题" name="title" className="mb-0">
            <Input
              placeholder="请输入任务标题"
              className="w-48"
              allowClear
            />
          </Form.Item>
          <Form.Item label="任务类型" name="taskType" className="mb-0">
            <Select placeholder="请选择" allowClear className="w-32">
              <Select.Option value="daily">每日任务</Select.Option>
              <Select.Option value="once">一次性任务</Select.Option>
              <Select.Option value="long">长期任务</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="状态" name="status" className="mb-0">
            <Select placeholder="请选择" allowClear className="w-32">
              <Select.Option value="pending">待完成</Select.Option>
              <Select.Option value="completed">已完成</Select.Option>
              <Select.Option value="disabled">已禁用</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="分类" name="categoryId" className="mb-0">
            <Select placeholder="请选择" allowClear className="w-36">
              {categories.map(c => (
                <Select.Option key={c.categoryId} value={c.categoryId}>{c.categoryName}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item className="mb-0">
            <Button
              type="primary"
              htmlType="submit"
              className="bg-primary-500 hover:bg-primary-600 border-primary-500"
            >
              搜索
            </Button>
          </Form.Item>
          <Form.Item className="mb-0">
            <Button htmlType="reset" className="border-gray-300">
              重置
            </Button>
          </Form.Item>
        </Form>
      </div>

      {/* 任务列表 */}
      <div className="bg-white rounded-xl shadow-soft p-6">
        <TableNav
          title={<span className="text-lg font-semibold text-gray-800">每日任务列表</span>}
          add={() => add({
            taskType: 'daily',
            status: 'pending',
            isPinned: false,
            sortOrder: 0,
            completionCount: 0,
            iconType: 'calendar'
          })}
          addPermission="daily:task:add"
        >
          <Button
            type="primary"
            size="small"
            onClick={() => {
              form.setFieldsValue({ taskType: 'daily', status: 'pending' });
              filter();
            }}
            className="bg-emerald-500 hover:bg-emerald-600 border-emerald-500"
          >
            待完成
          </Button>
        </TableNav>

        <Table
          loading={tableLoading}
          rowKey="taskId"
          tableLayout="auto"
          pagination={false}
          dataSource={list}
          columns={columns}
          size="middle"
          scroll={{x: true, y: `calc(var(--table-wrapper-height) - 150px)`}}
          className="mt-4"
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
    <div className="space-y-4">
      <Form.Item
        label="任务标题"
        name="title"
        rules={[{ required: true, message: '请输入任务标题' }]}
      >
        <Input
          placeholder="请输入任务标题"
          className="rounded-lg"
        />
      </Form.Item>

      <Form.Item
        label="任务类型"
        name="taskType"
        rules={[{ required: true, message: '请选择任务类型' }]}
      >
        <Select placeholder="请选择任务类型" className="w-full">
          <Select.Option value="daily">
            <span className="flex items-center gap-2">
              <CalendarOutlined className="text-blue-500" />
              每日任务
            </span>
          </Select.Option>
          <Select.Option value="once">
            <span className="flex items-center gap-2">
              <CheckCircleOutlined className="text-green-500" />
              一次性任务
            </span>
          </Select.Option>
          <Select.Option value="long">
            <span className="flex items-center gap-2">
              <StarOutlined className="text-purple-500" />
              长期任务
            </span>
          </Select.Option>
        </Select>
      </Form.Item>

      <Form.Item label="任务描述" name="description">
        <TextArea
          placeholder="请输入任务描述"
          rows={4}
          className="rounded-lg"
        />
      </Form.Item>

      <Form.Item label="分类" name="categoryId">
        <Select placeholder="请选择分类" allowClear className="w-full">
          {categories.map(c => (
            <Select.Option key={c.categoryId} value={c.categoryId}>
              <span className="flex items-center gap-2">
                <FolderOutlined />
                {c.categoryName}
              </span>
            </Select.Option>
          ))}
        </Select>
      </Form.Item>

      <Form.Item
        label="状态"
        name="status"
        rules={[{ required: true, message: '请选择状态' }]}
      >
        <Select placeholder="请选择状态" className="w-full">
          <Select.Option value="pending">
            <span className="px-2 py-1 rounded-full text-xs bg-orange-100 text-orange-700 border border-orange-200">
              待完成
            </span>
          </Select.Option>
          <Select.Option value="completed">
            <span className="px-2 py-1 rounded-full text-xs bg-emerald-100 text-emerald-700 border border-emerald-200">
              已完成
            </span>
          </Select.Option>
          <Select.Option value="disabled">
            <span className="px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-500 border border-gray-200">
              已禁用
            </span>
          </Select.Option>
        </Select>
      </Form.Item>

      <div className="flex gap-6">
        <Form.Item label="是否置顶" name="isPinned" valuePropName="checked" className="flex-1">
          <Switch checkedChildren={<PushpinOutlined />} unCheckedChildren={<PushpinOutlined />} />
        </Form.Item>

        <Form.Item
          label="排序"
          name="sortOrder"
          rules={[{ required: true, message: '请输入排序' }]}
          className="flex-1"
        >
          <InputNumber
            placeholder="数值越小越靠前"
            min={0}
            className="w-full"
          />
        </Form.Item>
      </div>

      <Form.Item label="图标类型" name="iconType" initialValue="calendar">
        <Input placeholder="请输入图标类型（如：calendar、star、check等）" />
      </Form.Item>

      <Form.Item label="备注" name="remark">
        <TextArea
          placeholder="请输入备注"
          rows={3}
          className="rounded-lg"
        />
      </Form.Item>
    </div>
  );
}

export default DailyTaskPage;
