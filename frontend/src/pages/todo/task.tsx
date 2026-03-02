import {FC, useEffect, useState} from "react";
import {Button, Form, Input, Select, Table, TableColumnsType, Tag, DatePicker, Modal} from "antd";
import {useContentHeight} from "@/hooks/useContentHeight.ts";
import {useTable} from "@/hooks/useTable.ts";
import {useAction} from "@/hooks/useAction.ts";
import TableNav from "@/components/TableNav/TableNav.tsx";
import TablePagination from "@/components/TablePagination/TablePagination.tsx";
import PermissionWrap from "@/components/PermissionWrap/PermissionWrap.tsx";
import ActionFrom from "@/components/ActionFrom/ActionFrom.tsx";
import {useHttp} from "@/hooks/useHttp.ts";
import dayjs from "dayjs";

const { RangePicker } = DatePicker;

const TodoTaskPage: FC = () => {
  useContentHeight();
  const [form] = Form.useForm();
  const { httpGet, httpPatch } = useHttp();
  const [categories, setCategories] = useState<BizTaskCategory[]>([]);

  const { list, getList, filter, pagination, paginationChange, tableLoading, total } = useTable<BizTask>(form, '/todo/task/list');
  const { remove, actionData, close, add, edit } = useAction<BizTask>({ url: '/todo/task', update: getList });

  // 加载分类列表
  useEffect(() => {
    httpGet<{ rows: BizTaskCategory[] }>('/todo/task/category/list', { pageNum: 1, pageSize: 100 })
      .then(res => setCategories(res.rows || []));
  }, [httpGet]);

  useEffect(() => {
    getList();
  }, [getList]);

  // 完成任务
  const completeTask = async (taskId: number) => {
    await httpPatch(`/todo/task/${taskId}/complete`);
    getList();
  };

  // 重开任务
  const reopenTask = async (taskId: number) => {
    await httpPatch(`/todo/task/${taskId}/reopen`);
    getList();
  };

  const columns: TableColumnsType<BizTask> = [
    {
      dataIndex: 'taskId',
      title: 'ID',
      width: 80,
    },
    {
      dataIndex: 'taskTitle',
      title: '任务标题',
      ellipsis: true,
    },
    {
      dataIndex: 'taskType',
      title: '类型',
      width: 80,
      render: (type) => {
        return type === '2' ? <Tag color="blue">Todo</Tag> : <Tag>任务</Tag>;
      }
    },
    {
      dataIndex: 'priority',
      title: '优先级',
      width: 100,
      render: (priority) => {
        const config = {
          '0': { color: 'default', text: '低' },
          '1': { color: 'blue', text: '中' },
          '2': { color: 'red', text: '高' },
        };
        const { color, text } = config[priority as keyof typeof config] || config['1'];
        return <Tag color={color}>{text}</Tag>;
      }
    },
    {
      dataIndex: 'status',
      title: '状态',
      width: 100,
      render: (status) => {
        return status === '1' ? <Tag color="green">已完成</Tag> : <Tag color="orange">待办</Tag>;
      }
    },
    {
      dataIndex: 'dueDate',
      title: '截止日期',
      width: 120,
    },
    {
      dataIndex: 'categoryId',
      title: '分类',
      width: 120,
      render: (categoryId) => {
        const category = categories.find(c => c.categoryId === categoryId);
        return category?.categoryName || '-';
      }
    },
    {
      dataIndex: 'createTime',
      title: '创建时间',
      width: 180,
    },
    {
      title: "操作",
      key: "operation",
      fixed: "right",
      width: 200,
      render: (_, record) => {
        return (
          <>
            <PermissionWrap perm="todo:task:edit">
              {record.status === '0' ? (
                <Button size="small" type="link" onClick={() => completeTask(record.taskId)}>完成</Button>
              ) : (
                <Button size="small" type="link" onClick={() => reopenTask(record.taskId)}>重开</Button>
              )}
              <Button size="small" type="link" onClick={() => edit(record)}>编辑</Button>
            </PermissionWrap>
            <PermissionWrap perm="todo:task:remove">
              <Button size="small" type="link" danger onClick={() => remove([record.taskId])}>删除</Button>
            </PermissionWrap>
          </>
        );
      },
    },
  ];

  return (
    <div className="page-container table-page">
      <div className="form-wrap">
        <Form layout="inline" form={form} onFinish={filter} onReset={filter}>
          <Form.Item label="任务标题" name="taskTitle">
            <Input placeholder="请输入任务标题" style={{width: 200}} />
          </Form.Item>
          <Form.Item label="类型" name="taskType">
            <Select style={{width: 120}} placeholder="请选择" allowClear>
              <Select.Option value="1">任务</Select.Option>
              <Select.Option value="2">Todo</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="优先级" name="priority">
            <Select style={{width: 100}} placeholder="请选择" allowClear>
              <Select.Option value="0">低</Select.Option>
              <Select.Option value="1">中</Select.Option>
              <Select.Option value="2">高</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="状态" name="status">
            <Select style={{width: 100}} placeholder="请选择" allowClear>
              <Select.Option value="0">待办</Select.Option>
              <Select.Option value="1">已完成</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">搜索</Button>
          </Form.Item>
          <Form.Item>
            <Button htmlType="reset">重置</Button>
          </Form.Item>
        </Form>
      </div>

      <div className="table-wrapper">
        <TableNav title="任务列表" add={() => add({ taskType: '2', status: '0', priority: '1' })} addPermission="todo:task:add">
          <Button type="primary" size="small" onClick={() => { form.setFieldsValue({ taskType: '2' }); filter(); }}>只看Todo</Button>
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
        />

        <TablePagination pagination={pagination} total={total} paginationChange={paginationChange} />
      </div>

      <ActionFrom actionData={actionData} url="/todo/task" close={close} update={getList}>
        <TaskForm categories={categories} />
      </ActionFrom>
    </div>
  );
};

function TaskForm({ categories }: { categories: BizTaskCategory[] }) {
  return (
    <>
      <Form.Item label="任务标题" name="taskTitle" rules={[{ required: true, message: '请输入任务标题' }]}>
        <Input placeholder="请输入任务标题" />
      </Form.Item>
      <Form.Item label="类型" name="taskType" rules={[{ required: true, message: '请选择类型' }]}>
        <Select style={{width: '100%'}} placeholder="请选择类型">
          <Select.Option value="1">任务</Select.Option>
          <Select.Option value="2">Todo</Select.Option>
        </Select>
      </Form.Item>
      <Form.Item label="分类" name="categoryId">
        <Select style={{width: '100%'}} placeholder="请选择分类" allowClear>
          {categories.map(c => (
            <Select.Option key={c.categoryId} value={c.categoryId}>{c.categoryName}</Select.Option>
          ))}
        </Select>
      </Form.Item>
      <Form.Item label="优先级" name="priority" rules={[{ required: true, message: '请选择优先级' }]}>
        <Select style={{width: '100%'}} placeholder="请选择优先级">
          <Select.Option value="0">低</Select.Option>
          <Select.Option value="1">中</Select.Option>
          <Select.Option value="2">高</Select.Option>
        </Select>
      </Form.Item>
      <Form.Item label="状态" name="status" rules={[{ required: true, message: '请选择状态' }]}>
        <Select style={{width: '100%'}} placeholder="请选择状态">
          <Select.Option value="0">待办</Select.Option>
          <Select.Option value="1">已完成</Select.Option>
        </Select>
      </Form.Item>
      <Form.Item label="截止日期" name="dueDate">
        <DatePicker style={{width: '100%'}} showTime format="YYYY-MM-DD HH:mm:ss" />
      </Form.Item>
      <Form.Item label="任务内容" name="taskContent">
        <Input.TextArea placeholder="请输入任务内容" rows={6} />
      </Form.Item>
    </>
  );
}

export default TodoTaskPage;
