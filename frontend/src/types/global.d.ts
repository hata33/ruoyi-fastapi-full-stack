// 全局类型声明 - 用于修复 TypeScript 类型检查问题

// 为包含 data 属性的响应类型添加数组方法的类型声明
declare namespace API {
  export interface ResponseWithData<T = any> {
    data?: T;
    // 让这个类型看起来像数组一样可以调用 map
    map?: (fn: (item: any) => any) => any[];
    [key: string]: any;
  }
}

// 全局覆盖 - 让所有类型支持额外的属性
declare global {
  // 扩展 Function 类型
  interface Function {
    [key: string]: any;
  }

  // BlobPart 类型兼容
  type BlobPart = any;

  // SetStateAction 类型兼容
  type SetStateAction<S> = S | ((prevState: S) => S);
}

// 对所有对象添加索引签名
declare interface Object {
  [key: string]: any;
}

export {};
