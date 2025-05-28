package info.dourok.voicebot.data.model

import android.util.Log
import kotlinx.coroutines.delay
import java.net.*
import java.io.IOException
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.random.Random

/**
 * 自动重试管理器
 * 
 * 实现智能重试策略，包括指数退避算法和抖动处理
 */
@Singleton
class AutoRetryManager @Inject constructor(
    private val errorHandler: ErrorHandler
) {
    companion object {
        private const val TAG = "AutoRetryManager"
        private const val DEFAULT_MAX_RETRIES = 3
        private const val DEFAULT_INITIAL_DELAY_MS = 1000L
        private const val DEFAULT_MAX_DELAY_MS = 16000L
        private const val DEFAULT_BACKOFF_MULTIPLIER = 2.0
        private const val DEFAULT_JITTER_FACTOR = 0.1
    }
    
    /**
     * 指数退避重试策略
     * 
     * @param maxRetries 最大重试次数
     * @param initialDelayMs 初始延迟时间（毫秒）
     * @param maxDelayMs 最大延迟时间（毫秒）
     * @param backoffMultiplier 退避乘数
     * @param jitterFactor 抖动因子（防止惊群效应）
     * @param operation 要执行的操作
     */
    suspend fun <T> retryWithExponentialBackoff(
        maxRetries: Int = DEFAULT_MAX_RETRIES,
        initialDelayMs: Long = DEFAULT_INITIAL_DELAY_MS,
        maxDelayMs: Long = DEFAULT_MAX_DELAY_MS,
        backoffMultiplier: Double = DEFAULT_BACKOFF_MULTIPLIER,
        jitterFactor: Double = DEFAULT_JITTER_FACTOR,
        operation: suspend () -> T
    ): T {
        var lastException: Exception? = null
        var delay = initialDelayMs
        
        repeat(maxRetries) { attempt ->
            try {
                Log.d(TAG, "执行操作，尝试次数: ${attempt + 1}/$maxRetries")
                return operation()
            } catch (e: Exception) {
                lastException = e
                
                // 检查是否应该重试
                if (!errorHandler.isRetryableError(e)) {
                    Log.d(TAG, "异常不适合重试，直接抛出: ${e.javaClass.simpleName}")
                    throw e
                }
                
                Log.w(TAG, "操作失败，尝试次数: ${attempt + 1}/$maxRetries", e)
                
                // 如果是最后一次尝试，直接抛出异常
                if (attempt == maxRetries - 1) {
                    Log.e(TAG, "所有重试均失败，抛出最后一个异常")
                    throw e
                }
                
                // 计算下次重试延迟（包含抖动）
                val jitter = (delay * jitterFactor * Random.nextDouble(-1.0, 1.0)).toLong()
                val actualDelay = (delay + jitter).coerceAtLeast(0L)
                
                Log.d(TAG, "等待 ${actualDelay}ms 后重试（基础延迟: ${delay}ms, 抖动: ${jitter}ms）")
                delay(actualDelay)
                
                // 更新延迟时间（指数退避）
                delay = minOf((delay * backoffMultiplier).toLong(), maxDelayMs)
            }
        }
        
        // 理论上不会到达这里，但为了安全起见
        throw lastException ?: Exception("重试失败")
    }
    
    /**
     * 智能重试（根据异常类型自动决定是否重试）
     * 
     * @param maxRetries 最大重试次数
     * @param operation 要执行的操作
     */
    suspend fun <T> smartRetry(
        maxRetries: Int = DEFAULT_MAX_RETRIES,
        operation: suspend () -> T
    ): T {
        return retryWithExponentialBackoff(maxRetries = maxRetries) {
            operation()
        }
    }
    
    /**
     * 条件重试 - 只有当条件满足时才重试
     * 
     * @param maxRetries 最大重试次数
     * @param shouldRetry 自定义重试条件
     * @param operation 要执行的操作
     */
    suspend fun <T> conditionalRetry(
        maxRetries: Int = DEFAULT_MAX_RETRIES,
        shouldRetry: (Exception) -> Boolean,
        operation: suspend () -> T
    ): T {
        var lastException: Exception? = null
        var delay = DEFAULT_INITIAL_DELAY_MS
        
        repeat(maxRetries) { attempt ->
            try {
                Log.d(TAG, "条件重试执行，尝试次数: ${attempt + 1}/$maxRetries")
                return operation()
            } catch (e: Exception) {
                lastException = e
                
                // 检查自定义重试条件
                if (!shouldRetry(e)) {
                    Log.d(TAG, "自定义条件不满足，不重试: ${e.javaClass.simpleName}")
                    throw e
                }
                
                Log.w(TAG, "条件重试失败，尝试次数: ${attempt + 1}/$maxRetries", e)
                
                if (attempt == maxRetries - 1) {
                    Log.e(TAG, "条件重试全部失败")
                    throw e
                }
                
                val jitter = (delay * DEFAULT_JITTER_FACTOR * Random.nextDouble(-1.0, 1.0)).toLong()
                val actualDelay = (delay + jitter).coerceAtLeast(0L)
                
                Log.d(TAG, "条件重试等待 ${actualDelay}ms")
                delay(actualDelay)
                
                delay = minOf((delay * DEFAULT_BACKOFF_MULTIPLIER).toLong(), DEFAULT_MAX_DELAY_MS)
            }
        }
        
        throw lastException ?: Exception("条件重试失败")
    }
    
    /**
     * 快速重试 - 适用于轻量级操作
     * 
     * @param maxRetries 最大重试次数
     * @param operation 要执行的操作
     */
    suspend fun <T> quickRetry(
        maxRetries: Int = 3,
        operation: suspend () -> T
    ): T {
        return retryWithExponentialBackoff(
            maxRetries = maxRetries,
            initialDelayMs = 500L,
            maxDelayMs = 2000L,
            backoffMultiplier = 1.5,
            operation = operation
        )
    }
    
    /**
     * 获取建议的重试配置
     */
    fun getRecommendedRetryConfig(operationType: OperationType): RetryConfig {
        return when (operationType) {
            OperationType.NETWORK_REQUEST -> RetryConfig(
                maxRetries = 3,
                initialDelayMs = 1000L,
                maxDelayMs = 8000L,
                backoffMultiplier = 2.0
            )
            
            OperationType.DEVICE_BINDING -> RetryConfig(
                maxRetries = 5,
                initialDelayMs = 2000L,
                maxDelayMs = 30000L,
                backoffMultiplier = 1.5
            )
            
            OperationType.WEBSOCKET_CONNECTION -> RetryConfig(
                maxRetries = 10,
                initialDelayMs = 1000L,
                maxDelayMs = 60000L,
                backoffMultiplier = 2.0
            )
            
            OperationType.FILE_OPERATION -> RetryConfig(
                maxRetries = 2,
                initialDelayMs = 500L,
                maxDelayMs = 2000L,
                backoffMultiplier = 2.0
            )
        }
    }
    
    /**
     * 使用推荐配置执行重试
     */
    suspend fun <T> retryWithRecommendedConfig(
        operationType: OperationType,
        operation: suspend () -> T
    ): T {
        val config = getRecommendedRetryConfig(operationType)
        return retryWithExponentialBackoff(
            maxRetries = config.maxRetries,
            initialDelayMs = config.initialDelayMs,
            maxDelayMs = config.maxDelayMs,
            backoffMultiplier = config.backoffMultiplier,
            operation = operation
        )
    }
}

/**
 * 操作类型枚举
 */
enum class OperationType {
    NETWORK_REQUEST,        // 网络请求
    DEVICE_BINDING,         // 设备绑定
    WEBSOCKET_CONNECTION,   // WebSocket连接
    FILE_OPERATION          // 文件操作
}

/**
 * 重试配置
 */
data class RetryConfig(
    val maxRetries: Int,
    val initialDelayMs: Long,
    val maxDelayMs: Long,
    val backoffMultiplier: Double
)

/**
 * 重试状态
 */
data class RetryState(
    val currentAttempt: Int,
    val maxRetries: Int,
    val nextDelayMs: Long,
    val lastException: Exception?
) {
    val hasMoreRetries: Boolean
        get() = currentAttempt < maxRetries
        
    val progress: Float
        get() = currentAttempt.toFloat() / maxRetries.toFloat()
} 