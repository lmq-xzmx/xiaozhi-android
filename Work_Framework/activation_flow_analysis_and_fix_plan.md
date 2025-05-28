/**
 * 解析OTA响应并保存配置
 */
private suspend fun parseJsonResponse(json: JSONObject): Boolean {
    return try {
        val otaResult = fromJsonToOtaResult(json)
        this.otaResult = otaResult
        
        Log.i(TAG, "OTA响应解析完成: needsActivation=${otaResult.needsActivation}, isActivated=${otaResult.isActivated}")
        
        // 根据响应类型保存相应配置
        when {
            // 情况1：需要激活（有activation字段）
            otaResult.needsActivation -> {
                val activationCode = otaResult.activationCode!!
                Log.i(TAG, "设备需要激活，激活码: $activationCode")
                
                // 保存激活信息到DeviceConfigManager
                deviceConfigManager.setActivationCode(activationCode)
                deviceConfigManager.updateBindingStatus(false)
                
                // 清除之前的WebSocket配置
                settingsRepository.webSocketUrl = null
                settingsRepository.transportType = TransportType.None
            }
            
            // 情况2：已激活（有websocket字段）
            otaResult.isActivated -> {
                val websocketUrl = otaResult.websocketUrl!!
                Log.i(TAG, "设备已激活，WebSocket URL: $websocketUrl")
                
                // 保存WebSocket配置到两个地方
                deviceConfigManager.setWebsocketUrl(websocketUrl)
                deviceConfigManager.updateBindingStatus(true)
                deviceConfigManager.setActivationCode(null) // 清除激活码
                
                // 同步到SettingsRepository
                settingsRepository.webSocketUrl = websocketUrl
                settingsRepository.transportType = TransportType.WebSockets
                
                Log.i(TAG, "WebSocket配置已保存到SettingsRepository")
            }
            
            // 情况3：有MQTT配置（备用传输方式）
            otaResult.mqttConfig != null -> {
                val mqttConfig = otaResult.mqttConfig!!
                Log.i(TAG, "收到MQTT配置: ${mqttConfig.endpoint}")
                
                // 保存MQTT配置
                deviceConfigManager.updateBindingStatus(true)
                settingsRepository.transportType = TransportType.MQTT
                // 这里可以添加MQTT配置保存逻辑
            }
            
            else -> {
                Log.w(TAG, "OTA响应不包含有效的配置信息")
                return false
            }
        }
        
        // 保存服务器时间（如果有）
        otaResult.serverTime?.let { serverTime ->
            Log.d(TAG, "服务器时间: ${serverTime.timestamp}")
            // 可以用于时间同步
        }
        
        true
    } catch (e: Exception) {
        Log.e(TAG, "解析OTA响应失败", e)
        false
    }
} 