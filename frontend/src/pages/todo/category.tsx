import {FC, useEffect, useState} from "react";
import {Button, Form, Input, Table, TableColumnsType, Tabs} from "antd";
import {useContentHeight} from "@/hooks/useContentHeight.ts";
import {useAction} from "@/hooks/useAction.ts";
import TableNav from "@/components/TableNav/TableNav.tsx";
import PermissionWrap from "@/components/PermissionWrap/PermissionWrap.tsx";
import ActionFrom from "@/components/ActionFrom/ActionFrom.tsx";
import {useHttp} from "@/hooks/useHttp.ts";

const TodoCategoryPage: FC = () => {
  useContentHeight();
  const { httpGet, httpDelete } = useHttp();
  const [activeTab, setActiveTab] = useState('note');
  const [noteCategories, setNoteCategories] = useState<BizNoteCategory[]>([]);
  const [taskCategories, setTaskCategories] = useState<BizTaskCategory[]>([]);
  const [loading, setLoading] = useState(false);

  const { remove: removeNoteCategory, actionData: noteActionData, close: closeNote, add: addNote, edit: editNote } = useAction<BizNoteCategory>({ url: '/todo/note/category', update: loadNoteCategories });
  const { remove: removeTaskCategory, actionData: taskActionData, close: closeTask, add: addTask, edit: editTask } = useAction<BizTaskCategory>({ url: '/todo/task/category', update: loadTaskCategories });

  const loadNoteCategories = () => {
    setLoading(true);
    httpGet<{ rows: BizNoteCategory[] }>('/todo/note/category/list', { pageNum: 1, pageSize: 100 })
      .then(res => setNoteCategories(res.rows || []))
      .finally(() => setLoading(false));
  };

  const loadTaskCategories = () => {
    setLoading(true);
    httpGet<{ rows: BizTaskCategory[] }>('/todo/task/category/list', { pageNum: 1, pageSize: 100 })
      .then(res => setTaskCategories(res.rows || []))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (activeTab === 'note') {
      loadNoteCategories();
    } else {
      loadTaskCategories();
    }
  }, [activeTab]);

  const noteColumns: TableColumnsType<BizNoteCategory> = [
    {
      dataIndex: 'categoryId',
      title: 'ID',
      width: 80,
    },
    {
      dataIndex: 'categoryName',
      title: '分类名称',
    },
    {
      dataIndex: 'sortOrder',
      title: '排序',
      width: 100,
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
        return (
          <>
            <PermissionWrap perm="todo:note:category:edit">
              <Button size="small" type="link" onClick={() => editNote(record)}>编辑</Button>
            </PermissionWrap>
            <PermissionWrap perm="todo:note:category:remove">
              <Button size="small" type="link" danger onClick={() => removeNoteCategory([record.categoryId])}>删除</Button>
            </PermissionWrap>
          </>
        );
      },
    },
  ];

  const taskColumns: TableColumnsType<BizTaskCategory> = [
    {
      dataIndex: 'categoryId',
      title: 'ID',
      width: 80,
    },
    {
      dataIndex: 'categoryName',
      title: '分类名称',
    },
    {
      dataIndex: 'sortOrder',
      title: '排序',
      width: 100,
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
        return (
          <>
            <PermissionWrap perm="todo:task:category:edit">
              <Button size="small" type="link" onClick={() => editTask(record)}>编辑</Button>
            </PermissionWrap>
            <PermissionWrap perm="todo:task:category:remove">
              <Button size="small" type="link" danger onClick={() => removeTaskCategory([record.categoryId])}>删除</Button>
            </PermissionWrap>
          </>
        );
      },
    },
  ];

  return (
    <div className="page-container table-page">
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'note',
            label: '记事分类',
            children: (
              <div className="table-wrapper" style={{marginTop: 16}}>
                <TableNav title="记事分类" add={() => addNote({ sortOrder: 0 })} addPermission="todo:note:category:add" />
                <Table
                  loading={loading}
                  rowKey="categoryId"
                  pagination={false}
                  dataSource={noteCategories}
                  columns={noteColumns}
                  size="middle"
                />
              </div>
            ),
          },
          {
            key: 'task',
            label: '任务分类',
            children: (
              <div className="table-wrapper" style={{marginTop: 16}}>
                <TableNav title="任务分类" add={() => addTask({ sortOrder: 0 })} addPermission="todo:task:category:add" />
                <Table
                  loading={loading}
                  rowKey="categoryId"
                  pagination={false}
                  dataSource={taskCategories}
                  columns={taskColumns}
                  size="middle"
                />
              </div>
            ),
          },
        ]}
      />

      <ActionFrom actionData={noteActionData} url="/todo/note/category" close={closeNote} update={loadNoteCategories}>
        <Form.Item label="分类名称" name="categoryName" rules={[{ required: true, message: '请输入分类名称' }]}>
          <Input placeholder="请输入分类名称" />
        </Form.Item>
        <Form.Item label="排序" name="sortOrder" rules={[{ required: true, message: '请输入排序' }]}>
          <Input type="number" placeholder="请输入排序" />
        </Form.Item>
      </ActionFrom>

      <ActionFrom actionData={taskActionData} url="/todo/task/category" close={closeTask} update={loadTaskCategories}>
        <Form.Item label="分类名称" name="categoryName" rules={[{ required: true, message: '请输入分类名称' }]}>
          <Input placeholder="请输入分类名称" />
        </Form.Item>
        <Form.Item label="排序" name="sortOrder" rules={[{ required: true, message: '请输入排序' }]}>
          <Input type="number" placeholder="请输入排序" />
        </Form.Item>
      </ActionFrom>
    </div>
  );
};

export default TodoCategoryPage;
