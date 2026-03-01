import {FC, useEffect, useState} from "react";
import {Button, Form, Input, Table, TableColumnsType, Space} from "antd";
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
      width: 60,
      className: 'text-gray-400 font-mono text-xs',
    },
    {
      dataIndex: 'categoryName',
      title: '分类名称',
      render: (name: string) => (
        <div className="flex items-center gap-2">
          <FolderOutlined className="text-gray-400 text-xs" />
          <span className="text-sm">{name}</span>
        </div>
      ),
    },
    {
      dataIndex: 'categoryIcon',
      title: '图标',
      width: 100,
      render: (icon: string) => (
        <span className="text-xs text-gray-500">{icon || '-'}</span>
      ),
    },
    {
      dataIndex: 'sortOrder',
      title: '排序',
      width: 80,
      render: (order: number) => (
        <span className="text-xs text-gray-500">{order}</span>
      ),
    },
    {
      dataIndex: 'createTime',
      title: '创建时间',
      width: 160,
      render: (time: string) => (
        <span className="text-xs text-gray-400">{time}</span>
      ),
    },
    {
      title: "操作",
      key: "operation",
      fixed: "right",
      width: 120,
      render: (_, record) => {
        return (
          <Space size={4}>
            <PermissionWrap perm="daily:category:edit">
              <Button
                size="small"
                type="link"
                onClick={() => edit(record)}
              >
                编辑
              </Button>
            </PermissionWrap>
            <PermissionWrap perm="daily:category:remove">
              <Button
                size="small"
                type="link"
                danger
                onClick={() => remove([record.categoryId])}
              >
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
      <div>
        <TableNav
          title="每日任务分类"
          add={() => add({ sortOrder: 0, categoryIcon: 'folder' })}
          addPermission="daily:category:add"
        />

        <Table
          loading={loading}
          rowKey="categoryId"
          pagination={false}
          dataSource={categories}
          columns={columns}
          size="small"
          className="mt-3"
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
    <div className="space-y-3">
      <Form.Item
        label="分类名称"
        name="categoryName"
        rules={[{ required: true, message: '请输入分类名称' }]}
      >
        <Input placeholder="请输入分类名称" />
      </Form.Item>

      <Form.Item
        label="图标"
        name="categoryIcon"
        rules={[{ required: true, message: '请输入图标' }]}
      >
        <Input placeholder="图标（如：folder、star等）" />
      </Form.Item>

      <Form.Item
        label="排序"
        name="sortOrder"
        rules={[{ required: true, message: '请输入排序' }]}
      >
        <Input
          type="number"
          placeholder="数值越小越靠前"
        />
      </Form.Item>

      <Form.Item label="备注" name="remark">
        <Input.TextArea
          placeholder="请输入备注"
          rows={2}
        />
      </Form.Item>
    </div>
  );
}

export default DailyTaskCategoryPage;
