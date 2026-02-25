import {FC, useEffect, useState} from "react";
import {Button, Form, Input, Select, Table, TableColumnsType, Tag} from "antd";
import {useContentHeight} from "@/hooks/useContentHeight.ts";
import {useTable} from "@/hooks/useTable.ts";
import {useAction} from "@/hooks/useAction.ts";
import TableNav from "@/components/TableNav/TableNav.tsx";
import TablePagination from "@/components/TablePagination/TablePagination.tsx";
import PermissionWrap from "@/components/PermissionWrap/PermissionWrap.tsx";
import ActionFrom from "@/components/ActionFrom/ActionFrom.tsx";
import {useHttp} from "@/hooks/useHttp.ts";

const TodoNotePage: FC = () => {
  useContentHeight();
  const [form] = Form.useForm();
  const { httpGet } = useHttp();
  const [categories, setCategories] = useState<BizNoteCategory[]>([]);

  const { list, getList, filter, pagination, paginationChange, tableLoading, total } = useTable<BizNote>(form, '/todo/note/list');
  const { remove, actionData, close, add, edit } = useAction<BizNote>({ url: '/todo/note', update: getList });

  // 加载分类列表
  useEffect(() => {
    httpGet<{ rows: BizNoteCategory[] }>('/todo/note/category/list', { pageNum: 1, pageSize: 100 })
      .then(res => setCategories(res.rows || []));
  }, [httpGet]);

  useEffect(() => {
    getList();
  }, [getList]);

  const columns: TableColumnsType<BizNote> = [
    {
      dataIndex: 'noteId',
      title: 'ID',
      width: 80,
    },
    {
      dataIndex: 'noteTitle',
      title: '标题',
      ellipsis: true,
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
      dataIndex: 'status',
      title: '状态',
      width: 80,
      render: (status) => {
        return status === '0' ? <Tag color="green">正常</Tag> : <Tag color="red">关闭</Tag>;
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
      width: 150,
      render: (_, record) => {
        return <>
          <PermissionWrap perm="todo:note:edit">
            <Button size="small" type="link" onClick={() => edit(record)}>编辑</Button>
          </PermissionWrap>
          <PermissionWrap perm="todo:note:remove">
            <Button size="small" type="link" danger onClick={() => remove([record.noteId])}>删除</Button>
          </PermissionWrap>
        </>
      },
    },
  ];

  return (
    <div className="page-container table-page">
      <div className="form-wrap">
        <Form layout="inline" form={form} onFinish={filter} onReset={filter}>
          <Form.Item label="标题" name="noteTitle">
            <Input placeholder="请输入标题" style={{width: 200}} />
          </Form.Item>
          <Form.Item label="状态" name="status">
            <Select style={{width: 120}} placeholder="请选择" allowClear>
              <Select.Option value="0">正常</Select.Option>
              <Select.Option value="1">关闭</Select.Option>
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
        <TableNav title="记事列表" add={() => add({ status: '0' })} addPermission="todo:note:add" />

        <Table
          loading={tableLoading}
          rowKey="noteId"
          tableLayout="auto"
          pagination={false}
          dataSource={list}
          columns={columns}
          size="middle"
          scroll={{x: true, y: `calc(var(--table-wrapper-height) - 150px)`}}
        />

        <TablePagination pagination={pagination} total={total} paginationChange={paginationChange} />
      </div>

      <ActionFrom actionData={actionData} url="/todo/note" close={close} update={getList}>
        <NoteForm categories={categories} />
      </ActionFrom>
    </div>
  );
};

function NoteForm({ categories }: { categories: BizNoteCategory[] }) {
  return (
    <>
      <Form.Item label="标题" name="noteTitle" rules={[{ required: true, message: '请输入标题' }]}>
        <Input placeholder="请输入标题" />
      </Form.Item>
      <Form.Item label="分类" name="categoryId">
        <Select style={{width: '100%'}} placeholder="请选择分类" allowClear>
          {categories.map(c => (
            <Select.Option key={c.categoryId} value={c.categoryId}>{c.categoryName}</Select.Option>
          ))}
        </Select>
      </Form.Item>
      <Form.Item label="状态" name="status">
        <Select style={{width: '100%'}} placeholder="请选择状态">
          <Select.Option value="0">正常</Select.Option>
          <Select.Option value="1">关闭</Select.Option>
        </Select>
      </Form.Item>
      <Form.Item label="内容" name="noteContent">
        <Input.TextArea placeholder="请输入内容" rows={6} />
      </Form.Item>
    </>
  );
}

export default TodoNotePage;
