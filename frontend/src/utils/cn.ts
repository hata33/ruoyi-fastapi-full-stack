import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * 合并 Tailwind CSS 类名
 * 使用 clsx 处理条件类名，使用 tailwind-merge 解决类名冲突
 *
 * @example
 * cn("px-2 py-1", "px-4") // => "py-1 px-4"
 * cn("text-lg", someCondition && "text-xl") // => "text-lg" 或 "text-xl"
 * cn({ "bg-red-500": isError }, "text-white") // => "bg-red-500 text-white" 或 "text-white"
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
