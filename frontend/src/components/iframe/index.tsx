/**
 * Iframe组件
 * 用于嵌入外部链接或内部页面
 */

import { FC, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { Card } from "antd";

const Iframe: FC = () => {
  const [searchParams] = useSearchParams();

  // 从URL参数中获取要嵌入的链接
  const url = useMemo(() => {
    return searchParams.get("url") || "";
  }, [searchParams]);

  if (!url) {
    return (
      <Card>
        <div style={{ textAlign: "center", padding: "40px" }}>
          <p>无效的链接</p>
        </div>
      </Card>
    );
  }

  return (
    <Card
      bodyStyle={{ padding: 0 }}
      style={{ height: "100%", margin: -16 }}
    >
      <iframe
        src={url}
        style={{
          width: "100%",
          height: "calc(100vh - 140px)",
          border: "none",
        }}
        title="iframe"
      />
    </Card>
  );
};

export default Iframe;
