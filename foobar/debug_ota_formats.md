# 🔧 OTA请求格式调试

根据`{"error":"Invalid OTA request"}`错误，让我们尝试不同的请求格式：

## 格式1：完整标准格式
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Device-Id: aa:bb:cc:dd:ee:ff" \
  -H "Client-Id: android-test" \
  -d '{
    "macAddress": "aa:bb:cc:dd:ee:ff",
    "application": {
      "version": "1.0.0",
      "name": "xiaozhi-android"
    },
    "board": {
      "type": "android"
    },
    "chipModelName": "android"
  }' \
  http://47.122.144.73:8002/xiaozhi/ota/
```

## 格式2：简化版本（只包含必需字段）
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Device-Id: aa:bb:cc:dd:ee:ff" \
  -H "Client-Id: android-test" \
  -d '{
    "macAddress": "aa:bb:cc:dd:ee:ff",
    "application": {
      "version": "1.0.0"
    }
  }' \
  http://47.122.144.73:8002/xiaozhi/ota/
```

## 格式3：使用不同的MAC地址格式
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Device-Id: AA:BB:CC:DD:EE:FF" \
  -H "Client-Id: android-test" \
  -d '{
    "macAddress": "AA:BB:CC:DD:EE:FF",
    "application": {
      "version": "1.0.0"
    },
    "board": {
      "type": "android"
    }
  }' \
  http://47.122.144.73:8002/xiaozhi/ota/
```

## 格式4：使用真实设备MAC格式
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Device-Id: 02:00:00:00:00:01" \
  -H "Client-Id: test-uuid-12345" \
  -d '{
    "macAddress": "02:00:00:00:00:01",
    "application": {
      "version": "1.0.0"
    },
    "board": {
      "type": "android"
    },
    "chipModelName": "android"
  }' \
  http://47.122.144.73:8002/xiaozhi/ota/
```

## 调试步骤：
1. **先尝试格式1**（最完整的格式）
2. 如果还是失败，**尝试格式2**（简化版）
3. 如果还是失败，**尝试格式3**（大写MAC）
4. 如果还是失败，**尝试格式4**（不同MAC地址）

## 成功标志：
- 返回包含`"activation"`字段的JSON
- 或返回包含`"websocket"`字段的JSON

## 如果所有格式都失败：
我们将立即转向**方案A：完整设备绑定实现**

---
**请按顺序尝试上述格式，并告知哪个格式有效或者是否都失败。** 