import {FC, useEffect, useState} from "react";
import {Button, Form, Input, Table, TableColumnsType} from "antd";
import {useContentHeight} from "@/hooks/useContentHeight.ts";
import {useAction} from "@/hooks/useAction.ts";
import TableNav from "@/components/TableNav/TableNav.tsx";
import PermissionWrap from "@/components/PermissionWrap/PermissionWrap.tsx";
import ActionFrom from "@/components/ActionFrom/ActionFrom.tsx";
import {useHttp} from "@/hooks/useHttp.ts";
import {FolderOutlined, EditOutlined, DeleteOutlined} from "@ant-design/icons";

const DailyTaskCategoryPage: FC = () => {
  useContentHeight();
  const { httpGet } = useHttp();
  const [categories, setCategories] = useState<DailyTaskCategory[]>([]);
  const [loading, setLoading] = useState(false);

  // 先定义 loadCategories 函数
  const loadCategories = () => {
    setLoading(true);
    httpGet<{ rows: DailyTaskCategory[] }>('/daily-task-category/list', { pageNum: 1, pageSize: 100 })
      .then(res => setCategories(res.rows || []))
      .finally(() => setLoading(false));
  };

  const { remove, actionData, close, add, edit } = useAction<DailyTaskCategory>({
    url: '/daily-task-category',
    update: loadCategories
  });

  useEffect(() => {
    loadCategories();
  }, []);

  const columns: TableColumnsType<DailyTaskCategory> = [
    {
      dataIndex: 'categoryId',
      title: 'ID',
      width: 80,
      className: 'text-gray-500 font-mono text-sm',
    },
    {
      dataIndex: 'categoryName',
      title: '分类名称',
      render: (name: string) => (
        <div className="flex items-center gap-2">
          <span className="p-2 bg-blue-100 rounded-lg">
            <FolderOutlined className="text-blue-500" />
          </span>
          <span className="font-medium text-gray-700">{name}</span>
        </div>
      ),
    },
    {
      dataIndex: 'categoryIcon',
      title: '图标',
      width: 120,
      render: (icon: string) => (
        <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 rounded-md text-sm text-gray-600">
          {icon || '-'}
        </span>
      ),
    },
    {
      dataIndex: 'sortOrder',
      title: '排序',
      width: 100,
      render: (order: number) => (
        <span className="inline-flex items-center justify-center w-8 h-8 bg-primary-100 text-primary-700 rounded-full font-medium text-sm">
          {order}
        </span>
      ),
    },
    {
      dataIndex: 'createTime',
      title: '创建时间',
      width: 180,
      render: (time: string) => (
        <span className="text-gray-500 text-sm">{time}</span>
      ),
    },
    {
      title: "操作",
      key: "operation",
      fixed: "right",
      width: 150,
      render: (_, record) => {
        return (
          <div className="flex gap-2">
            <PermissionWrap perm="daily:category:edit">
              <Button
                size="small"
                type="link"
                onClick={() => edit(record)}
                className="text-primary-600 hover:text-primary-700"
              >
                <EditOutlined className="text-xs mr-1" />
                编辑
              </Button>
            </PermissionWrap>
            <PermissionWrap perm="daily:category:remove">
              <Button
                size="small"
                type="link"
                danger
                onClick={() => remove([record.categoryId])}
                className="text-red-500 hover:text-red-600"
              >
                <DeleteOutlined className="text-xs mr-1" />
                删除
              </Button>
            </PermissionWrap>
          </div>
        );
      },
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      <div className="bg-white rounded-xl shadow-soft p-6">
        <TableNav
          title={<span className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            <FolderOutlined className="text-blue-500" />
            每日任务分类
          </span>}
          add={() => add({ sortOrder: 0, categoryIcon: 'folder' })}
          addPermission="daily:category:add"
        />

        <Table
          loading={loading}
          rowKey="categoryId"
          pagination={false}
          dataSource={categories}
          columns={columns}
          size="middle"
          className="mt-4"
        />
      </div>

      <ActionFrom actionData={actionData} url="/daily-task-category" close={close} update={loadCategories}>
        <CategoryForm />
      </ActionFrom>
    </div>
  );
};

function CategoryForm() {
  return (
    <div className="space-y-4">
      <Form.Item
        label="分类名称"
        name="categoryName"
        rules={[{ required: true, message: '请输入分类名称' }]}
      >
        <Input
          placeholder="请输入分类名称"
          prefix={<FolderOutlined className="text-gray-400" />}
          className="rounded-lg"
        />
      </Form.Item>

      <Form.Item
        label="图标"
        name="categoryIcon"
        rules={[{ required: true, message: '请输入图标' }]}
      >
        <Input
          placeholder="请输入图标（如：folder、star、calendar等）"
          className="rounded-lg"
        />
      </Form.Item>

      <Form.Item
        label="排序"
        name="sortOrder"
        rules={[{ required: true, message: '请输入排序' }]}
      >
        <Input
          type="number"
          placeholder="数值越小越靠前"
          className="rounded-lg"
        />
      </Form.Item>

      <Form.Item label="备注" name="remark">
        <Input.TextArea
          placeholder="请输入备注"
          rows={3}
          className="rounded-lg"
        />
      </Form.Item>
    </div>
  );
}

export default DailyTaskCategoryPage;
