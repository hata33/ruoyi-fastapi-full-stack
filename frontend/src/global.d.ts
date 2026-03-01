interface Dict {
  label: string
  value: string
  listClass: string
}

interface Pagination {
  pageNum: number
  pageSize: number
}

interface Menu {
  menuId: number
  parentId: number
  menuType: 'M' | 'C' | 'F'
  menuName: string
  icon?: string
  orderNum: number
  path?: string
  perms?: string
  visible: string
  status: string
  children: Menu[] | null
}

interface User {
  admin: boolean
  userId: number
  userName: string
  deptId: number
  dept: {
    deptName: string
  }
  phonenumber: string
  email: string
  sex: string
  status: string
  postIds: number[] | null
  roleIds: number[] | null
}


interface Role {
  roleId: number
  roleName: string
  roleKey: string
  roleSort: number
  status: string
  remark: string
  admin: boolean
}

interface Dept {
  deptId: number
  parentId: number
  deptName: string
  leader: string
  orderNum: number
  status: string
  email: string
  phone: string
  createTime: string
  children: Dept[] | null
}

interface Dict {
  dictId: number
  dictName: string
  dictType: string
  remark: string
  status: string
  createTime: string
  createBy: string
}


interface DictData {
  dictCode: number
  dictValue: string
  dictLabel: string
  dictSort: number
  listClass: string
  status: string
  remark: string
  createBy: string
  createTime: string
}

interface Post {
  postId: number
  postName: string
  postCode: string
  createTime: string
  postSort: number
  status: string
  remark: string
}

interface SysConfig {
  configId: number
  configKey: string
  configName: string
  configType: string
  configValue: string
  createTime: string
  remark: string
}

interface SysNotice {
  noticeId: number
  noticeTitle: string
  noticeType: string
  status: string
  noticeContent: string
  createBy: string
}

interface OperationLog {
  operId: number
  title: string
  businessType: string
  operName: string
  operIp: string
  operLocation: string
  status: string
  operTime: string
  costTime: string
}


interface LoginLog {
  infoId: number
  userName: string
  ipaddr: string
  loginLocation: string
  browser: string
  os: string
  status: string
  msg: string
  loginTime: string
}

interface CodeGen {
  tableId: number
  tableName: string
  tableComment: string
  className: string
  createTime: string
  updateTime: string
  businessName: string
}

interface FieldInfo {
  columnName: string
  columnComment: string
  columnType: string
  javaType: string
  javaField: string
  isInsert: string
  isEdit: string
  isList: string
  isQuery: string
  queryType: string
  isRequired: string
  htmlType: string
  dictType: string
}

// Todo 模块类型定义
interface BizNote {
  noteId: number
  noteTitle: string
  noteContent: string
  categoryId: number
  userId: number
  status: string
  createBy: string
  createTime: string
  updateTime: string
  remark: string
}

interface BizNoteCategory {
  categoryId: number
  categoryName: string
  userId: number
  sortOrder: number
  createBy: string
  createTime: string
  updateTime: string
  remark: string
}

interface BizTask {
  taskId: number
  taskTitle: string
  taskContent: string
  categoryId: number
  userId: number
  taskType: string  // 1=任务 2=Todo
  status: string    // 0=待办 1=已完成
  priority: string  // 0=低 1=中 2=高
  dueDate: string
  completedAt: string
  createBy: string
  createTime: string
  updateTime: string
  remark: string
}

interface BizTaskCategory {
  categoryId: number
  categoryName: string
  userId: number
  sortOrder: number
  createBy: string
  createTime: string
  updateTime: string
  remark: string
}

// 每日任务模块类型定义
interface DailyTask {
  taskId: number
  title: string
  description: string
  taskType: 'daily' | 'once' | 'long'
  status: 'pending' | 'completed' | 'disabled'
  isPinned: boolean
  sortOrder: number
  completionCount: number
  iconType: string
  userId: number
  categoryId: number
  lastCompletedAt: string
  disabledAt: string
  createBy: string
  createTime: string
  updateBy: string
  updateTime: string
  remark: string
  categoryName?: string
}

interface DailyTaskCategory {
  categoryId: number
  categoryName: string
  categoryIcon: string
  sortOrder: number
  userId: number
  createBy: string
  createTime: string
  updateBy: string
  updateTime: string
  remark: string
}
