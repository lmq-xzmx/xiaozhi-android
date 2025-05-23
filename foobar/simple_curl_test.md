# 🔧 简单的OTA接口测试命令

## 复制以下命令到任何终端执行：

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Device-Id: aa:bb:cc:dd:ee:ff" \
  -H "Client-Id: android-test" \
  -d '{"macAddress":"aa:bb:cc:dd:ee:ff","application":{"version":"1.0.0"},"board":{"type":"android"},"chipModelName":"android"}' \
  http://47.122.144.73:8002/xiaozhi/ota/
```

## 预期结果：

### 成功情况1（需要激活）：
```json
{
  "activation": {
    "code": "123456",
    "message": "http://47.122.144.73:8002\n123456"
  }
}
```
**→ 记下激活码，去管理面板绑定**

### 成功情况2（已绑定）：
```json
{
  "websocket": {
    "url": "ws://47.122.144.73:8000/xiaozhi/v1/"
  }
}
```
**→ 设备已绑定，可以直接使用**

### 失败情况：
```json
{"error": "Invalid OTA request"}
```
**→ 需要调整参数格式**

## 管理面板地址：
http://47.122.144.73:8002/#/device-management?agentId=6bf580ad09cf4b1e8bd332dafb9e6d30

---
请执行上述curl命令并告知结果！ 