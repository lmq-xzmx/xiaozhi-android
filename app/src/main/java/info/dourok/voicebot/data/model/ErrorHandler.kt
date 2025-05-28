package info.dourok.voicebot.data.model

import android.util.Log
import java.net.*
import java.io.IOException
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 错误处理器
 * 
 * 负责将技术异常转换为用户友好的错误信息
 */
@Singleton
class ErrorHandler @Inject constructor() {
    
    companion object {
        private const val TAG = "ErrorHandler"
    }
    
    /**
     * 将异常转换为用户友好的错误信息
     */
    fun translateError(exception: Exception): String {
        Log.d(TAG, "处理错误: ${exception.javaClass.simpleName} - ${exception.message}")
        
        return when (exception) {
            // 网络连接错误
            is SocketTimeoutException -> "网络连接超时，请检查网络设置后重试"
            is ConnectException -> "无法连接到服务器，请检查服务器地址和网络连接"
            is UnknownHostException -> "无法解析服务器地址，请检查网络连接或服务器地址"
            is NoRouteToHostException -> "网络路由错误，请检查网络设置"
            is PortUnreachableException -> "服务器端口不可达，请联系技术支持"
            
            // HTTP错误 - 改为处理HTTP响应码错误
            is HttpResponseException -> translateHttpError(exception)
            
            // 通用IO错误
            is IOException -> "网络或文件操作错误：${exception.message ?: "未知错误"}"
            
            // JSON解析错误
            is org.json.JSONException -> "服务器响应格式错误，请联系技术支持"
            
            // 安全错误
            is SecurityException -> "权限不足，请检查应用权限设置"
            
            // 其他错误
            else -> {
                val message = exception.message
                if (message.isNullOrBlank()) {
                    "发生未知错误，请重试或联系技术支持"
                } else {
                    "操作失败：$message"
                }
            }
        }
    }
    
    /**
     * 处理HTTP特定错误
     */
    private fun translateHttpError(exception: HttpResponseException): String {
        return when (exception.code) {
            400 -> "请求参数错误，请检查设备配置"
            401 -> "设备认证失败，请重新绑定设备"
            403 -> "设备无权限访问，请联系管理员"
            404 -> "服务接口不存在，请检查服务器配置或联系技术支持"
            408 -> "请求超时，请重试"
            429 -> "请求频率过高，请稍后重试"
            500 -> "服务器内部错误，请稍后重试或联系技术支持"
            502 -> "网关错误，请稍后重试"
            503 -> "服务暂时不可用，请稍后重试"
            504 -> "网关超时，请稍后重试"
            else -> "服务器错误(${exception.code})，请联系技术支持"
        }
    }
    
    /**
     * 检查错误是否可重试
     */
    fun isRetryableError(exception: Exception): Boolean {
        return when (exception) {
            // 网络临时错误，可重试
            is SocketTimeoutException -> true
            is ConnectException -> true
            is IOException -> true
            
            // HTTP 5xx错误通常可重试
            is HttpResponseException -> exception.code in 500..599
            
            // 其他错误通常不建议重试
            else -> false
        }
    }
    
    /**
     * 获取错误的严重级别
     */
    fun getErrorSeverity(exception: Exception): ErrorSeverity {
        return when (exception) {
            // 网络错误 - 警告级别
            is SocketTimeoutException, 
            is ConnectException, 
            is UnknownHostException -> ErrorSeverity.WARNING
            
            // HTTP客户端错误 - 错误级别
            is HttpResponseException -> {
                when (exception.code) {
                    in 400..499 -> ErrorSeverity.ERROR
                    in 500..599 -> ErrorSeverity.WARNING // 服务器错误，可能临时
                    else -> ErrorSeverity.ERROR
                }
            }
            
            // 安全和权限错误 - 严重级别
            is SecurityException -> ErrorSeverity.CRITICAL
            
            // 其他错误 - 错误级别
            else -> ErrorSeverity.ERROR
        }
    }
    
    /**
     * 根据错误类型提供用户操作建议
     */
    fun getActionSuggestion(exception: Exception): ActionSuggestion {
        return when (exception) {
            is SocketTimeoutException, is ConnectException -> 
                ActionSuggestion.CHECK_NETWORK
                
            is UnknownHostException -> 
                ActionSuggestion.CHECK_NETWORK_AND_DNS
                
            is HttpResponseException -> {
                when (exception.code) {
                    401, 403 -> ActionSuggestion.REBIND_DEVICE
                    404 -> ActionSuggestion.CONTACT_SUPPORT
                    in 500..599 -> ActionSuggestion.RETRY_LATER
                    else -> ActionSuggestion.CONTACT_SUPPORT
                }
            }
            
            is SecurityException -> 
                ActionSuggestion.CHECK_PERMISSIONS
                
            else -> 
                ActionSuggestion.RETRY_OR_CONTACT_SUPPORT
        }
    }
}

/**
 * HTTP响应异常 - 替代retrofit2.HttpException
 */
class HttpResponseException(
    val code: Int,
    message: String = "HTTP Error $code"
) : Exception(message)

/**
 * 错误严重级别
 */
enum class ErrorSeverity {
    WARNING,    // 警告：临时错误，通常可自动恢复
    ERROR,      // 错误：需要用户干预
    CRITICAL    // 严重：需要立即处理
}

/**
 * 用户操作建议
 */
enum class ActionSuggestion {
    CHECK_NETWORK,              // 检查网络连接
    CHECK_NETWORK_AND_DNS,      // 检查网络和DNS设置
    REBIND_DEVICE,              // 重新绑定设备
    CHECK_PERMISSIONS,          // 检查应用权限
    RETRY_LATER,                // 稍后重试
    CONTACT_SUPPORT,            // 联系技术支持
    RETRY_OR_CONTACT_SUPPORT    // 重试或联系技术支持
}

/**
 * 包装的错误信息
 */
data class ErrorInfo(
    val userMessage: String,
    val severity: ErrorSeverity,
    val suggestion: ActionSuggestion,
    val canRetry: Boolean,
    val originalException: Exception
) {
    /**
     * 获取完整的用户提示信息
     */
    fun getFullUserMessage(): String {
        val baseMessage = userMessage
        val suggestionText = when (suggestion) {
            ActionSuggestion.CHECK_NETWORK -> "建议检查网络连接"
            ActionSuggestion.CHECK_NETWORK_AND_DNS -> "建议检查网络连接和DNS设置"
            ActionSuggestion.REBIND_DEVICE -> "建议重新绑定设备"
            ActionSuggestion.CHECK_PERMISSIONS -> "建议检查应用权限设置"
            ActionSuggestion.RETRY_LATER -> "建议稍后重试"
            ActionSuggestion.CONTACT_SUPPORT -> "建议联系技术支持"
            ActionSuggestion.RETRY_OR_CONTACT_SUPPORT -> "建议重试或联系技术支持"
        }
        
        return "$baseMessage\n$suggestionText"
    }
}

/**
 * ErrorHandler扩展函数，提供完整的错误信息
 */
fun ErrorHandler.getErrorInfo(exception: Exception): ErrorInfo {
    return ErrorInfo(
        userMessage = translateError(exception),
        severity = getErrorSeverity(exception),
        suggestion = getActionSuggestion(exception),
        canRetry = isRetryableError(exception),
        originalException = exception
    )
} 